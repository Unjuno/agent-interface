"""Read-only reconstruction from raw event/clock/process evidence; imports no probe/runner."""
from pathlib import Path
import hashlib,json,statistics,sys

def check(ok,why):
    if not ok: raise ValueError(why)
def integer(v): return type(v) is int and v>=0
def key(m,code):
    check(type(m) is str and len(m)==64 and all(c in '0123456789abcdef' for c in m),'keymap encoding')
    return (bytes.fromhex(m)[code//8]>>(code%8))&1

def reduce_events(events,window,code):
    value=None; focused=False; awaiting=False
    for e in events:
        check(type(e['type']) is int and type(e['synthetic']) is int and e['synthetic']==0,'event type/source')
        t=e['type']
        if t==9 or t==10:
            check(e['window']==window and type(e['mode']) is int and e['mode']==0,'focus source/mode')
            focused=t==9;awaiting=focused;value=None
        elif t==11:
            check(awaiting and focused,'unpaired snapshot')
            value=key(e['map'],code);awaiting=False
        elif t in (2,3):
            check(e['window']==window and integer(e['code']),'key source')
            check(focused and not awaiting and value is not None,'key without basis')
            if e['code']==code:value=int(t==2)
        else:raise ValueError('unknown event')
    check(focused and not awaiting and value is not None,'unknown final basis')
    return value

def audit_block(rows,receipt,rep,scenario,arm,n):
    check(len(rows)==n+4,'sample denominator')
    start,end=rows[0],rows[-1]
    check(start['kind']=='start' and end['kind']=='end','endpoints')
    for k,v in [('rep',rep),('scenario',scenario),('arm',arm),('returncode',0)]:
        check(type(receipt[k]) is int and receipt[k]==v,'process '+k)
    check(start['pid']==receipt['pid'] and integer(start['pid']),'pid')
    check(start['arm']==arm and start['scenario']==scenario and start['samples']==n and start['warmup']==2,'native plan')
    check(integer(receipt['before_ns']) and receipt['before_ns']<receipt['after_ns'],'process clocks')
    check(end['final_keymap']=='00'*32 and end['pointer_mask']==0,'neutral cleanup')
    check(len(receipt['argv'])==6 and Path(receipt['argv'][0]).name=='probe' and receipt['argv'][2:]==list(map(str,[arm,scenario,n,2])),'argv')
    durations=[];cpus=[];requests=0
    for i,r in enumerate(rows[1:-1],-2):
        check(type(r['index']) is int and r['index']==i and r['kind']=='sample','sample index')
        clocks=[r[k] for k in ('oracle_before_begin','oracle_before_end','before_ns','after_ns','oracle_after_begin','oracle_after_end')]
        check(all(integer(x) for x in clocks) and clocks==sorted(clocks),'clock order')
        check(receipt['before_ns']<=clocks[0]<=clocks[-1]<=receipt['after_ns'],'clock envelope')
        check(r['after_ns']>r['before_ns'] and integer(r['cpu_before_ns']) and r['cpu_after_ns']>=r['cpu_before_ns'],'positive time')
        check(all(integer(r[k]) for k in ('request_before','request_after','processed')),'serial type')
        delta=r['request_after']-r['request_before']
        check(delta==(2 if arm==2 else 1) and r['processed']==r['request_after']-1,'request/reply accounting')
        code=start['code'];check(type(code) is int and 8<=code<=255,'keycode')
        before=key(r['pre'],code);after=key(r['post'],code)
        check(r['pre']==r['post'] and before==int(scenario in (1,2)),'oracle state')
        check(reduce_events(r['bootstrap'],start['window'],code)==0,'seed')
        reconstructed=reduce_events(r['bootstrap']+r['events'],start['window'],code)
        check(reconstructed==before==after,'event/oracle agreement')
        check([e['type'] for e in r['events']]==[[],[2],[10,9,11],[10,9,11,3]][scenario],'exposure shape')
        for k in ('known','focus','down','decision'):check(type(r[k]) is int,'decision type')
        check(r['known']==1 and r['focus']==1 and r['down']==reconstructed and r['decision']==before,'decision')
        if arm:check(key(r['query'],code)==before and r['query']==r['pre'],'queried state')
        else:check(r['query']=='00'*32,'no query output')
        if i>=0:
            durations.append(r['after_ns']-r['before_ns']);cpus.append(r['cpu_after_ns']-r['cpu_before_ns']);requests+=delta
    return dict(rep=rep,scenario=scenario,arm=arm,samples=n,request_count=requests,median_ns=statistics.median(durations),min_ns=min(durations),max_ns=max(durations),cpu_median_ns=statistics.median(cpus))

def audit(root,reps,n):
    summaries=[]
    for rep in reps:
        batch=root/f'batch{rep}';complete=json.loads((batch/'COMPLETE.json').read_text());server=json.loads((batch/'SERVER.json').read_text())
        check(complete['rep']==rep and complete['samples']==n and len(complete['blocks'])==12,'batch identity')
        check(server['returncode']==0 and server['socket_removed'] is True and server['auth_removed'] is True,'server cleanup')
        check(type(server['pid']) is int and server['before_ns']<server['after_ns'],'server identity')
        for idx,r in enumerate(complete['blocks']):
            s=idx//3;arm=(idx%3+rep+s)%3;stem=f'{s}-{arm}';raw=(batch/(stem+'.jsonl')).read_bytes();err=(batch/(stem+'.stderr')).read_bytes()
            check(not err and hashlib.sha256(raw).hexdigest()==r['stdout_sha256'] and hashlib.sha256(err).hexdigest()==r['stderr_sha256'],'process bytes')
            check(json.loads((batch/(stem+'.process.json')).read_text())==r,'receipt copy')
            check(server['before_ns']<=r['before_ns']<r['after_ns']<=server['after_ns'],'server envelope')
            summaries.append(audit_block([json.loads(x) for x in raw.splitlines()],r,rep,s,arm,n))
    pairs=[]
    for rep in reps:
        for s in range(4):
            a={x['arm']:x['median_ns'] for x in summaries if x['rep']==rep and x['scenario']==s}
            pairs.append(dict(rep=rep,scenario=s,event_query=a[0]/a[1],query_double=a[1]/a[2]))
    eq=statistics.median(x['event_query'] for x in pairs);qd=statistics.median(x['query_double'] for x in pairs)
    return dict(accounting='PASS_SYNC_REQUEST_ACCOUNTING_SCOPED',blocks=len(summaries),timed_samples=len(summaries)*n,warmups=len(summaries)*2,event_query_ratio=eq,query_double_ratio=qd,event_latency='PASS_EVENT_LATENCY_SCOPED' if eq<=.8 else 'HOLD_EVENT_LATENCY_BENEFIT_NOT_ESTABLISHED',redundant_sync='PASS_REDUNDANT_SYNC_REMOVAL_SCOPED' if qd<=.8 else 'HOLD_REDUNDANT_SYNC_BENEFIT_NOT_ESTABLISHED',summaries=summaries,paired_ratios=pairs)
if __name__=='__main__':
    try: print(json.dumps(audit(Path(sys.argv[1]),range(int(sys.argv[2])),int(sys.argv[3])),sort_keys=True,indent=2))
    except (ValueError,KeyError,TypeError,OSError) as e:print(json.dumps({'status':'HOLD_AUDIT','error':str(e)}));sys.exit(1)
