"""Raw-only auditor: does not import study, batch, reader, or DeliveryLedger."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parent
SID='issue3985-fixed-lifetime'

def enc(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def sha(x):
    return hashlib.sha256(x).hexdigest()

def check(ok,label):
    if not ok:
        raise ValueError(label)

def equal(a,b,label):
    check(enc(a)==enc(b),label)

def expected_stream(n):
    parts=[]
    for i in range(1,n+1):
        obj={'delivery_id':f'delivery:{i}','event':'observation','index':i,'pad':''}
        obj['pad']='x'*(255-len(enc(obj)))
        parts.append(enc(obj)+b'\n')
    return b''.join(parts)

def cursor(data,offset):
    return {'schema':'agent-interface/experimental-read-cursor-v1','stream_id':SID,
            'offset':offset,'prefix_sha256':sha(data[:offset]),'next_sequence':offset//256+1}

def response(data,old,page):
    end=min(len(data),old+page*256)
    return {'schema':'agent-interface/experimental-inbox-read-v1',
            'records':[json.loads(x) for x in data[old:end].splitlines()],
            'tail_state':'limit' if end<len(data) else 'end','problem':None,
            'next_cursor':cursor(data,end),'authority':'none','acknowledged':False,'input_dispatched':False}

def clock(v,label):
    for key in ('wall_start_ns','wall_end_ns','cpu_start_ns','cpu_end_ns'):
        check(type(v[key]) is int and v[key]>=0,label+':'+key)
    check(v['wall_end_ns']>=v['wall_start_ns'] and v['cpu_end_ns']>=v['cpu_start_ns'],label+':order')

def audit_case(raw,data,expected):
    n,page,rep=expected
    equal([raw['n'],raw['page'],raw['rep'],raw['line_bytes'],raw['max_bytes']],
          [n,page,rep,256,1048576],'allocation_fields')
    equal(raw['source_blobs'],{'reader.py':'ea72c166c2cea511ea91031dfbb14563fe4e3245',
          'delivery_ledger_v2.py':'fb50be9d4d821a7836e6a0158c53a983f0f91df5'},'source_blobs')
    check(type(raw['pid']) is int and raw['pid']>0,'pid')
    check(data==expected_stream(n),'source_stream')
    check(raw['stream_sha256']==raw['stream_after_sha256']==sha(data),'stream_hash')
    m=n//page
    for name in ('plain','measured'):
        leg=raw[name]
        clock(leg,name)
        check(len(leg['calls'])==m+1,'call_count')
        old=0
        previous=None
        lastwall=leg['wall_start_ns']
        lastcpu=leg['cpu_start_ns']
        for j,item in enumerate(leg['calls']):
            clock(item,name+str(j))
            check(lastwall<=item['wall_start_ns']<=item['wall_end_ns']<=leg['wall_end_ns'],'wall_containment')
            check(lastcpu<=item['cpu_start_ns']<=item['cpu_end_ns']<=leg['cpu_end_ns'],'cpu_containment')
            equal(item['request_cursor'],previous,'request_cursor')
            want=response(data,old,page)
            equal(item['response'],want,'response')
            previous=want['next_cursor']
            old=previous['offset']
            lastwall,lastcpu=item['wall_end_ns'],item['cpu_end_ns']
        check(old==len(data),'final_offset')
    equal(raw['plain']['read_calls'],[],'plain_instrumented')
    equal(raw['plain']['hash_lengths'],[],'plain_hash_instrumented')
    equal(raw['measured']['read_calls'],[[1048577,len(data)]]*(m+1),'read_lengths')
    hs=[]
    for j in range(m):
        hs.extend([j*page*256,(j+1)*page*256])
    hs.extend([len(data),len(data)])
    equal(raw['measured']['hash_lengths'],hs,'hash_lengths')
    read_total=sum(v[1] for v in raw['measured']['read_calls'])
    hash_total=sum(raw['measured']['hash_lengths'])
    check(read_total==(m+1)*len(data),'read_law')
    check(hash_total==(m+2)*len(data),'hash_law')
    p=raw['plain']
    return {'n':n,'page':page,'rep':rep,'logical_read_bytes':read_total,
            'hash_input_bytes':hash_total,'wall_ns':p['wall_end_ns']-p['wall_start_ns'],
            'cpu_ns':p['cpu_end_ns']-p['cpu_start_ns']}

def audit_capacity(folder,raw=None):
    raw=raw or json.loads((folder/'RAW.json').read_bytes())
    check(raw['schema']=='pagination-capacity-3985-v1','cap_schema')
    check(len(raw['rows'])==9,'cap_count')
    schedule=[(p,m) for p in (1,8,32) for m in ('exact_cap','overflow_initial','overflow_suffix')]
    base=expected_stream(4)
    for r,(p,m) in zip(raw['rows'],schedule):
        equal([r['page'],r['mode']],[p,m],'cap_identity')
        check(r['source']==f'{p}-{m}.jsonl','cap_path')
        data=(folder/r['source']).read_bytes()
        check(data==base+(b'' if m=='exact_cap' else b' '),'cap_bytes')
        equal(r['bytes'],len(data),'cap_len')
        check(r['before_sha256']==r['after_sha256']==sha(data),'cap_hash')
        equal(r['cursor_before_json'],r['cursor_after_json'],'cap_cursor_mutation')
        c=None
        if m=='overflow_suffix':
            equal(r['initial'],response(base,0,2),'cap_initial')
            c=cursor(base,512)
        else:
            equal(r['initial'],None,'cap_no_initial')
        check(r['cursor_before_json']==enc(c).decode(),'cap_request')
        if m=='exact_cap':
            equal(r['response'],response(base,0,p),'cap_response')
            equal(r['error'],None,'cap_error')
        else:
            equal(r['response'],None,'cap_no_response')
            equal(r['error'],'STREAM_READ_BOUND_EXCEEDED','cap_overflow')
    return 9

def process_receipt(folder,r):
    check(type(r['exit_code']) is int and r['exit_code']==0 and r['timeout'] is False,'process_exit')
    name=r['name']
    stdout=(folder/(name+'.stdout')).read_bytes()
    stderr=(folder/(name+'.stderr')).read_bytes()
    check(sha(stdout)==r['stdout_sha256'] and sha(stderr)==r['stderr_sha256'] and not stderr,'process_logs')
    payload=json.loads(stdout)
    check(payload['pid']==r['pid'] and payload['status']=='completed','process_identity')
    raw=(folder/name/'RAW.json').read_bytes()
    check(sha(raw)==payload['raw_sha256'],'process_raw_hash')
    check(json.loads(raw)['pid']==r['pid'],'raw_pid')

def audit_all(formal):
    freeze=json.loads((ROOT/'FREEZE.json').read_bytes())
    for rel,digest in freeze['sha256'].items():
        check(sha((ROOT/rel).read_bytes())==digest,'freeze:'+rel)
    rows=[]
    previous=None
    for index,n in enumerate((128,256,512,1024)):
        folder=formal/f'batch-{index}'
        supervisor=json.loads((folder/'SUPERVISOR.json').read_bytes())
        check(type(supervisor['exit_code']) is int and supervisor['exit_code']==0 and supervisor['timeout'] is False,'batch_exit')
        equal(supervisor['index'],index,'batch_index')
        check(sha((folder/'batch.stdout').read_bytes())==supervisor['stdout_sha256'],'batch_stdout')
        check(sha((folder/'batch.stderr').read_bytes())==supervisor['stderr_sha256'] and not (folder/'batch.stderr').read_bytes(),'batch_stderr')
        check(supervisor['batch_sha256']==sha((folder/'BATCH.json').read_bytes()),'batch_hash')
        batch=json.loads((folder/'BATCH.json').read_bytes())
        equal(json.loads((folder/'batch.stdout').read_bytes()),batch,'batch_stdout_payload')
        equal([batch['index'],batch['n']],[index,n],'batch_identity')
        check(batch['pid']==supervisor['pid'] and batch['status']=='completed','batch_pid')
        check(batch['freeze_sha256']==sha((ROOT/'FREEZE.json').read_bytes()),'batch_freeze')
        equal(batch['previous_supervisor_sha256'],previous,'batch_chain')
        previous=sha((folder/'SUPERVISOR.json').read_bytes())
        prs=json.loads((folder/'PROCESSES.json').read_bytes())
        check(batch['process_receipts_sha256']==sha((folder/'PROCESSES.json').read_bytes()),'receipts_hash')
        check(len(prs)==batch['processes']==(10 if index==3 else 9),'process_count')
        expected=[]
        for rep in range(3):
            pages=[1,8,32]
            for page in pages[rep:]+pages[:rep]:
                expected.append((n,page,rep))
        for r,e in zip(prs[:9],expected):
            process_receipt(folder,r)
            name=f'n{e[0]}-p{e[1]}-r{e[2]}'
            check(r['name']==name,'schedule')
            d=folder/name
            rows.append(audit_case(json.loads((d/'RAW.json').read_bytes()),(d/'stream.jsonl').read_bytes(),e))
        if index==3:
            check(prs[9]['name']=='capacity','cap_process')
            process_receipt(folder,prs[9])
            audit_capacity(folder/'capacity')
    summaries=[]
    for n in (128,256,512,1024):
        for page in (1,8,32):
            selected=[r for r in rows if r['n']==n and r['page']==page]
            vals=[r['wall_ns'] for r in selected]
            cpus=[r['cpu_ns'] for r in selected]
            summaries.append({'n':n,'page':page,'wall_median_ns':statistics.median(vals),
                 'wall_min_ns':min(vals),'wall_max_ns':max(vals),'cpu_median_ns':statistics.median(cpus),
                 'logical_read_bytes':selected[0]['logical_read_bytes'],'hash_input_bytes':selected[0]['hash_input_bytes']})
    small=next(r for r in summaries if r['n']==1024 and r['page']==1)['wall_median_ns']
    large=next(r for r in summaries if r['n']==1024 and r['page']==32)['wall_median_ns']
    ratio=small/large
    return {'integrity':'PASS','work_law':'PASS_PAGINATION_WORK_LAW_SCOPED',
            'timing':'PASS_LOCAL_BATCHING_TIME_SCOPED' if ratio>=2 else 'HOLD_LOCAL_BATCHING_TIME_NOT_ESTABLISHED',
            'page1_over_page32_wall_ratio':ratio,'cases':36,'capacity_controls':9,'processes':37,
            'summaries':summaries,'rows':rows,'errors':[]}

def mutations(folder):
    raw=json.loads((folder/'RAW.json').read_bytes());data=(folder/'stream.jsonl').read_bytes()
    expected=(raw['n'],raw['page'],raw['rep'])
    functions={
      'missing_call':lambda x:x['plain']['calls'].pop(),
      'changed_payload':lambda x:x['plain']['calls'][0]['response']['records'][0].update(index=99),
      'invented_ack':lambda x:x['plain']['calls'][0]['response'].update(acknowledged=True),
      'bool_cursor':lambda x:x['plain']['calls'][0]['response']['next_cursor'].update(next_sequence=True),
      'read_count':lambda x:x['measured']['read_calls'][0].__setitem__(1,1),
      'hash_count':lambda x:x['measured']['hash_lengths'].__setitem__(0,1),
      'clock_reverse':lambda x:x['plain'].update(wall_end_ns=0),
      'source_identity':lambda x:x['source_blobs'].update({'reader.py':'0'*40}),
      'allocation':lambda x:x.update(rep=99),
      'boolean_hash_count':lambda x:x['measured']['hash_lengths'].__setitem__(0,False)}
    results={}
    for name,fn in functions.items():
        altered=copy.deepcopy(raw);fn(altered)
        try:
            audit_case(altered,data,expected)
        except (ValueError,KeyError,TypeError,IndexError) as exc:
            results[name]={'rejected':True,'reason':str(exc)}
        else:
            results[name]={'rejected':False}
    check(all(v['rejected'] for v in results.values()),'mutation_accepted')
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('path',type=Path)
    p.add_argument('--case',action='store_true')
    p.add_argument('--controls',action='store_true')
    a=p.parse_args()
    try:
        if a.case:
            raw=json.loads((a.path/'RAW.json').read_bytes())
            result={'integrity':'PASS','row':audit_case(raw,(a.path/'stream.jsonl').read_bytes(),(64,4,-1))}
            control_path=a.path
        else:
            result=audit_all(a.path)
            control_path=a.path/'batch-0'/'n128-p1-r0'
        if a.controls:
            result['corruption_controls']=mutations(control_path)
        print(json.dumps(result,sort_keys=True,separators=(',',':')))
    except (ValueError,KeyError,TypeError,IndexError,FileNotFoundError,json.JSONDecodeError) as exc:
        print(json.dumps({'integrity':'HOLD_OR_FAIL','errors':[str(exc)]}))
        raise SystemExit(2)
