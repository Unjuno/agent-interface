from __future__ import annotations
import argparse, json, queue, subprocess, sys, threading, time
from pathlib import Path


def rows(path):
    p=Path(path)
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()] if p.exists() else []


def direct_bounds(events, program_id):
    admissions=[r for r in events if r.get('event')=='input_admission' and r.get('id')==program_id]
    releases=[r for r in events if r.get('event')=='input_release_transition' and r.get('release_batch_identifier')==program_id]
    if not admissions:
        return {'measurement_ready': True, 'hold_count': 0, 'retained_lower_ms': 0.0, 'retained_upper_ms': 0.0}
    by={(r.get('intent_token'),r.get('key')):r for r in releases if r.get('owner_transition_verified') is True}
    lower=upper=0
    for a in admissions:
        rel=by.get((a.get('intent_token'),a.get('key')))
        if rel is None: raise AssertionError('unmatched admission')
        start=a['input_ack_ns']
        lower += max(0, rel['release_call_started_ns']-start)
        upper += max(0, rel['release_call_returned_ns']-a['admitted_ns'])
    return {'measurement_ready': True, 'hold_count':len(admissions),
            'retained_lower_ms': lower/1e6, 'retained_upper_ms': upper/1e6}


def summarize(root, program_id, wait_ms):
    runtime=Path(root)/'runtime'; events=rows(runtime/'events.jsonl'); score=json.loads((runtime/'score.json').read_text())
    direct=direct_bounds(events,program_id)
    no_input_lower=max(0.0,wait_ms-direct['retained_upper_ms'])
    no_input_upper=max(0.0,wait_ms-direct['retained_lower_ms'])
    terminals=[r for r in events if r.get('event')=='terminal' and r.get('id')==program_id]
    releases=[(r.get('release') or {}) for r in terminals]
    scorer_summary=json.loads((runtime/'scorer-summary.json').read_text())
    leak=sum(1 for r in events if isinstance(r.get('schema'),str) and r['schema'].startswith('independent-progress-'))
    return {'program_id':program_id,'direct':direct,'wait_ms':wait_ms,
            'no_retained_input_lower_ms':no_input_lower,'no_retained_input_upper_ms':no_input_upper,
            'terminal_status':terminals[-1]['status'] if terminals else None,
            'terminal_release_empty': bool(releases and releases[-1].get('verified') is True and releases[-1].get('keys_down')==[] and releases[-1].get('buttons_down',[])==[]),
            'scorer_missed_sample_periods':(scorer_summary.get('scheduler') or {}).get('missed_sample_periods'),
            'controller_scorer_leak_count':leak,
            'score':{k:score[k] for k in ('map_exit','episode_finished','player_dead','death_count','kill_count')}}


def run_arm(here,out,seed,mode,wait_ms,recovery_ms,health_loss):
    out.mkdir(parents=True,exist_ok=False); runtime=out/'runtime'
    p=subprocess.Popen([sys.executable,str(here/'session_map01_v13.py'),'--out',str(runtime),'--seed',str(seed),'--timeout-seconds','60','--skill','1'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    q=queue.Queue(); latest=None; source_health=None; cancelled=False
    def reader():
        try:
            for line in p.stdout:q.put(json.loads(line))
        finally:q.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def send(row): p.stdin.write(json.dumps(row)+'\n'); p.stdin.flush()
    def take(timeout=25):
        nonlocal latest,source_health,cancelled
        try:r=q.get(timeout=timeout)
        except queue.Empty:raise TimeoutError('event timeout')
        if r is None:raise RuntimeError('session closed '+p.stderr.read())
        if r.get('event')=='observation':latest=r
        if r.get('event')=='typed_observation':
            sig=(r.get('signals') or {}).get('health') or {}
            if source_health is None and sig.get('status')=='observed': source_health=sig.get('value')
            if mode=='recovery' and not cancelled and source_health is not None and sig.get('status')=='observed' and sig.get('value') < source_health-health_loss:
                send({'op':'cancel','id':'wait-recovery'});cancelled=True
        return r
    def wait(pred,timeout=25):
        end=time.monotonic()+timeout
        while True:
            r=take(max(.01,end-time.monotonic()))
            if pred(r):return r
            if time.monotonic()>=end:raise TimeoutError('predicate timeout')
    try:
        wait(lambda r:r.get('event')=='ready');wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
        if source_health is None: raise RuntimeError('typed source health missing')
        send({'op':'clock'}); clk=wait(lambda r:r.get('event')=='clock')
        if mode=='coast':
            pid='wait-coast';steps=[{'op':'coast','duration_ms':wait_ms,'sample_ms':50}]
        else:
            pid='wait-recovery';coast=max(1,wait_ms-recovery_ms);steps=[{'op':'hold','keys':['a'],'duration_ms':recovery_ms},{'op':'coast','duration_ms':coast,'sample_ms':50}]
        send({'op':'submit','id':pid,'expected_sequence':latest['sequence'],'valid_until_ns':clk['runtime_ns']+1_500_000_000,'steps':steps})
        term=wait(lambda r:r.get('event')=='terminal' and r.get('id')==pid)
        if term.get('status') not in ('completed','cancelled'):raise RuntimeError('bad terminal '+repr(term))
        time.sleep(.12);send({'op':'finish'});wait(lambda r:r.get('event')=='post_control_score');p.stdin.close();rc=p.wait(timeout=10)
        if rc:raise RuntimeError('session rc '+str(rc)+' '+p.stderr.read())
    finally:
        if p.poll() is None:p.kill();p.wait()
    value=summarize(out,pid,wait_ms);value.update(mode=mode,source_health=source_health,guard_max_health_loss=health_loss,guard_cancelled=cancelled)
    (out/'summary.json').write_text(json.dumps(value,indent=2)+'\n')
    return value


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seed',type=int,default=990615);ap.add_argument('--wait-ms',type=int,default=600);ap.add_argument('--recovery-ms',type=int,default=240);ap.add_argument('--health-loss',type=int,default=8);a=ap.parse_args()
    here=a.repo/'research/doom';a.out.mkdir(parents=True,exist_ok=False)
    arms=[run_arm(here,a.out/'coast',a.seed,'coast',a.wait_ms,a.recovery_ms,a.health_loss),run_arm(here,a.out/'recovery',a.seed,'recovery',a.wait_ms,a.recovery_ms,a.health_loss)]
    c,r=arms
    result={'schema':'map01-recovery-mechanics-development-v1','seed':a.seed,'arms':arms,
      'coast_input_admissions_zero':c['direct']['hold_count']==0,
      'recovery_input_exposed':r['direct']['hold_count']>=1,
      'recovery_reduces_no_input_upper':r['no_retained_input_upper_ms']<c['no_retained_input_upper_ms'],
      'hard_safety_pass':all(x['terminal_release_empty'] and x['scorer_missed_sample_periods']==0 and x['controller_scorer_leak_count']==0 for x in arms),
      'scientific_efficacy_claim':False}
    (a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    if not all((result['hard_safety_pass'],result['coast_input_admissions_zero'],result['recovery_input_exposed'],result['recovery_reduces_no_input_upper'])):raise SystemExit(1)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
