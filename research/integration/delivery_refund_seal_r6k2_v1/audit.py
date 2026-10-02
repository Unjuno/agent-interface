"""Read-only independent reconstruction. Does not import actors, run or wire."""
import base64, collections, hashlib, json, sys
from pathlib import Path

SCENARIOS = ('NORMAL_ACK','RECEIVED_ACK_LOST','DATA_DROPPED','DATA_DELAYED','QUERY_REPLY_LOST','FOREIGN_QUERY_REPLY')
POLICIES = ('HOLD','QUERY_ABSENT','SEAL_ABSENT')
FIELDS = ('session','epoch','id','origin','n','sha256')
DATA = bytes(range(256))*16
DIGEST = hashlib.sha256(DATA).hexdigest()


def pack(x):
    return (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()


def load_case(path):
    result = {'case': json.loads((path/'case.json').read_text()),
              'dialogue': json.loads((path/'dialogue.json').read_text())}
    for role in ('sender','relay','receiver'):
        result[role] = [json.loads(line) for line in (path/(role+'.jsonl')).read_text().splitlines()]
        result[role+'_stderr'] = (path/(role+'.stderr')).read_text()
    return result


def check_case(obj):
    errors, checks = [], 0
    def check(ok, name):
        nonlocal checks
        checks += 1
        if not ok: errors.append(name)
    c = obj['case']; session = c['id']; scenario=c['scenario']; policy=c['policy']
    check(scenario in SCENARIOS and policy in POLICIES,'spec')
    check(c['complete'] is True and c['socket_cleanup'] is True,'completion')
    check(c['end_ns'] >= c['start_ns'],'case_clock')
    check(set(c['processes']) == {'sender','relay','receiver'},'actor_set')
    check(len({p['pid'] for p in c['processes'].values()}) == 3,'independent_pids')
    for role in ('sender','relay','receiver'):
        proc = c['processes'].get(role,{})
        log = obj[role]
        check(type(proc.get('exit')) is int and proc['exit']==0,'exit:'+role)
        check(proc.get('ready')=={'ready':role,'pid':proc.get('pid')},'ready:'+role)
        check(obj[role+'_stderr']=='','stderr:'+role)
        check(bool(log) and log[0]['kind']=='START' and log[-1]['kind']=='END','journal_complete:'+role)
        check([r['seq'] for r in log]==list(range(len(log))),'seq:'+role)
        check(all(r['pid']==proc.get('pid') for r in log),'pid:'+role)
        check(all(a['ns']<=b['ns'] for a,b in zip(log,log[1:])),'time:'+role)
        check(c['start_ns']<=log[0]['ns']<=log[-1]['ns']<=c['end_ns'],'bracket:'+role)
        check(log[0]['session']==session and log[0]['argv']==proc['argv'][3:],'source_command:'+role)
    if any(not obj[role] or obj[role][-1]['kind']!='END' for role in ('sender','relay','receiver')):
        return dict(errors=errors,checks=checks,policy=policy,scenario=scenario,received_bytes=0,cue_bytes=0,auto_packets=0,overage=False,refunded_bytes=0,extra_cue=False,prevented_bodies=0)
    def identity(rid):
        return {'session':session,'epoch':'receiver-1','id':rid,
                'origin':'AUTO' if rid.startswith('a') else 'CUE','n':4096,'sha256':DIGEST}
    statuses, bodies, headers, delivered = {}, [], [], []
    for r in obj['receiver'][1:-1]:
        if r['kind']=='HEADER':
            ident=r['request']['packet'];rid=ident['id'];state=statuses.get(rid,'ABSENT')
            check(ident==identity(rid),'receiver_identity')
            check(r['response']==dict(ident,state=state,ready=state=='ABSENT'),'header_admission')
            headers.append(r)
            if state!='ABSENT':delivered.append(r['response'])
        elif r['kind']=='BODY':
            ident=r['packet'];rid=ident['id'];raw=base64.b64decode(r['payload'],validate=True)
            check(statuses.get(rid,'ABSENT')=='ABSENT','body_after_terminal')
            check(bool(headers) and headers[-1]['response']['ready'] is True and headers[-1]['request']['packet']==ident,'body_header')
            check(raw==DATA and ident==identity(rid),'body_bytes')
            statuses[rid]='RECEIVED';bodies.append(ident)
        elif r['kind']=='RPC':
            q=r['request'];op=q['op']
            if op=='STOP':continue
            ident=q['packet'];rid=ident['id']
            check(ident==identity(rid),'rpc_identity')
            if op=='SEAL' and statuses.get(rid,'ABSENT')=='ABSENT':statuses[rid]='CANCELED'
            check(r['response']==dict(ident,state=statuses.get(rid,'ABSENT')),'receiver_reply')
            if op=='DELIVER':delivered.append(r['response'])
    end=obj['receiver'][-1]
    check(end['states']=={k:{'packet':identity(k),'state':v} for k,v in statuses.items()},'receiver_final')
    check(len({b['id'] for b in bodies})==len(bodies),'duplicate_body')
    forwards=[r for r in obj['relay'] if r['kind']=='FORWARD']
    check([r['actual'] for r in forwards]==delivered,'relay_receiver_order')
    check(len(forwards)==len(headers),'header_forward_count')
    for f,h in zip(forwards,headers):
        check(f['header']==h['response'] and f['packet']==h['request']['packet'],'forward_header')
        check(f['body_bytes']==(4096 if h['response']['ready'] else 0),'body_transmission')
        check(f['delivered'] is None or f['delivered']==f['actual'],'ack_forward')
    rpc=[r for r in obj['relay'] if r['kind']=='RPC']
    staged={}; staged_list=[]
    for r in rpc:
        q=r['request'];op=q['op']
        if op=='STAGE':
            p=q['packet'];rid=p['id']
            check(p==identity(rid) and base64.b64decode(q['payload'],validate=True)==DATA,'stage_bytes')
            check(rid not in staged,'stage_once');staged[rid]=p;staged_list.append(rid)
        elif op in ('RELEASE','DROP'):
            check(q['id'] in staged,'relay_pending');staged.pop(q['id'],None)
    check(not staged and obj['relay'][-1]['pending_ids']==[],'relay_drained')
    queries=[r for r in rpc if r['request']['op']=='STATUS']
    native_queries=[r for r in obj['receiver'] if r['kind']=='RPC' and r['request']['op'] in ('QUERY','SEAL')]
    check(len(queries)==len(native_queries),'query_count')
    for a,b in zip(queries,native_queries):
        q=a['request']; expected=dict(b['response'])
        check(q['packet']==b['request']['packet'] and q['method']==b['request']['op'],'query_binding')
        check(a['actual']==b['response'],'query_actual')
        if q['fault']=='LOST':expected=None
        elif q['fault']=='FOREIGN':expected['session']='other-session'
        check(a['response']==expected,'query_transport')
    steps=[r for r in obj['sender'] if r['kind']=='STEP']
    check(obj['dialogue']==[{'request':r['request'],'response':r['response']} for r in steps],'caller_dialogue')
    ledger={};qi=0;prepared=[];refunds=0
    for r in steps:
        check(r['before']==ledger,'ledger_before')
        q=r['request'];op=q['op'];extra={}
        if op=='PREPARE':
            rid=q['id'];origin=q['origin'];prepared.append(rid)
            spent=sum(v['packet']['n'] for v in ledger.values() if v['charged'])
            cues=sum(v['packet']['n'] for v in ledger.values() if v['charged'] and v['packet']['origin']=='CUE')
            admit=spent<=12288 and (origin=='AUTO' or cues<=4096)
            ledger[rid]={'packet':identity(rid),'charged':admit,'outcome':'UNKNOWN' if admit else 'BUDGET_REFUSED'}
            extra={'accepted':admit}
        elif op=='ACK':
            entry=ledger[q['id']];reply=q['reply']
            good=isinstance(reply,dict) and all(reply.get(k)==entry['packet'][k] for k in FIELDS)
            if good and reply.get('state')=='RECEIVED':entry['outcome']='RECEIVED'
            extra={'outcome':entry['outcome']}
        elif op=='RECONCILE':
            replies={}
            if policy!='HOLD':
                for rid,e in ledger.items():
                    if not e['charged'] or e['outcome']!='UNKNOWN':continue
                    if qi>=len(queries):check(False,'missing_query');continue
                    native=queries[qi];qi+=1;reply=native['response'];replies[rid]=reply
                    check(native['request']['packet']==e['packet'],'query_sender')
                    check(native['request']['method']==('SEAL' if policy=='SEAL_ABSENT' else 'QUERY'),'query_method')
                    good=isinstance(reply,dict) and all(reply.get(k)==e['packet'][k] for k in FIELDS)
                    state=reply.get('state') if good else None
                    if state==('CANCELED' if policy=='SEAL_ABSENT' else 'ABSENT'):
                        e['charged']=False;e['outcome']='REFUNDED';refunds+=4096
                    elif state=='RECEIVED':e['outcome']='RECEIVED'
            extra={'replies':replies}
        elif op=='STOP':extra={'stopped':'sender'}
        check(r['after']==ledger,'ledger_after')
        spent=sum(v['packet']['n'] for v in ledger.values() if v['charged'])
        check(r['response']==dict(extra,charged_bytes=spent,authority_granted=False),'sender_response')
    check(qi==len(queries),'query_consumption')
    check(prepared==['c1','c2','c3','a1','a2'],'request_schedule')
    check(sum(r['request']['op']=='RECONCILE' for r in steps)==2,'reconcile_twice')
    check(obj['sender'][-1]['ledger']==ledger,'ledger_terminal')
    check(staged_list==[rid for rid in prepared if ledger[rid]['outcome']!='BUDGET_REFUSED'],'stage_admission')
    received=[b['id'] for b in bodies]
    reclaim=scenario in ('DATA_DROPPED','DATA_DELAYED') and policy!='HOLD'
    first=scenario!='DATA_DROPPED' and not (policy=='SEAL_ABSENT' and scenario in ('DATA_DELAYED','QUERY_REPLY_LOST','FOREIGN_QUERY_REPLY'))
    expected=(['c1','c2'] if first else [])+(['c3'] if reclaim else [])+['a1','a2']
    check(sorted(received)==sorted(expected),'endpoint_ids')
    check(refunds==(8192 if reclaim else 0),'refund_once')
    n=len(bodies)*4096;cue=sum(b['origin']=='CUE' for b in bodies)*4096
    over=n>16384 or cue>8192
    check(over==(policy=='QUERY_ABSENT' and scenario=='DATA_DELAYED'),'quota_endpoint')
    return {'errors':errors,'checks':checks,'policy':policy,'scenario':scenario,
            'received_bytes':n,'cue_bytes':cue,'auto_packets':sum(b['origin']=='AUTO' for b in bodies),
            'overage':over,'refunded_bytes':refunds,'extra_cue': 'c3' in received,
            'prevented_bodies':sum(not h['response']['ready'] for h in headers)}


def audit(root, phase):
    root=Path(root); errors=[]; rows=[]; checks=0
    freeze={'sha256':{}} if phase.startswith('construction') and not (root/'FREEZE.json').exists() else json.loads((root/'FREEZE.json').read_text())
    for n,d in freeze['sha256'].items():
        checks+=1
        if not (root/n).is_file() or hashlib.sha256((root/n).read_bytes()).hexdigest()!=d:errors.append('source:'+n)
    for i,scenario in enumerate(SCENARIOS):
        p=root/phase/('b'+str(i))
        receipt=json.loads((p/'batch.json').read_text()); launch=json.loads((p/'launcher.json').read_text())
        checks+=2
        if not receipt['complete'] or launch['exit']!=0:errors.append('batch:'+str(i))
        expected=['r6k2-'+phase+'-'+str(i)+'-'+str(r)+'-'+a for r in range(2) for a in (POLICIES if r==0 else POLICIES[::-1])]
        if receipt['ids']!=expected:errors.append('batch_ids:'+str(i))
        for ident in expected:
            row=check_case(load_case(p/ident));rows.append(row);checks+=row['checks']
            errors.extend(ident+':'+e for e in row['errors'])
    totals={}
    for policy in POLICIES:
        selected=[r for r in rows if r['policy']==policy]
        totals[policy]={k:sum(r[k] for r in selected) for k in ('received_bytes','cue_bytes','auto_packets','overage','refunded_bytes','extra_cue','prevented_bodies')}
        totals[policy]['cases']=len(selected)
    return {'decision':'PASS_TERMINAL_DELIVERY_REFUND_BOUNDARY_SCOPED' if not errors else 'HOLD_OR_FAIL_AUDIT',
            'errors':errors,'checks':checks,'cases':len(rows),'policies':totals,'actor_exits':3*len(rows),'batches':6}


if __name__=='__main__':
    result=audit(sys.argv[1],sys.argv[2]);sys.stdout.buffer.write(pack(result));raise SystemExit(bool(result['errors']))
