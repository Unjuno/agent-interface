"""Independent raw-only checker. Does not import actors, bundle, native or policy."""
from pathlib import Path
import hashlib,json,statistics,sys
CONTEXTS=('UP','DOWN','EDGE_BURST','FOCUS_RETURN')
MODES=('FOCUS_QUERY','FOCUS_SYNC','FOCUS_PIGGYBACK')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def strictint(v):return type(v) is int

def evaluate(root,formal=True,source_root=None):
    root=Path(root);errors=[];checks=0;records=0;requests={m:0 for m in MODES};ratios=[];cells={};first={};blocks=0
    def ck(ok,why):
        nonlocal checks
        checks+=1
        if not ok:errors.append(why)
    def bit(h,c):return bool(bytes.fromhex(h)[c//8]&(1<<(c%8)))
    def state(s,down):
        d=s['decision'];ck(d==dict(status='WAIT' if down else 'TYPE',shift_down=down,authority='none',input_dispatched=False),'state decision')
        ck(type(d['shift_down']) is bool and d['input_dispatched'] is False,'decision exact types')
    def acq(s):
        ck(all(strictint(s[k]) for k in ('next_before','next_after','processed_before','processed_after','query_calls','sync_calls','native_errors')),'acquisition integer fields')
        ck(s['wall_before_ns']<=s['native_before_ns']<=s['native_after_ns']<=s['wall_after_ns'],'acquisition clocks')
        ck(s['cpu_before_ns']<=s['cpu_after_ns'],'acquisition cpu clocks')
        ck(s['native_errors']==0,'native errors')
        ck(s['next_after']-s['next_before']==s['query_calls']+s['sync_calls'],'acquisition requests')
        if s['query_calls']+s['sync_calls']:ck(s['processed_after']>=s['next_after']-1,'reply processed')
    def replay(events,code,target,seed,start):
        down=bit(seed,code);focused=True;known=True;waiting=False
        for i,e in enumerate(events):
            ck(strictint(e['ordinal']) and e['ordinal']==start+i,'event sequence')
            ck(e['send_event'] is False,'native rather than synthetic send_event')
            t=e['type'];ck(strictint(t) and t in (2,3,9,10,11),'event type')
            if t in (2,3):
                ck(e['window']==target and strictint(e['keycode']),'event target/code')
                if e['keycode']==code:down=t==2
                if waiting:known=False;waiting=False
            elif t in (9,10):
                ck(e['window']==target and e['mode']==0,'normal focus event')
                known=False;focused=t==9;waiting=focused
            else:
                ck(waiting and focused and len(e['keymap'])==64,'keymap association')
                down=bit(e['keymap'],code);known=True;waiting=False
        ck(known and focused and not waiting,'reconstructed known state')
        return down
    if formal and source_root is not None:
        source=Path(source_root);freeze=json.loads((source/'FREEZE.json').read_bytes())
        for n,h in freeze['files'].items():ck(digest(source/n)==h,'source hash '+n)
    for ci,context in enumerate(CONTEXTS):
        batch=root/context
        if not batch.exists():ck(False,'missing context '+context);continue
        start=json.loads((batch/'START.json').read_bytes());end=json.loads((batch/'END.json').read_bytes());server=json.loads((batch/'server.json').read_bytes())
        ck(start['context']==context and start['formal'] is formal and start['affinity']==[0],'batch identity')
        ck(start['pid']==end['pid'] and start['start_ns']<=end['end_ns'],'batch lifetime')
        ck(end['failure'] is None and end['cleanup_errors']==[] and end['completed']==(3 if formal else 1),'batch completion')
        ck(server['returncode']==0 and type(server['returncode']) is int and server['socket_absent'] is True and server['auth_removed'] is True,'server cleanup')
        ck('-nolisten' in server['argv'] and 'tcp' in server['argv'] and '-auth' in server['argv'],'private server')
        outer=json.loads((root/(context+'.process.json')).read_bytes())
        ck(outer['returncode']==0 and strictint(outer['returncode']) and outer.get('timeout') is False,'outer exit')
        ck(not (root/(context+'.stderr')).read_bytes(),'runner stderr')
        wires={}
        for role in ('writer','witness'):
            p=json.loads((batch/(role+'.process.json')).read_bytes())
            ck(type(p['returncode']) is int and p['returncode']==0 and p['error'] is None,'actor exit '+role)
            ck(not (batch/(role+'.stderr')).read_bytes(),'actor stderr')
            log=[json.loads(x) for x in (batch/(role+'.wire.jsonl')).read_text().splitlines()]
            ck(log[0]['direction']=='out' and json.loads(log[0]['text'])['pid']==p['pid'],'actor ready')
            ins=[json.loads(x['text']) for x in log if x['direction']=='in'];outs=[json.loads(x['text']) for x in log if x['direction']=='out'][1:]
            ck(len(ins)==len(outs),'IPC length')
            for i,(a,b) in enumerate(zip(ins,outs)):
                ck(a['id']==b['id']==i+1 and a['op']==b['op'] and b['before_ns']<=b['after_ns'],'IPC correlation')
            wires[role]={a['id']:(a,b) for a,b in zip(ins,outs)}
        names=sorted(batch.glob('block-*.json'));ck(len(names)==(3 if formal else 1),'block denominator')
        cells[context]={m:[] for m in MODES};first[context]={m:[] for m in MODES}
        for index,path in enumerate(names):
            r=json.loads(path.read_bytes());blocks+=1;code=r['code'];target=r['target']
            ck(r['context']==context and r['index']==index and r['epoch']==context+'-'+str(index),'block identity')
            ck(strictint(code) and 8<=code<=255 and strictint(target),'key and target types')
            ck(r['seed']=='00'*32 and r['fresh']['result']['target']==target,'neutral seed')
            for key in ('fresh','mutation','release'):
                ck(wires['writer'][r[key]['id']][1]==r[key],'writer bytes '+key)
            for key in ('before','after','neutral'):
                ck(wires['witness'][r[key]['id']][1]==r[key],'witness bytes '+key)
            ops=r['mutation']['result']['operations'];d=False;f=target
            expected=[('edge',True)] if context=='DOWN' else []
            if context=='EDGE_BURST':expected=[('edge',bool(1-i%2)) for i in range(17)]
            if context=='FOCUS_RETURN':expected=[('focus',r['fresh']['result']['away']),('edge',True),('focus',target)]
            actual=[(o['kind'],o['down'] if o['kind']=='edge' else o['window']) for o in ops]
            ck(actual==expected,'writer schedule')
            for o in ops:
                ck(o['before_ns']<=o['after_ns'],'writer clock')
                if o['kind']=='edge':ck(type(o['down']) is bool and o['keycode']==code,'writer edge');d=o['down']
                else:f=o['window']
            ck(f==target,'final writer focus')
            for key in ('before','after'):
                w=r[key]['result'];ck(bit(w['keymap'],code)==d and w['focus']==target and w['pointer_mask']&0x1f00==0,'witness state')
            ck(r['before']['result']['keymap']==r['after']['result']['keymap'],'quiescent endpoint bytes')
            w=r['neutral']['result'];ck(w['keymap']=='00'*32 and w['pointer_mask']&0x1f00==0,'neutral cleanup')
            for s in [r['other_local'],r['other_sync']]:acq(s)
            ck(r['other_reply']['r1']-r['other_reply']['r0']==1,'other connection request')
            ck(r['other_local']['events']==[] and r['other_local']['next_after']==r['other_local']['next_before'],'other connection local-only')
            state(r['other_local'],False);state(r['other_sync'],d)
            hist={m:[] for m in MODES};origin={}
            for arm,m in enumerate(MODES):
                b=r['bootstrap'][arm];origin[m]=b['events'][-1]['ordinal']+1 if b['events'] else 0
            ck(len(r['samples'])==(51 if formal else 12),'sample denominator')
            for ix,s in enumerate(r['samples']):
                records+=1;j=ix//3;order=ix%3;m=MODES[(order+j+index)%3]
                ck(s['mode']==m and s['sample']==j and s['arm_order']==order,'sample order')
                ck(s['authority']=='none' and s['task_success'] is None,'neutral output')
                a=s['state'];f=s['focus'];acq(a)
                ck(all(strictint(f[k]) for k in f),'focus exact integer fields')
                ck(f['errors']==0 and f['focus']==target and f['r1']-f['r0']==1 and f['p1']>=f['r1']-1,'focus reply')
                ck(a['next_before']==f['r1'],'same connection request chain')
                ck(r['before']['after_ns']<=s['start_ns']<=f['t0']<=f['t1']<=a['wall_before_ns']<=a['wall_after_ns']<=s['end_ns']<=r['after']['before_ns'],'bundle clock')
                ck(s['cpu0']<=s['cpu1'],'bundle cpu')
                req=f['r1']-f['r0']+a['next_after']-a['next_before']
                ck(req==(1 if m=='FOCUS_PIGGYBACK' else 2),'bundle request count')
                ck(a['query_calls']==(1 if m=='FOCUS_QUERY' else 0) and a['sync_calls']==(1 if m=='FOCUS_SYNC' else 0),'method calls')
                if m=='FOCUS_QUERY':ck(bit(a['keymap'],code)==d,'query actual keymap');ck(a['events']==[],'query no event drain')
                else:
                    hist[m].extend(a['events']);ck(replay(hist[m],code,target,r['seed'],origin[m])==d,'event-derived state')
                    ck(a['history_count']==len(hist[m]),'retained history size')
                state(a,d)
                if j>=3:requests[m]+=req
            times={m:[s['end_ns']-s['start_ns'] for s in r['samples'] if s['mode']==m and s['sample']>=3] for m in MODES}
            ck(all(times.values()),'missing measured arm')
            if not all(times.values()):continue
            block_medians={m:statistics.median(v) for m,v in times.items()}
            ratio=block_medians['FOCUS_PIGGYBACK']/block_medians['FOCUS_QUERY'];ratios.append(ratio)
            for m in MODES:
                cells[context][m].append(block_medians[m]);first[context][m].extend(s['end_ns']-s['start_ns'] for s in r['samples'] if s['mode']==m and s['sample']==0)
    summaries={c:{m:{'median_ns':statistics.median(v),'min_ns':min(v),'max_ns':max(v)} for m,v in modes.items() if v} for c,modes in cells.items()}
    per={c:statistics.median([a/b for a,b in zip(cells[c]['FOCUS_PIGGYBACK'],cells[c]['FOCUS_QUERY'])]) for c in cells if cells[c]['FOCUS_QUERY']}
    speed=bool(ratios) and statistics.median(ratios)<=.8 and all(x<=.8 for x in per.values())
    return dict(status='PASS_FOCUS_REPLY_PIGGYBACK_CONTRACT' if not errors else 'FAIL_RAW_AUDIT',errors=errors,checks=checks,blocks=blocks,acquisitions=records,primary_requests=requests,
                paired_median_ratio=statistics.median(ratios) if ratios else None,per_context_ratios=per,block_medians=summaries,first_ns=first,
                speed_status=('PASS_FOCUS_STATE_LOCAL_COST' if speed else 'HOLD_NO_20_PERCENT_BUNDLE_GAIN') if not errors else 'UNEVALUATED')

if __name__=='__main__':
    try:
        ans=evaluate(sys.argv[1],len(sys.argv)<3 or sys.argv[2]!='construct',Path(__file__).resolve().parent)
    except Exception as e:
        ans=dict(status='STOP_AUDITOR_INPUT',errors=[type(e).__name__+': '+str(e)])
    print(json.dumps(ans,sort_keys=True,indent=2));sys.exit(bool(ans['errors']))
