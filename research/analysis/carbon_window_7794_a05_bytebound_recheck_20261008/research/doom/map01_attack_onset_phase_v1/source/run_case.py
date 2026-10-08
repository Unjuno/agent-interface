from __future__ import annotations
import argparse,json,os,queue,subprocess,sys,threading,time,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load_jsonl(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run_case(source,v12,out,arm,case_id,seed=992600):
    source=Path(source).resolve();v12=Path(v12).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=False);runtime=out/'runtime'
    if arm not in ('IMMEDIATE','ONE_WINDOW_PREROLL'):raise ValueError(arm)
    pre_roll_ms=0 if arm=='IMMEDIATE' else 600
    env=dict(os.environ);env['MAP01_SOURCE_ROOT']=str(source);env['MAP01_V12_ROOT']=str(v12)
    cmd=[sys.executable,str(HERE/'session_entry.py'),'--out',str(runtime),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(source/'research/doom/fixtures/map01-threat-contact-v2/fixture.json')]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=env)
    q=queue.Queue();seen=[];latest=None;markers={}
    def reader():
        try:
            for line in p.stdout:
                try:q.put(json.loads(line))
                except Exception:q.put({'event':'nonjson_stdout','line':line.rstrip()})
        finally:q.put(None)
    t=threading.Thread(target=reader,daemon=True);t.start()
    def wait(pred,timeout=40):
        nonlocal latest
        end=time.monotonic()+timeout
        while True:
            remain=end-time.monotonic()
            if remain<=0:raise TimeoutError('event timeout')
            row=q.get(timeout=remain)
            if row is None:raise RuntimeError('stdout closed: '+p.stderr.read())
            seen.append(row)
            if row.get('event')=='observation':latest=row
            if pred(row):return row
    def send(row):p.stdin.write(json.dumps(row)+'\n');p.stdin.flush()
    failure=None
    try:
        ready=wait(lambda r:r.get('event')=='ready');initial=wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
        markers['ready_seen_ns']=time.perf_counter_ns();markers['initial_sequence']=initial.get('sequence');markers['initial_capture_ns']=initial.get('capture_ns')
        markers['pre_roll_started_ns']=time.perf_counter_ns()
        if pre_roll_ms:time.sleep(pre_roll_ms/1000)
        markers['pre_roll_finished_ns']=time.perf_counter_ns()
        send({'op':'clock'});clock=wait(lambda r:r.get('event')=='clock');markers['clock_runtime_ns']=clock.get('runtime_ns')
        markers['submit_sent_ns']=time.perf_counter_ns()
        send({'op':'submit','id':case_id,'expected_sequence':latest['sequence'],'valid_until_ns':clock['runtime_ns']+5_000_000_000,'steps':[{'op':'hold','keys':['space'],'duration_ms':600},{'op':'observe'}]})
        terminal=wait(lambda r:r.get('event')=='terminal' and r.get('id')==case_id)
        if terminal.get('status')!='completed':raise RuntimeError('program not completed '+repr(terminal))
        markers['terminal_seen_ns']=time.perf_counter_ns()
        time.sleep(.15);send({'op':'finish'});score=wait(lambda r:r.get('event')=='post_control_score');markers['finish_score_seen_ns']=time.perf_counter_ns();p.stdin.close();rc=p.wait(timeout=20)
        if rc:raise RuntimeError('session rc='+str(rc)+' stderr='+p.stderr.read())
    except BaseException as exc:
        failure=repr(exc);raise
    finally:
        if p.poll() is None:p.kill();p.wait()
        t.join(timeout=2)
        out.joinpath('controller_events.json').write_text(json.dumps(seen,indent=2)+'\n')
        out.joinpath('launch.json').write_text(json.dumps({'cmd':cmd,'arm':arm,'pre_roll_ms':pre_roll_ms,'seed':seed,'case_id':case_id,'markers':markers,'failure':failure},indent=2)+'\n')
    return runtime

def derive(runtime,arm,case_id):
    runtime=Path(runtime);events=load_jsonl(runtime/'events.jsonl');samples=load_jsonl(runtime/'scorer-samples.jsonl')
    launch=json.loads((runtime.parent/'launch.json').read_text())
    downs=[];ups=[]
    for r in events:
        if r.get('event')=='input_admission':
            m=r.get('physical_key_measurement');e=m.get('adapter_edge') if isinstance(m,dict) else None
            if isinstance(e,dict) and e.get('key')=='space':downs.append(e)
        if r.get('event')=='input_release_transition' and r.get('key')=='space':
            m=r.get('physical_key_measurement');e=m.get('adapter_edge') if isinstance(m,dict) else None
            if isinstance(e,dict):ups.append((r,e))
    positives=[];prev=None
    for row in samples:
        s=row.get('payload',{})
        if prev is not None:
            if s.get('kill_count',0)>prev.get('kill_count',0):positives.append({'kind':'KILL_COUNT_INCREASE','observed_ns':s['sample_ns'],'before':prev['kill_count'],'after':s['kill_count'],'authority':False})
            if s.get('map_exit') and not prev.get('map_exit'):positives.append({'kind':'MAP_EXIT','observed_ns':s['sample_ns'],'authority':False})
        prev=s
    physical=None
    if len(downs)==1 and len(ups)==1:
        rr,u=ups[0];d=downs[0]
        physical={'down':d,'up':u,'release':rr,'lineage_ok':all(d.get(k)==u.get(k) for k in ('actuation_id','owner_id','intent_token','key')) and all(d.get(k)==rr.get(k) for k in ('owner_id','intent_token','key')),'confirmed':d.get('status')=='CONFIRMED_PHYSICAL_DOWN' and u.get('status')=='CONFIRMED_PHYSICAL_UP'}
    bound=[]
    if physical and physical['confirmed'] and physical['lineage_ok']:
        down_hi=physical['down']['interval'][1]
        for e in positives:
            if e['observed_ns']>=down_hi:bound.append({**e,'plan_id':case_id,'actuation_id':physical['down']['actuation_id'],'scorer_authority':False})
    score=json.loads((runtime/'score.json').read_text()) if (runtime/'score.json').exists() else None
    payloads=[r.get('payload',{}) for r in samples if isinstance(r.get('payload'),dict)]
    baseline=payloads[0] if payloads else None
    down_hi=physical['down']['interval'][1] if physical else None
    pre_attack=[s for s in payloads if type(s.get('sample_ns')) is int and type(down_hi) is int and s['sample_ns']<down_hi]
    admission_sample=pre_attack[-1] if pre_attack else baseline
    return {'arm':arm,'pre_roll_ms':launch['pre_roll_ms'],'case_id':case_id,'seed':launch['seed'],'physical_down_count':len(downs),'physical_up_count':len(ups),'physical':physical,'positive_events':positives,'bound_task_effects':bound,'scorer_samples':len(samples),'scorer_baseline':baseline,'scorer_pre_attack_last':admission_sample,'score':score,'markers':launch.get('markers',{}),'runtime_sources_sha256':sha(runtime/'sources.json')}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--v12',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--arm',required=True);ap.add_argument('--case-id',required=True);ap.add_argument('--seed',type=int,default=992600);a=ap.parse_args()
    rt=run_case(a.source,a.v12,a.out,a.arm,a.case_id,a.seed);d=derive(rt,a.arm,a.case_id);a.out.joinpath('DERIVED.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps(d,sort_keys=True,default=str))
