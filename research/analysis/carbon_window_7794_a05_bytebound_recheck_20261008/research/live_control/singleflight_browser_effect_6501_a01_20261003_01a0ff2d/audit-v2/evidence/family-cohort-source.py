"""Versioned retained-only correction; original audit.py and A01 remain unchanged."""
import copy
import hashlib
import json
from pathlib import Path
import sys

def exact(a,b):
    return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)

def scope(case,target,generation):
    return {'verifier':'dom-ready-v1','source':case,'target':target,'generation':generation,
            'digest':f'{case}/{target}/{generation}/READY','predicate':'ready','window':case,'role':'read_only'}

KINDS={'cold_equivalent':'equivalent','warm_equivalent':'equivalent','mixed_targets':'mixed',
       'generation_change':'generation','late_caller':'late'}
ORDER=[['cold_equivalent','independent'],['cold_equivalent','predicate'],['cold_equivalent','scoped'],
       ['warm_equivalent','scoped'],['warm_equivalent','independent'],['warm_equivalent','predicate'],
       ['mixed_targets','predicate'],['mixed_targets','scoped'],['mixed_targets','independent'],
       ['generation_change','scoped'],['generation_change','predicate'],['generation_change','independent'],
       ['late_caller','independent'],['late_caller','scoped'],['late_caller','predicate']]

def audit(client,server,mini=False):
    errors=[]
    def require(condition,label):
        if not condition:errors.append(label)
    def ns(value,label):
        if type(value) is not str or not value.isascii() or not value.isdigit():
            errors.append(label+':clock_type');return -1
        return int(value)
    require(client.get('schema')=='6501-browser-client-v1','client_schema')
    require(server.get('schema')=='6501-browser-server-v1','server_schema')
    require(client.get('fatal') is None and not client.get('watchdog_fired'),'client_fatal')
    require(client['cleanup'].get('browser_closed') is True and
            client['cleanup'].get('browser_exit_code')==0 and type(client['cleanup'].get('browser_exit_code')) is int,'browser_cleanup')
    require(server.get('active_reads_at_close')==0 and type(server.get('active_reads_at_close')) is int and
            server.get('listener_closed') is True and server.get('thread_terminal') is True,'server_cleanup')
    expected=[['cold_equivalent','independent'],['cold_equivalent','scoped'],
              ['mixed_targets','predicate'],['mixed_targets','scoped'],
              ['generation_change','predicate'],['generation_change','scoped']] if mini else ORDER
    require([[r.get('case'),r.get('policy')] for r in client['rows']]==expected,'denominator_order')
    segments=[];current=None;previous=-1
    for i,event in enumerate(server['events']):
        require(type(event.get('seq')) is int and event['seq']==i,'server_sequence')
        stamp=event.get('ns')
        require(type(stamp) is int and stamp>=previous,'server_clock')
        previous=stamp if type(stamp) is int else previous
        if event['event']=='setup':
            current={'setup':event,'events':[]};segments.append(current)
        elif current is None:errors.append('event_before_setup')
        else:current['events'].append(event)
    require(len(segments)==len(client['rows']),'server_denominator')
    summary={p:{'offered_reads':0,'warmup_reads':0,'correct_effects':0,'refusals':0} for p in ('independent','predicate','scoped')}
    elapsed={};read_ids=set();total_waiters=0
    for row,segment in zip(client['rows'],segments):
        case,policy=row['case'],row['policy'];label=case+'/'+policy
        if case not in KINDS or policy not in summary:
            errors.append('unknown_condition');continue
        kind=KINDS[case]
        require(segment['setup']['case']==case and segment['setup']['policy']==policy,label+':setup')
        require(row.get('status')=='COMPLETE' and row.get('context_closed') is True,label+':disposition')
        require(row.get('pending_entries')==0 and type(row.get('pending_entries')) is int,label+':pending')
        cohort_start=ns(row['offered_ns'],label)
        cohort_end=ns(row['ended_ns'],label)
        require(cohort_start<=cohort_end,label+':cohort_interval')
        consumers=row['consumers'];total_waiters+=len(consumers)
        require([c['request'] for c in consumers]==['w1','w2'],label+':waiter_denominator')
        require(len(consumers)==2,label+':waiter_count')
        events=segment['events'];generation=1;reads={};last_end=-1
        closes=[e for e in events if e['event']=='case_closed']
        require(len(closes)==1 and events[-1]['event']=='case_closed',label+':close')
        for e in events:
            if e['event']=='generation_flip':
                generation+=1;require(type(e['generation']) is int and e['generation']==generation,label+':flip')
            elif e['event']=='read_arrived':
                rid=e['read_id'];require(type(rid) is int and rid not in read_ids,label+':read_id');read_ids.add(rid)
                wanted=scope(case,e['scope']['target'],generation)
                require(e['scope']['target'] in ('A','B') and exact(e['scope'],wanted),label+':captured_scope')
                require(exact(e['dom_snapshot'],wanted),label+':dom_server_scope')
                reads[rid]={'arrived':e}
            elif e['event']=='read_service_begin':
                require(e['read_id'] in reads and e['ns']>=last_end,label+':serial_service')
                reads[e['read_id']]['begin']=e
            elif e['event']=='read_return':
                r=reads.get(e['read_id'],{})
                require('begin' in r and e['ns']>=r.get('begin',{}).get('ns',0),label+':service_time')
                require(exact(e['scope'],r.get('arrived',{}).get('scope')) and e['value']=='READY' and
                        e['evidence_ref']==f"read-{e['read_id']}",label+':return_scope')
                r['return']=e;last_end=e['ns']
        require(generation==(2 if kind=='generation' else 1),label+':final_generation')
        offered=[r for r in reads.values() if r['arrived']['phase']=='offered']
        warm=[r for r in reads.values() if r['arrived']['phase']=='warmup']
        desired_reads=2 if policy=='independent' or kind=='late' or (policy=='scoped' and kind!='equivalent') else 1
        require(len(offered)==desired_reads and len(warm)==int(case=='warm_equivalent') and
                len(reads)==len(offered)+len(warm),label+':read_counts')
        require(all('begin' in r and 'return' in r for r in reads.values()),label+':unfinished_read')
        client_events=row['events'];prev=-1
        warmup_ends=[i for i,e in enumerate(client_events) if e['event']=='warmup_complete']
        require(len(warmup_ends)==int(case=='warm_equivalent'),label+':warmup_boundary')
        warmup_end=warmup_ends[0] if warmup_ends else -1
        for i,e in enumerate(client_events):
            stamp=ns(e['ns'],label)
            require(type(e['seq']) is int and e['seq']==i and stamp>=prev,label+':client_event_order');prev=stamp
            if i<=warmup_end:
                require(stamp<=cohort_start,label+':warmup_before_offer')
            else:
                require(cohort_start<=stamp<=cohort_end,label+':event_in_cohort')
        require(sum(e['event']=='spawn' for e in client_events)==len(reads),label+':spawn_counts')
        require(sum(e['event']=='join' for e in client_events)==2-desired_reads,label+':join_counts')
        expected_commits={}
        for consumer in consumers:
            request=consumer['request'];target='B' if kind=='mixed' and request=='w2' else 'A'
            requested_generation=2 if kind=='generation' and request=='w2' else 1
            requested=scope(case,target,requested_generation);fresh=scope(case,target,generation)
            require(exact(consumer['requested'],requested),label+':requested_scope')
            require(exact(consumer['current'],fresh),label+':fresh_scope')
            result=consumer['result'];r=reads.get(result['read_id'],{});returned=r.get('return',{})
            wanted_result={k:returned.get(k) for k in ('read_id','scope','value','evidence_ref')}
            require(exact(result,wanted_result),label+':delivery_binding')
            started,deadline,decision,ended=[ns(consumer[k],label) for k in ('started_ns','deadline_ns','decision_ns','ended_ns')]
            require(deadline-started==5_000_000_000 and started<=decision<=ended and
                    ns(consumer['elapsed_ns'],label)==ended-started,label+':waiter_clock')
            require(cohort_start<=started<=decision<=ended<=cohort_end,label+':waiter_in_cohort')
            if kind=='generation' and request=='w1':expected_decision='STALE_ON_RETURN'
            elif policy=='predicate' and request=='w2' and kind in ('mixed','generation'):expected_decision='DISTINCT_SCOPE'
            else:expected_decision='ELIGIBLE'
            require(decision<deadline,label+':unexpected_deadline')
            require(consumer['decision']==expected_decision,label+':decision')
            corresponding=[e for e in client_events if e['event']=='decision' and e['request']==request]
            require(len(corresponding)==1 and corresponding[0]['decision']==expected_decision and
                    exact(corresponding[0]['requested'],requested) and exact(corresponding[0]['current'],fresh),label+':decision_event')
            if expected_decision=='ELIGIBLE':
                expected_commits[request]=target
                require(consumer['feedback']=='Committed '+target,label+':feedback')
            else:require(consumer['feedback'] is None,label+':false_feedback')
        commits=[e for e in events if e['event']=='commit']
        require(len(commits)==len(expected_commits),label+':commit_count')
        seen={}
        for event in commits:
            request=event['request_id'];wanted=expected_commits.get(request)
            require(request not in seen and wanted==event['target'] and event['accepted'] is True and
                    type(event['generation']) is int and event['generation']==generation and
                    event['intent']==f'{case}/{request}/{wanted}',label+':effect_intent')
            source_consumer=next((c for c in consumers if c['request']==request),None)
            require(source_consumer is not None and event['evidence_ref']==source_consumer['result']['evidence_ref'],label+':effect_read_ref')
            seen[request]=event['target']
        require(exact(seen,expected_commits),label+':effects')
        if closes:
            require(exact(closes[0]['commits'],expected_commits) and type(closes[0]['reads']) is int and
                    closes[0]['reads']==len(reads) and type(closes[0]['active_reads']) is int and
                    closes[0]['active_reads']==0 and closes[0]['generation']==generation,label+':independent_state')
        feedback_events=[e for e in client_events if e['event']=='useful_feedback']
        require(len(feedback_events)==len(expected_commits) and
                {e['request']:e['text'] for e in feedback_events}=={k:'Committed '+v for k,v in expected_commits.items()},label+':useful_feedback')
        used=[c['result']['read_id'] for c in consumers]
        require(len(set(used))==desired_reads,label+':shared_delivery_counts')
        if kind=='late':
            late=[e for e in client_events if e['event']=='late_caller_after_completion']
            require(len(late)==1 and ns(late[0]['ns'],label)>=ns(consumers[0]['ended_ns'],label) and
                    ns(consumers[1]['started_ns'],label)>ns(consumers[0]['ended_ns'],label),label+':late_not_cache')
        if kind=='generation':
            require(any(e['event']=='public_generation_change' for e in client_events),label+':public_flip')
        elapsed[(case,policy)]=ns(row['elapsed_ns'],label)
        require(ns(row['ended_ns'],label)-ns(row['offered_ns'],label)==elapsed[(case,policy)],label+':cohort_clock')
        summary[policy]['offered_reads']+=len(offered);summary[policy]['warmup_reads']+=len(warm)
        summary[policy]['correct_effects']+=len(expected_commits);summary[policy]['refusals']+=2-len(expected_commits)
    required_waiters=12 if mini else 30
    require(total_waiters==required_waiters,'all_waiters')
    benefit=None if mini or errors else all(elapsed.get((c,'scoped'),10**30)<elapsed.get((c,'independent'),-1)
                                  for c in ('cold_equivalent','warm_equivalent'))
    return {'errors':errors,'rows':len(client['rows']),'waiters':total_waiters,'summary':summary,
            'equivalent_cohort_latency_gain_observed':benefit,
            'cohort_elapsed_ns':{c+'/'+p:v for (c,p),v in elapsed.items()}}

def controls(client,server,mini=False):
    result=[]
    def probe(name,change):
        c,s=copy.deepcopy(client),copy.deepcopy(server);change(c,s)
        try: errors=audit(c,s,mini)['errors']
        except (KeyError,TypeError,ValueError,IndexError):errors=['malformed_record']
        result.append({'control':name,'rejected':bool(errors),'errors':errors})
    probe('omit_row',lambda c,s:c['rows'].pop())
    probe('generation_type',lambda c,s:c['rows'][0]['consumers'][0]['requested'].__setitem__('generation',True))
    probe('wrong_result_target',lambda c,s:c['rows'][0]['consumers'][0]['result']['scope'].__setitem__('target','B'))
    probe('false_feedback',lambda c,s:c['rows'][0]['consumers'][0].__setitem__('feedback','Committed B'))
    probe('duplicate_waiter',lambda c,s:c['rows'][0]['consumers'][1].__setitem__('request','w1'))
    probe('browser_cleanup',lambda c,s:c['cleanup'].__setitem__('browser_closed',False))
    probe('numeric_server_cleanup',lambda c,s:s.__setitem__('active_reads_at_close',False))
    probe('wrong_intent',lambda c,s:next(e for e in s['events'] if e['event']=='commit').__setitem__('intent','borrowed/w2/A'))
    probe('false_state',lambda c,s:next(e for e in s['events'] if e['event']=='case_closed')['commits'].__setitem__('w1','B'))
    probe('accepted_type',lambda c,s:next(e for e in s['events'] if e['event']=='commit').__setitem__('accepted',1))
    probe('deadline_type',lambda c,s:c['rows'][0]['consumers'][0].__setitem__('deadline_ns',True))
    probe('pending_entry',lambda c,s:c['rows'][0].__setitem__('pending_entries',1))
    return result

if __name__=='__main__':
    directory,output=map(Path,sys.argv[1:3]);mini='--mini' in sys.argv[3:]
    client=json.loads((directory/'client.json').read_bytes());server=json.loads((directory/'server.json').read_bytes())
    result=audit(client,server,mini);result['controls']=controls(client,server,mini)
    result['input_sha256']={name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in ('client.json','server.json')}
    ok=not result['errors'] and all(c['rejected'] for c in result['controls'])
    result['status']='PASS_BROWSER_EFFECT_METHOD_SCOPED' if ok else 'FAIL_AUDIT'
    result['hypothesis']='H_PASS_AUTHORED_FIXTURE_ONLY' if ok and result['equivalent_cohort_latency_gain_observed'] else 'HOLD_NOT_ESTABLISHED'
    with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='controls'}))
    sys.exit(0 if ok else 1)
