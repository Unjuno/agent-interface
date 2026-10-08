"""Independent raw-result auditor: stdlib only, never imports tested code."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics

ROOT=Path(__file__).resolve().parent
NAMES=('applied','stale','revision_conflict','same_value','absent','altered_request',
       'invalid_epoch','duplicate_commit','missing_commit','unknown_status')

def b(x):return json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode()
def h(x):return hashlib.sha256(x).hexdigest()
def job(session,identity,revision,value,kind='AUTO'):
    return {'document':'doc','epoch':'epoch-1','job_id':identity,'kind':kind,
            'revision':revision,'session':session,'value':value}

def fixture_commitment(n,session,after=False):
    """Reconstruct the synthetic input independently, not from stored summaries."""
    count=21 if after else 0
    d=hashlib.sha256()
    d.update(b'document\n')
    d.update(b([1,n+count,f'append-value-{count:08d}' if after else f'value-{n:08d}'])+b'\n')
    d.update(b'commits\n')
    for i in range(1,n+1):d.update(b([i,f'bg-{i:08d}',i,f'value-{i:08d}','AUTO'])+b'\n')
    for i in range(1,count+1):d.update(b([n+i,f'append-{i:08d}',n+i,f'append-value-{i:08d}','SUBMIT'])+b'\n')
    d.update(b'seen\n')
    for i in range(1,count+1):
        j=job(session,f'append-{i:08d}',n+i,f'append-value-{i:08d}','SUBMIT')
        d.update(b([j['job_id'],h(b(j)),'APPLIED'])+b'\n')
    for i in range(1,n+1):
        j=job(session,f'bg-{i:08d}',i,f'value-{i:08d}')
        d.update(b([j['job_id'],h(b(j)),'APPLIED'])+b'\n')
    return {'sha256':d.hexdigest(),'counts':{'document':1,'commits':n+count,'seen':n+count}}

def empty_result():
    return {'schema':'research/replay-first-outcome-v1','outcome':'UNKNOWN_INCONSISTENT',
            'request_sha256':None,'stored_status':None,'request_commit_count':None,
            'current_state':None,'current_value_matches':None,'authority':False,
            'replay_authority':False,'task_success':None}

def reference(j,session,doc,seen,commits):
    out=empty_result()
    fields={'session','document','epoch','job_id','revision','value','kind'}
    if (type(j)!=dict or set(j)!=fields or j['session']!=session or not session or
        j['document']!='doc' or j['epoch']!='epoch-1' or type(j['revision'])!=int or
        not 0<j['revision']<2**63 or type(j['value'])!=str or len(j['value'])>64 or
        type(j['job_id'])!=str or not 0<len(j['job_id'])<=80 or j['kind'] not in ('AUTO','SUBMIT')):
        out['outcome']='INVALID_QUERY';return out
    out['request_sha256']=h(b(j))
    out['current_state']={'revision':doc[0],'value':doc[1]}
    out['current_value_matches']=doc[1]==j['value']
    receipts=[r for r in seen if r[0]==j['job_id']]
    events=[r for r in commits if r[1]==j['job_id']]
    if not receipts:
        if not events:out['outcome']='NOT_RECORDED'
        return out
    if len(receipts)!=1:return out
    if receipts[0][1]!=out['request_sha256']:
        out['outcome']='CONFLICT_ID';return out
    status=receipts[0][2]
    if status=='APPLIED':
        desired=[j['job_id'],j['revision'],j['value'],j['kind']]
        if len(events)==1 and type(events[0][0])==int and events[0][0]>0 and list(events[0][1:])==desired:
            out.update(outcome='APPLIED_ONCE',stored_status=status,request_commit_count=1)
    elif not events:
        mapping={'STALE':'REJECTED_STALE','CONFLICT_REVISION':'REJECTED_REVISION_CONFLICT',
                 'DUPLICATE_REVISION':'NO_NEW_COMMIT_SAME_VALUE'}
        if status in mapping:out.update(outcome=mapping[status],stored_status=status,request_commit_count=0)
    return out

def check_index(rows,arm,need):
    if arm=='PLAIN':need(rows==[],'unexpected index')
    else:need(len(rows)==1 and b(rows[0][1:]) == b(['commits_by_job',0,'c',0]), 'index must be ordinary non-unique')

def decode(envelope,need):
    raw=base64.b64decode(envelope['stdout_b64'],validate=True)
    need(h(raw)==envelope['stdout_sha256'],'stdout digest')
    need(type(envelope['exit']) is int and envelope['exit']==0,'worker exit')
    need(envelope['timeout'] is False,'worker timeout')
    need(envelope['stderr_b64']=='','worker stderr')
    need(type(envelope['pid']) is int and envelope['pid']>0,'worker pid')
    need(envelope['start_ns']<envelope['end_ns'],'worker time bounds')
    out=json.loads(raw)
    need(out['pid']==envelope['pid'],'pid join')
    argv=envelope['argv']
    need(argv[1:3]==['-S','-B'] and Path(argv[3]).name=='worker.py','argv interpreter/worker')
    for flag,expected in [('--phase',out['phase']),('--arm',out['arm'])]:
        need(argv[argv.index(flag)+1]==expected,'argv '+flag)
    if out['kind']=='performance':
        for flag,expected in [('--n',str(out['n'])),('--rep',str(out['repetition']))]:
            need(argv[argv.index(flag)+1]==expected,'argv '+flag)
    else:need('--contracts' in argv,'contract argv')
    return out

def analyze(envelopes,complete=True):
    errors=[];checks=0;unexpected=[];perf=[];contracts=[]
    def need(condition,message):
        nonlocal checks
        checks+=1
        if not condition:errors.append(message)
    expected_sources={n:h((ROOT/n).read_bytes()) for n in ('query.py','sink.py','worker.py')}
    env=json.loads((ROOT/'ENVIRONMENT.json').read_text())
    commitments={}
    for number,envelope in enumerate(envelopes):
      try:
        o=decode(envelope,need)
        need(o['arm'] in ('PLAIN','INDEXED'),'arm')
        need(o['source_ids']==expected_sources,'loaded source identity')
        need(o['affinity']==env['worker_affinity'],'worker affinity')
        if o['kind']=='performance':
            n=o['n'];session=o['session'];rep=o['repetition'];arm=o['arm']
            need(type(n)==int and n>=4 and type(rep)==int and rep in range(3),'workload shape')
            need(session==f"i6k2-{o['phase']}-{n}",'session')
            key=(n,session)
            if key not in commitments:commitments[key]=(fixture_commitment(n,session),fixture_commitment(n,session,True))
            initial,final=commitments[key]
            need(b(o['seed'])==b(initial) and b(o['before'])==b(initial) and b(o['after_query'])==b(initial),'logical input/index/readonly parity')
            need(b(o['final'])==b(final),'append state/table commitment')
            need(o['db_sha_before_queries']==o['db_sha_after_queries'],'read-only physical bytes')
            need(len(o['db_sha_before_queries'])==64 and len(o['final_db_sha256'])==64,'DB digests')
            check_index(o['index_list'],arm,need)
            need(o['index_columns']==([] if arm=='PLAIN' else [[0,1,'job_id']]),'indexed column')
            need(o['pragmas']['journal_mode']=='delete' and o['pragmas']['synchronous']==2 and o['pragmas']['read_uncommitted']==0,'SQLite settings')
            need(o['final_bytes']==o['pragmas']['page_size']*o['pragmas']['page_count'],'file/page size')
            need(o['index_bytes']>=o['seed_bytes']>0,'index file cost')
            if arm=='PLAIN':need(o['index_build'] is None and o['index_bytes']==o['seed_bytes'],'no index treatment')
            else:
                z=o['index_build'];need(z['result'] is None and z['wall'][1]>z['wall'][0] and z['cpu'][1]>=z['cpu'][0],'index build clocks')
            requests=[job(session,f'bg-{i:08d}' if i<=n else 'absent-job',i,f'value-{i:08d}') for i in (1,n//2,n,n+1)]
            need(b(o['requests'])==b(requests),'query input recipe')
            expected=[]
            for j in requests:
                present=j['revision']<=n
                s=[[j['job_id'],h(b(j)),'APPLIED']] if present else []
                c=[[j['revision'],j['job_id'],j['revision'],j['value'],'AUTO']] if present else []
                expected.append(reference(j,session,(n,f'value-{n:08d}'),s,c))
            need(len(o['warmups'])==8 and len(o['samples'])==44,'query denominator')
            for i,z in enumerate(o['warmups']):
                k=i%4;need(z['round']==i//4 and z['query_class']==k and b(z['result'])==b(expected[k]),'warmup output/order')
            for i,z in enumerate(o['samples']):
                r=i//4;k=(r+i%4)%4
                need(z['round']==r and z['query_class']==k,'sample order')
                need(b(z['result'])==b(expected[k]),'query result semantics')
                need(type(z['wall'][0]) is int and z['wall'][0]<z['wall'][1] and z['cpu'][0]<=z['cpu'][1],'query clocks')
                need(envelope['start_ns']<=z['wall'][0]<z['wall'][1]<=envelope['end_ns'],'query in process interval')
            need(len(o['appends'])==21,'append denominator')
            for i,z in enumerate(o['appends'],1):
                j=job(session,f'append-{i:08d}',n+i,f'append-value-{i:08d}','SUBMIT')
                before={'revision':n+i-1,'value':f'value-{n:08d}' if i==1 else f'append-value-{i-1:08d}'}
                after={'revision':n+i,'value':j['value']}
                need(b(z['request'])==b(j),'append recipe')
                need(b(z['result'])==b(dict(status='APPLIED',before=before,state=after,authority=False)),'append semantics')
                need(z['wall'][0]<z['wall'][1] and z['cpu'][0]<=z['cpu'][1],'append clocks')
            need(len(o['plans'])==4 and all(p and len(p[0])==4 for p in o['plans']),'query plan receipts')
            perf.append(o)
        elif o['kind']=='contracts':
            need([x['name'] for x in o['cases']]==list(NAMES),'contract denominator/order')
            category={'applied':'APPLIED_ONCE','stale':'REJECTED_STALE','revision_conflict':'REJECTED_REVISION_CONFLICT',
                      'same_value':'NO_NEW_COMMIT_SAME_VALUE','absent':'NOT_RECORDED','altered_request':'CONFLICT_ID',
                      'invalid_epoch':'INVALID_QUERY','duplicate_commit':'UNKNOWN_INCONSISTENT',
                      'missing_commit':'UNKNOWN_INCONSISTENT','unknown_status':'UNKNOWN_INCONSISTENT'}
            for z in o['cases']:
                raw=base64.b64decode(z['db_b64'],validate=True)
                need(h(raw)==z['db_sha256']==z['after_sha256'],'contract DB read-only bytes')
                con=sqlite3.connect(':memory:')
                try:
                    con.deserialize(raw)
                    doc=con.execute('SELECT revision,value FROM document').fetchone()
                    s=con.execute('SELECT job_id,fingerprint,status FROM seen ORDER BY job_id').fetchall()
                    c=con.execute('SELECT ordinal,job_id,revision,value,kind FROM commits ORDER BY ordinal').fetchall()
                    actual_index=[list(r) for r in con.execute('PRAGMA index_list(commits)')]
                finally:con.close()
                need(z['index_list']==actual_index,'literal contract index')
                check_index(actual_index,o['arm'],need)
                expect=reference(z['request'],z['session'],doc,s,c)
                need(b(z['result'])==b(expect),'contract relational oracle')
                need(expect['outcome']==category[z['name']],'directed contract condition')
                need(z['sql_trace']==[] if z['name']=='invalid_epoch' else ('BEGIN' in z['sql_trace'] and 'COMMIT' in z['sql_trace']),'query transaction/no-open')
                if z['name']=='duplicate_commit':need(len(c)==2,'duplicate evidence retained')
            contracts.append(o)
        else:need(False,'unknown record kind')
      except Exception as error:
        unexpected.append({'record':number,'error':repr(error)})
    if complete:
        expected={(n,a,r) for n in (256,4096,32768) for a in ('PLAIN','INDEXED') for r in range(3)}
        need(len(perf)==18 and {(x['n'],x['arm'],x['repetition']) for x in perf}==expected,'complete performance matrix')
        need(len(contracts)==2 and {x['arm'] for x in contracts}=={'PLAIN','INDEXED'},'complete contract workers')
        need(all(x['phase']=='formal' for x in perf+contracts),'formal phase')
    return dict(errors=errors,unexpected_errors=unexpected,checks=checks,performance=perf,contracts=contracts)

def load(directory):
    return [json.loads(p.read_text()) for p in sorted(Path(directory).glob('batch-*/worker-*.json'))]

def extent(values):
    return {'median':statistics.median(values),'min':min(values),'max':max(values)}

def summary(a):
    rows=[];ratios={}
    for n in sorted({r['n'] for r in a['performance']}):
        by_arm={}
        for arm in ('PLAIN','INDEXED'):
            workers=sorted([r for r in a['performance'] if r['n']==n and r['arm']==arm],key=lambda r:r['repetition'])
            totals=[sum(s['wall'][1]-s['wall'][0] for s in r['samples']) for r in workers]
            by_arm[arm]=totals
            rows.append(dict(n=n,arm=arm,query44_ms=extent([x/1e6 for x in totals]),
                query_class_ms=[extent([statistics.median([(s['wall'][1]-s['wall'][0])/1e6 for s in r['samples'] if s['query_class']==k]) for r in workers]) for k in range(4)],
                append_ms=extent([statistics.median([(s['wall'][1]-s['wall'][0])/1e6 for s in r['appends']]) for r in workers]),
                index_build_ms=None if arm=='PLAIN' else extent([(r['index_build']['wall'][1]-r['index_build']['wall'][0])/1e6 for r in workers]),
                before_index_bytes=extent([r['seed_bytes'] for r in workers]),after_index_bytes=extent([r['index_bytes'] for r in workers])))
        ratios[str(n)]=extent([x/y for x,y in zip(by_arm['INDEXED'],by_arm['PLAIN'])])
    ok=not a['errors'] and not a['unexpected_errors']
    fast=ok and '32768' in ratios and ratios['32768']['median']<=.5
    return {'semantics':'PASS_QUERY_INDEX_SEMANTICS_SCOPED' if ok else 'HOLD_OR_FAIL',
            'query_time':'PASS_LARGE_HISTORY_QUERY_TIME_SCOPED' if fast else 'HOLD_QUERY_TIME_BENEFIT',
            'performance_workers':len(a['performance']),'contract_cases':sum(len(x['cases']) for x in a['contracts']),
            'timed_queries':sum(len(x['samples']) for x in a['performance']),
            'timed_appends':sum(len(x['appends']) for x in a['performance']),
            'checks':a['checks'],'errors':a['errors'],'unexpected_errors':a['unexpected_errors'],
            'by_size_arm':rows,'paired_total_ratios':ratios,'production_adoption':False}

def audit(directory):
    a=analyze(load(directory))
    freeze=json.loads((ROOT/'FREEZE.json').read_text())
    for n,digest in freeze['sha256'].items():
        if h((ROOT/n).read_bytes())!=digest:a['errors'].append('source freeze:'+n)
    for batch in range(4):
        p=Path(directory)/f'batch-{batch}'
        try:
            start=json.loads((p/'START.json').read_text());end=json.loads((p/'END.json').read_text())
            outer=json.loads(p.with_suffix('.outer.json').read_text())
            if not(type(outer['exit']) is int and outer['exit']==0 and outer['timeout'] is False and
                   outer['stderr_b64']=='' and start['pid']==end['pid']==outer['pid'] and
                   start['sources']==freeze['sha256'] and end['workers']==(2 if batch==3 else 6)):
                a['errors'].append('batch receipt:'+str(batch))
        except Exception as e:a['errors'].append('missing/invalid batch:'+str(batch)+':'+repr(e))
    return summary(a)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--out',type=Path,required=True);v=p.parse_args()
    result=audit(v.directory)
    with v.out.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('semantics','query_time','performance_workers','contract_cases','checks','errors','unexpected_errors')}))
    raise SystemExit(0 if not result['errors'] and not result['unexpected_errors'] else 1)
