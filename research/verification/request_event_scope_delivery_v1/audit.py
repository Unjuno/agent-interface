"""Raw-only audit: does not import fixture, runner, previous or new consumer."""
import argparse, copy, hashlib, json, sqlite3, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()
def exact(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)

def inspect(raw,out,plan,freeze_sha):
    errors=[]; counts=Counter();value_pass=0; unsupported=0;complete=0
    def check(condition,name):
        if not condition:errors.append(name)
    rows=raw.get('rows',[])
    reps=1 if raw.get('construction') is True else plan['repetitions']
    check(raw.get('allocation')==plan['allocation'],'allocation')
    check(len(rows)==len(plan['scenarios'])*reps,'denominator')
    check(raw.get('freeze_sha256')==freeze_sha,'freeze_binding')
    check(type(raw.get('runner_pid')) is int and raw['runner_pid']>0,'runner_pid')
    check(raw.get('terminal',{}).get('status')=='COMPLETE','terminal')
    check(type(raw.get('terminal',{}).get('rows')) is int and raw['terminal']['rows']==len(rows),'terminal_rows')
    for i,row in enumerate(rows):
        t='row:'+str(i)+':'
        try:
            expected_case=plan['scenarios'][i%len(plan['scenarios'])]
            name=expected_case['name']; rep=i//len(plan['scenarios'])
            check(type(row['index']) is int and row['index']==i,t+'index')
            check(type(row['repetition']) is int and row['repetition']==rep and row['scenario']==name,t+'schedule')
            cfg=row['config'];q=cfg['request'];v={'saved':True,'revision':8,'payload':'requested:'+str(rep)}
            expected_q={'request_id':'q-'+str(i),'session':'session-'+str(i),'resource':'document','epoch':1,'value':v}
            check(exact(q,expected_q),t+'request_contract')
            app=row['application'];obs=row['observer']
            for role,p in [('application',app),('observer',obs)]:
                check(type(p['exit']) is int and p['exit']==0,t+role+'_exit')
                check(type(p['pid']) is int and p['pid']>0,t+role+'_pid')
                check(type(p['start_ns']) is int and type(p['end_ns']) is int and p['start_ns']<=p['end_ns'],t+role+'_clock')
                check(p['stderr']=='',t+role+'_stderr')
                check(len(p['cmd'])==4 and p['cmd'][1]=='-S' and p['cmd'][2].endswith('/'+role+'.py'),t+role+'_command')
            check(app['pid']!=obs['pid'] and app['end_ns']<=obs['start_ns'],t+'separate_process_order')
            check(exact(json.loads(app['stdin']),cfg),t+'application_stdin')
            al=[json.loads(x) for x in app['stdout'].splitlines()]
            for event in al:
                check(type(event['pid']) is int and event['pid']==app['pid'] and app['start_ns']<=event['time_ns']<=app['end_ns'],t+'application_event_binding')
            # Independently simulate the explicit operations, not policy labels.
            state=copy.deepcopy(cfg['initial']); expected_all=[];floor=0
            phase_events=[]
            for phase in ('pre','post'):
                for op in cfg[phase]:
                    seq=len(expected_all)+1
                    e={'seq':seq,'request':op['request'],'before':copy.deepcopy(state),'after':op['request']['value']}
                    phase_events.append(('operation_finished',op,seq))
                    if not op['rollback']:expected_all.append(e);state=copy.deepcopy(e['after'])
                if phase=='pre':floor=len(expected_all);phase_events.append(('accepted',None,None))
            phase_events.append(('finished',None,None))
            check(len(al)==len(phase_events),t+'application_events_count')
            for event,expected in zip(al,phase_events):
                check(event['event']==expected[0],t+'app_event_order')
                if expected[0]=='operation_finished':
                    check(exact(event['request'],expected[1]['request']) and event['rollback'] is expected[1]['rollback'] and type(event['staged_seq']) is int and event['staged_seq']==expected[2],t+'app_operation')
            accept=[e for e in al if e['event']=='accepted'][0]
            check(exact(accept,row['acceptance']) and exact(accept['request'],q) and accept['accepted'] is True and accept['grants_input_authority'] is False and type(accept['floor']) is int and accept['floor']==floor and accept['instance']==cfg['instance'],t+'acceptance')
            check(al[-1]['floor']==floor and al[-1]['ceiling']==len(expected_all),t+'application_terminal')
            check(exact(json.loads(obs['stdin']),{'floor':floor}),t+'observer_query')
            # Query the final database directly, without observer or fixture helpers.
            dbpath=out/row['database']
            check(dbpath.resolve().is_relative_to(out.resolve()),t+'database_path')
            dbbytes=dbpath.read_bytes()
            check(sha(dbbytes)==row['database_sha256']==row['database_before_observer_sha256'],t+'database_hash_read_only')
            db=sqlite3.connect(dbpath.resolve().as_uri()+'?mode=ro',uri=True)
            metadata=db.execute('SELECT instance,session,resource,epoch FROM metadata').fetchall()
            actual_state=db.execute('SELECT saved,revision,payload FROM state').fetchall()
            all_events=[{'seq':r[0],'request':json.loads(r[1]),'before':json.loads(r[2]),'after':json.loads(r[3])} for r in db.execute('SELECT seq,request_json,before_json,after_json FROM events ORDER BY seq')]
            db.close()
            check(metadata==[(cfg['instance'],q['session'],q['resource'],q['epoch'])],t+'database_metadata')
            check(actual_state==[(int(state['saved']),state['revision'],state['payload'])],t+'database_state')
            check(exact(all_events,expected_all),t+'database_events')
            ob=json.loads(obs['stdout'])
            check(type(ob['pid']) is int and ob['pid']==obs['pid'] and obs['start_ns']<=ob['time_ns']<=obs['end_ns'],t+'observer_identity')
            expected_snap={'schema':1,'instance':cfg['instance'],'session':q['session'],'resource':q['resource'],'epoch':q['epoch'],'floor':floor,'ceiling':len(expected_all),'complete':True,'state':state,'events':expected_all[floor:]}
            check(exact(ob['snapshot'],expected_snap) and exact(row['snapshot'],expected_snap),t+'snapshot_from_database')
            delivered=copy.deepcopy(expected_snap)
            if name=='INCOMPLETE_HISTORY':delivered['complete']=False;delivered['events']=[]
            if name=='WRONG_INCARNATION':delivered['instance']='unrelated-instance'
            check(exact(row['delivered'],delivered),t+'registered_transport_intervention')
            # Independent event/state obligations on the exact delivered record.
            state_status='MATCH' if state==q['value'] else 'DIFFERENT'
            if delivered['instance']!=accept['instance']:state_status='UNKNOWN';event_status='UNKNOWN'
            elif delivered['complete'] is not True:event_status='UNKNOWN'
            else:
                selected=[e for e in delivered['events'] if e['request']['request_id']==q['request_id']]
                if any(not exact(e['request'],q) for e in selected):event_status='REQUEST_CONFLICT'
                elif len(selected)==0:event_status='NOT_APPLIED_IN_WINDOW'
                elif len(selected)==1:event_status='APPLIED_ONCE'
                else:event_status='APPLIED_MULTIPLE'
            expected_decision={'state':state_status,'event':event_status,'complete_this_request':state_status=='MATCH' and event_status=='APPLIED_ONCE','grants_input_authority':False,'causal_necessity':'UNRESOLVED'}
            check(exact(row['candidate'],expected_decision),t+'candidate_oracle')
            check(state_status==expected_case['state'] and event_status==expected_case['event'] and expected_decision['complete_this_request'] is expected_case['complete_this_request'],t+'predeclared_gate')
            expected_value_evidence={'target_id':q['resource'],'expected_target_id':q['resource'],'request_id':q['request_id'],'kind':'typed_state','freshness':'CURRENT','cleanup_verified':True,'receipt':{'schema':1,'accepted':True,'target_id':q['resource'],'request_id':q['request_id'],'kind':'typed_state'},'contract':{'mode':'EXACT_VALUE','expected':q['value']},'observed':state}
            check(exact(row['previous_evidence'],expected_value_evidence),t+'previous_contract')
            vp=state==q['value']
            check(row['previous_value_verdict']==('PASS_POSTCONDITION' if vp else 'FAIL_POSTCONDITION'),t+'previous_value_oracle')
            check(row['naive_complete_this_request'] is vp,t+'naive_policy')
            value_pass+=vp;complete+=expected_decision['complete_this_request'];unsupported+=vp and not expected_decision['complete_this_request'];counts[event_status]+=1
        except Exception as exc:
            errors.append(t+type(exc).__name__+':'+str(exc))
    factor=reps/plan['repetitions']
    check(value_pass==plan['expected_previous_value_pass']*factor,'value_pass_total')
    check(complete==plan['expected_complete_request']*factor,'complete_request_total')
    check(unsupported==plan['expected_unsupported_promotion']*factor,'unsupported_promotion_total')
    check(dict(counts)=={k:int(v*factor) for k,v in plan['expected_event_counts'].items()},'event_counts')
    return {'decision':'PASS_REQUEST_EVENT_SCOPE_SCOPED' if not errors else 'HOLD_AUDIT_OR_EVIDENCE','errors':errors,'rows':len(rows),'event_counts':dict(counts),'previous_value_pass':value_pass,'complete_this_request':complete,'unsupported_naive_promotion':unsupported,'actual_model_calls':0,'counterfactual_causality_established':False}

def controls(raw,out,plan,freeze):
    changes={
      'missing_row':lambda x:x['rows'].pop(),
      'duplicate_row':lambda x:x['rows'].__setitem__(1,copy.deepcopy(x['rows'][0])),
      'row_order':lambda x:x['rows'].reverse(),
      'source_binding':lambda x:x.__setitem__('freeze_sha256','x'),
      'boolean_exit':lambda x:x['rows'][0]['application'].__setitem__('exit',False),
      'boolean_floor':lambda x:x['rows'][0]['acceptance'].__setitem__('floor',False),
      'changed_request':lambda x:x['rows'][0]['config']['request']['value'].__setitem__('payload','other'),
      'changed_event':lambda x:x['rows'][0]['delivered']['events'][0]['request'].__setitem__('request_id','other'),
      'missing_history':lambda x:x['rows'][0]['delivered'].__setitem__('events',[]),
      'wrong_snapshot_identity':lambda x:x['rows'][0]['delivered'].__setitem__('instance','wrong'),
      'promoted_unknown':lambda x:x['rows'][9]['candidate'].__setitem__('complete_this_request',True),
      'boolean_complete':lambda x:x['rows'][0]['candidate'].__setitem__('complete_this_request',1),
      'changed_db_digest':lambda x:x['rows'][0].__setitem__('database_sha256','0'*64),
      'lost_observer_output':lambda x:x['rows'][0]['observer'].__setitem__('stdout','{}'),
      'changed_previous_verdict':lambda x:x['rows'][0].__setitem__('previous_value_verdict','FAIL_POSTCONDITION')}
    result={}
    for name,change in changes.items():
        modified=copy.deepcopy(raw);change(modified);a=inspect(modified,out,plan,freeze)
        result[name]={'rejected':bool(a['errors']),'errors':a['errors'][:3]}
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('out');ap.add_argument('--report',required=True);ap.add_argument('--controls',action='store_true');args=ap.parse_args()
    out=Path(args.out);raw_bytes=(out/'RAW.json').read_bytes();raw=json.loads(raw_bytes);plan=json.loads((ROOT/'plan.json').read_text())
    f=ROOT/'FREEZE.json';freeze_sha=sha(f.read_bytes()) if f.exists() else None
    source_errors=[]
    if not raw['construction']:
        for name,h in json.loads(f.read_text())['source_sha256'].items():
            if sha((ROOT/name).read_bytes())!=h:source_errors.append(name)
    if source_errors:
        result={'decision':'STOP_SOURCE_MISMATCH','source_errors':source_errors,'scientific_rows_scored':0}
        Path(args.report).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result));return 2
    result=inspect(raw,out,plan,freeze_sha);result['source_errors']=source_errors;result['raw_sha256']=sha(raw_bytes)
    journal=[json.loads(x) for x in (out/'journal.jsonl').read_text().splitlines()]
    result['journal_matches_raw']=exact(journal,raw['rows'])
    if args.controls:result['corruption_controls']=controls(raw,out,plan,freeze_sha)
    okay=not result['errors'] and not source_errors and result['journal_matches_raw'] and all(x['rejected'] for x in result.get('corruption_controls',{}).values())
    if not okay:result['decision']='HOLD_AUDIT_OR_EVIDENCE'
    Path(args.report).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True));return 0 if okay else 2

if __name__=='__main__':sys.exit(main())
