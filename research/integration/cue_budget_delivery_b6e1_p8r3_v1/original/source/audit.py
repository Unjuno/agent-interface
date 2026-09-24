"""Read-only audit. Imports no runner, quota, worker, or inherited extractor."""
from __future__ import annotations
import argparse,base64,hashlib,json,sqlite3
from pathlib import Path

SCENARIOS=('WITHIN','OVERFLOW','RESTART_REPEAT','ID_CONFLICT','RACE_QUOTA','RACE_DUPLICATE','RESERVED_EXIT','STALE_SCOPE')
ARMS=('PER_REQUEST','SPLIT_CHECK','ATOMIC_RESERVE')

def expected_statuses(s,a):
    ordinary={
        'WITHIN':['READY','READY'],
        'OVERFLOW':['READY','READY','HOLD_BUDGET'],
        'RESTART_REPEAT':['READY','DUPLICATE_NO_OUTPUT'],
        'ID_CONFLICT':['READY','REJECT_ID_CONFLICT'],
        'RACE_QUOTA':['READY','READY' if a=='SPLIT_CHECK' else 'HOLD_BUSY'],
        'RACE_DUPLICATE':['READY','DUPLICATE_NO_OUTPUT' if a=='SPLIT_CHECK' else 'HOLD_BUSY'],
        'RESERVED_EXIT':[None,'DUPLICATE_NO_OUTPUT','HOLD_BUDGET'],
        'STALE_SCOPE':['REJECT_SCOPE','READY'],
    }[s]
    if a=='PER_REQUEST':
        return [None,'READY','READY'] if s=='RESERVED_EXIT' else (['REJECT_SCOPE','READY'] if s=='STALE_SCOPE' else ['READY']*len(ordinary))
    return ordinary

def canonical(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(data):return hashlib.sha256(data).hexdigest()

def independent_images(request):
    c=request['cues'][0];ctx=request['context']
    if any(c[k]!=ctx[k] for k in ('generation','intent','session','surface')):return None
    x,y,w,h=c['roi'];images=[]
    frames=sorted((f for f in request['frames'] if c['emitted_ns']-5_000_000_000<=f['capture_end_ns']<=c['emitted_ns']),
                  key=lambda f:(f['capture_end_ns'],f['sequence']))[-2:]
    for f in frames:
        data=base64.b64decode(f['rgb_b64'],validate=True)
        if len(data)!=128*64*3 or digest(data)!=f['rgb_sha256']:raise ValueError('fixture pixels')
        out=bytearray()
        for row in range(y,y+h):
            for col in range(x,x+w):
                offset=3*(row*128+col)
                for channel in range(3):out.append(data[offset+channel])
        images.append((f,bytes(out)))
    return images

def audit(root:Path,phase='pilot'):
    checks=0;errors=[]
    def ck(condition,tag):
        nonlocal checks
        checks+=1
        if not condition:errors.append(tag)
    def js(path):
        try:return json.loads(path.read_bytes())
        except (OSError,ValueError):ck(False,'missing_or_invalid:'+str(path.relative_to(root)));return None
    base=root/phase
    original=js(root/'fixture/original_request.json')
    reps=(99,) if phase=='construction' else ((98,) if phase=='construction02' else (0,1))
    case_specs=[(f'r{r}-{s.lower()}-{a.lower()}',s,a,r) for r in reps for s in SCENARIOS for a in ARMS]
    if phase=='pilot':
        case_specs=[x for x in case_specs if x[1] not in ('OVERFLOW','STALE_SCOPE') and x[2]!='PER_REQUEST']
    ck(sorted(p.name for p in base.iterdir() if p.is_dir())==sorted(x[0] for x in case_specs),'case_denominator')
    if phase=='pilot':
        freeze=js(root/'FREEZE.json')
        if freeze:
            for name,h in freeze['files'].items():
                try:ck(digest((root/name).read_bytes())==h,'source:'+name)
                except OSError:ck(False,'source_missing:'+name)
    n_batches=1 if phase=='construction' else 4
    for b in range(n_batches):
        bs=js(base/f'BATCH_{b}_START.json');be=js(base/f'BATCH_{b}_END.json')
        ex=js(base/f'BATCH_{b}_EXIT.json')
        ids=[x[0] for x in (case_specs if phase=='construction' else case_specs[b*6:b*6+6])]
        if bs and be:
            if phase=='pilot':ck(bs.get('freeze_sha')==digest((root/'FREEZE.json').read_bytes()),f'batch{b}:freeze_binding')
            ck([x['case_id'] for x in bs['specifications']]==ids,f'batch{b}:start_ids')
            ck(be.get('cases')==ids and be.get('complete') is True,f'batch{b}:end')
            ck(bs['start_ns']<=be['end_ns'] and bs['pid']==be['pid'],f'batch{b}:order')
        if ex:ck(ex.get('exit')==0,f'batch{b}:exit')
    stats={a:{'cases':0,'attempts':0,'ready':0,'emitted_rgb_bytes':0,'reserved_bytes':0,
              'over_budget_cases':0,'repeated_id_outputs':0,'reservation_without_output_bytes':0} for a in ARMS}
    rows=[];all_pids=[]
    for case_id,s,a,r in case_specs:
        d=base/case_id;cfg=js(d/'config.json');end=js(d/'CASE_END.json')
        if not cfg or not end:continue
        cap=6144 if s in ('RACE_QUOTA','RESERVED_EXIT') else 12288
        ck(cfg==dict(case_id=case_id,scenario=s,arm=a,repetition=r,scope=f'cue-budget-b6e1/{phase}/{case_id}',cap=cap),case_id+':config')
        exp=expected_statuses(s,a);n=len(exp)
        ck(end.get('complete') is True and end.get('attempts')==n,case_id+':end')
        ck(sorted(x.name for x in d.iterdir() if x.is_dir())==[f'a{i}' for i in range(n)],case_id+':attempt_denominator')
        attempts=[];outputs=[];expected_claims=[]
        for i,want in enumerate(exp):
            tag=f'{case_id}/a{i}';folder=d/f'a{i}'
            st=js(folder/'START.json');ex=js(folder/'EXIT.json');req=js(folder/'request.json')
            if st is None or ex is None or req is None:continue
            expect_req=json.loads(json.dumps(original));cue=expect_req['cues'][0]
            cue['cue_id']=('A' if i==0 else chr(65+i))
            if s in ('RESTART_REPEAT','ID_CONFLICT','RACE_DUPLICATE'):cue['cue_id']='A'
            if s=='RESERVED_EXIT':cue['cue_id']='A' if i<=1 else 'B'
            if s=='STALE_SCOPE':
                cue['cue_id']='A'
                if i==0:cue['generation']+=1
            if s=='ID_CONFLICT' and i==1:cue['roi']=[0,0,32,32]
            ck(req==expect_req,tag+':request_content')
            raw=(folder/'request.json').read_bytes()
            ck(raw==canonical(req),tag+':canonical_request')
            try:
                stdout=(folder/'stdout.jsonl').read_bytes();events=[json.loads(x) for x in stdout.splitlines()]
                ck(stdout.endswith(b'\n'),tag+':full_records')
            except (OSError,ValueError):ck(False,tag+':stdout');continue
            ck(digest(stdout)==ex.get('stdout_sha'),tag+':stdout_sha')
            ck(digest(raw)==ex.get('request_sha'),tag+':request_sha')
            ck((folder/'stderr').read_bytes()==b'',tag+':stderr_empty')
            ck(digest((folder/'stderr').read_bytes())==ex.get('stderr_sha'),tag+':stderr_sha')
            cut=s=='RESERVED_EXIT' and i==0
            ck(ex.get('exit')==(23 if cut else 0),tag+':exit_code')
            ck(ex.get('pid')==st.get('pid'),tag+':pid');all_pids.append(st['pid'])
            ck(st.get('cut') is cut and st.get('pause') is s.startswith('RACE_'),tag+':launch_mode')
            ck(len(events)>=3 and events[0]['kind']=='START' and events[1]['kind']=='PREPARED',tag+':event_start')
            ck(all(e['pid']==st['pid'] for e in events),tag+':event_pid')
            ck(all(type(e['at_ns']) is int for e in events),tag+':time_types')
            ck([e['at_ns'] for e in events]==sorted(e['at_ns'] for e in events),tag+':time_order')
            ck(st['started_ns']<=events[0]['at_ns']<=events[-1]['at_ns']<=ex['finished_ns'],tag+':time_bracket')
            ck(events[0].get('request_sha')==digest(raw),tag+':start_request_binding')
            results=[e for e in events if e['kind']=='RESULT'];checked=[e for e in events if e['kind']=='CHECKED']
            reserve=[e for e in events if e['kind']=='RESERVATION'];cuts=[e for e in events if e['kind']=='DECLARED_EXIT']
            ck(len(results)==(0 if cut else 1),tag+':result_count')
            ck(len(checked)<=1 and len(reserve)<=1,tag+':single_admission')
            if checked:ck(checked[0].get('in_transaction') is (a=='ATOMIC_RESERVE'),tag+':transaction_boundary')
            if cut:ck(len(cuts)==1 and cuts[0]['code']==23 and cuts[0]['before_output'] is True,tag+':declared_cut')
            else:ck(cuts==[],tag+':no_extra_cut')
            oracle=independent_images(req)
            ck(events[1].get('rgb_bytes')==(0 if oracle is None else 6144),tag+':prepared_exact_cost')
            if results:
                result=results[0];ck(result.get('status')==want,tag+':status')
                ck(result.get('grants_authority') is False,tag+':authority')
                if want=='READY':
                    ck(oracle is not None and len(oracle)==2,tag+':oracle_coverage')
                    payload=result.get('payload');ck(isinstance(payload,dict),tag+':payload')
                    if isinstance(payload,dict):
                        ck(set(payload)=={'responses','grants_authority','task_input','extends_lease','verifies_effect'},tag+':payload_schema')
                        ck(all(payload.get(k) is False for k in ('grants_authority','task_input','extends_lease','verifies_effect')),tag+':payload_non_authority')
                        rr=payload['responses'];ck(len(rr)==1,tag+':response_count');rr=rr[0]
                        ck(rr['status']=='ATTENTION_READY' and rr['rgb_bytes']==6144,tag+':upstream_status')
                        ck(all(rr.get(k) is False for k in ('grants_authority','task_input','extends_lease','verifies_effect')),tag+':response_non_authority')
                        ck(len(rr['images'])==2,tag+':image_count');total=0
                        for j,(frame,pix) in enumerate(oracle or []):
                            im=rr['images'][j];b=base64.b64decode(im['rgb_b64'],validate=True);total+=len(b)
                            ck(b==pix,tag+f':pixels{j}')
                            ck(im['sha256']==digest(b) and im['bytes']==len(b),tag+f':image_hash{j}')
                            ck(im['source_sha256']==frame['rgb_sha256'] and im['sequence']==frame['sequence'] and im['capture_end_ns']==frame['capture_end_ns'] and im['roi']==cue['roi'],tag+f':source_binding{j}')
                        ck(total==result['rgb_bytes']==6144,tag+':emitted_count')
                        outputs.append((cue['cue_id'],digest(raw),total))
                    ck(len(reserve)==1 and reserve[0]['status']=='COMMITTED',tag+':reserve_before_output')
                    if reserve:ck(reserve[0]['at_ns']<=result['at_ns'],tag+':commit_order')
                else:ck(result.get('rgb_bytes')==0 and result.get('payload') is None,tag+':no_payload_on_refusal')
            if reserve and reserve[0]['status']=='COMMITTED':
                ck(reserve[0]['claim'] is (a!='PER_REQUEST'),tag+':claim_flag')
                ck(reserve[0]['reserved_cost']==(0 if a=='PER_REQUEST' else 6144),tag+':reserved_cost')
                if a!='PER_REQUEST':expected_claims.append((cfg['scope'],cue['cue_id'],digest(raw),6144))
            attempts.append({'events':events,'st':st,'ex':ex})
        ck(len(attempts)==n,case_id+':complete_processes')
        ck(len(end.get('exits',[]))==n and sorted(x['pid'] for x in end['exits'])==sorted(x['st']['pid'] for x in attempts),case_id+':end_process_ids')
        if s.startswith('RACE_') and len(attempts)==2:
            e0,e1=(x['events'] for x in attempts)
            c0=next((e for e in e0 if e['kind']=='CHECKED'),None)
            c1=next((e for e in e1 if e['kind'] in ('CHECKED','DECISION')),None)
            r0=next((e for e in e0 if e['kind']=='RESERVATION'),None)
            ck(c0 is not None and c1 is not None and r0 is not None,case_id+':race_exposure')
            if c0 and c1 and r0:
                ck(c0['at_ns']<c1['at_ns']<r0['at_ns'],case_id+':overlapped_check_order')
                if a=='ATOMIC_RESERVE':ck(c1.get('status')=='HOLD_BUSY',case_id+':actual_busy')
                else:ck(c0['used']==c1['used']==0 and c0['prior_sha'] is None and c1['prior_sha'] is None,case_id+':stale_read_witness')
        db=None
        try:
            db=sqlite3.connect('file:'+str((d/'quota.sqlite').resolve())+'?mode=ro&immutable=1',uri=True)
            ck(db.execute('PRAGMA integrity_check').fetchall()==[('ok',)],case_id+':sqlite_integrity')
            ck(db.execute('SELECT scope,cap FROM config').fetchall()==[(cfg['scope'],cap)],case_id+':sqlite_config')
            claims=db.execute('SELECT scope,cue_id,request_sha,cost FROM claims ORDER BY seq').fetchall()
            ck(claims==expected_claims,case_id+':claims_from_raw')
        except (OSError,sqlite3.Error):ck(False,case_id+':database_read');claims=[]
        finally:
            if db:db.close()
        out_bytes=sum(x[2] for x in outputs);charged=sum(x[3] for x in claims)
        repeated=len(outputs)-len(set(x[0] for x in outputs))
        stranded=charged-sum(x[2] for x in outputs) if a!='PER_REQUEST' else 0
        if a=='ATOMIC_RESERVE':
            ck(out_bytes<=charged<=cap,case_id+':candidate_quota_invariant')
            ck(repeated==0,case_id+':candidate_no_duplicate_output')
        row={'case_id':case_id,'scenario':s,'arm':a,'attempts':n,'ready':len(outputs),'rgb_bytes':out_bytes,
             'cap':cap,'reserved_bytes':charged,'over_budget':out_bytes>cap,'repeated_id_outputs':repeated,
             'reservation_without_output_bytes':stranded}
        rows.append(row);stt=stats[a];stt['cases']+=1;stt['attempts']+=n;stt['ready']+=len(outputs)
        stt['emitted_rgb_bytes']+=out_bytes;stt['reserved_bytes']+=charged
        stt['over_budget_cases']+=int(out_bytes>cap);stt['repeated_id_outputs']+=repeated
        stt['reservation_without_output_bytes']+=stranded
    ck(len(rows)==len(case_specs),'complete_cases')
    # PID uniqueness is not assumed globally; operating systems may reuse them.
    return {'phase':phase,'checks':checks,'errors':errors,'cases':len(rows),'worker_receipts':len(all_pids),
            'stats':stats,'rows':rows,'scope':'LOCAL_HISTORICAL_IMAGE_PROCESS_PILOT_NO_GUI_NO_MODEL',
            'decision':'PASS_LOCAL_CUMULATIVE_CUE_BUDGET_BOUNDARY' if not errors else 'HOLD_OR_FAIL_LOCAL_GATE'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--phase',default='pilot');a=p.parse_args()
    result=audit(a.root,a.phase);print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(bool(result['errors']))
