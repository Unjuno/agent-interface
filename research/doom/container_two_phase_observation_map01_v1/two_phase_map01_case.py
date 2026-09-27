from __future__ import annotations
import argparse,json,queue,subprocess,sys,threading,time
from pathlib import Path
SRC=Path('/mnt/data/release_real_setup/src')
HERE=SRC/'research/doom'
FIX=HERE/'fixtures/map01-threat-contact-v2/fixture.json'
VENV=Path('/mnt/data/two-phase-map01-venv/bin/python')

def rows(path):
    p=Path(path); return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['baseline','candidate'],required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seed',type=int,required=True);ap.add_argument('--hold-ms',type=int,default=250);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False); runtime=a.out/'runtime'
    script=HERE/'session_map01_v13.py' if a.mode=='baseline' else Path('/mnt/data/session_map01_two_phase_dev_v1.py')
    cmd=[str(VENV),str(script),'--out',str(runtime),'--seed',str(a.seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIX)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    q=queue.Queue(); latest=None
    def reader():
        try:
            for line in p.stdout:
                try:q.put(json.loads(line))
                except Exception:q.put({'event':'nonjson','line':line})
        finally:q.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def send(r):p.stdin.write(json.dumps(r)+'\n');p.stdin.flush()
    def take(timeout=30):
        nonlocal latest
        try:r=q.get(timeout=timeout)
        except queue.Empty:raise TimeoutError('event timeout')
        if r is None:raise RuntimeError('session closed '+p.stderr.read())
        if r.get('event')=='observation':latest=r
        return r
    def wait(pred,timeout=30):
        end=time.monotonic()+timeout
        while True:
            r=take(max(.01,end-time.monotonic()))
            if pred(r):return r
            if time.monotonic()>=end:raise TimeoutError('predicate')
    try:
        wait(lambda r:r.get('event')=='ready'); wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
        send({'op':'clock'});clk=wait(lambda r:r.get('event')=='clock')
        pid=f'two-phase-{a.mode}'
        send({'op':'submit','id':pid,'expected_sequence':latest['sequence'],'valid_until_ns':clk['runtime_ns']+3_000_000_000,
              'steps':[{'op':'hold','keys':['d'],'duration_ms':a.hold_ms}]})
        term=wait(lambda r:r.get('event')=='terminal' and r.get('id')==pid)
        time.sleep(.1);send({'op':'finish'});wait(lambda r:r.get('event')=='post_control_score');p.stdin.close();rc=p.wait(timeout=10)
        if rc:raise RuntimeError('session rc '+str(rc)+' '+p.stderr.read())
    finally:
        if p.poll() is None:p.kill();p.wait()
    ev=rows(runtime/'events.jsonl')
    admissions=[r for r in ev if r.get('event')=='input_admission' and r.get('key')=='d']
    releases=[r for r in ev if r.get('event')=='input_release_transition' and r.get('release_batch_identifier')==pid and r.get('key')=='d']
    if len(admissions)!=1 or len(releases)!=1:raise AssertionError((len(admissions),len(releases)))
    ad,rel=admissions[0],releases[0]
    upper=(rel['release_call_returned_ns']-ad['admitted_ns'])/1e6
    lower=(rel['release_call_started_ns']-ad['input_ack_ns'])/1e6
    boundaries=[r for r in ev if r.get('event')=='two_phase_observation_boundary' and r.get('id')==pid]
    obs=[r for r in ev if r.get('event')=='observation' and r.get('id')==pid]
    # closest observation artifact before normal release (baseline) or any split evidence (candidate)
    prev=[o for o in obs if isinstance(o.get('artifact_ready_ns'),int) and o['artifact_ready_ns']<=rel['release_call_started_ns']]
    nearest=max(prev,key=lambda o:o['artifact_ready_ns']) if prev else None
    score=json.loads((runtime/'score.json').read_text())
    scorer=json.loads((runtime/'scorer-summary.json').read_text())
    leak=sum(1 for r in ev if isinstance(r.get('schema'),str) and r['schema'].startswith('independent-progress-'))
    summary={'mode':a.mode,'seed':a.seed,'hold_ms':a.hold_ms,'terminal_status':term.get('status'),'retained_lower_ms':lower,'retained_upper_ms':upper,
             'release_verified':rel.get('owner_transition_verified'),'two_phase_boundary_count':len(boundaries),
             'two_phase_release_before_artifact_all':bool(boundaries) and all(r.get('release_before_artifact') for r in boundaries),
             'nearest_pre_release_artifact_gap_ms':None if nearest is None else (rel['release_call_started_ns']-nearest['artifact_ready_ns'])/1e6,
             'nearest_pre_release_capture_to_release_ms':None if nearest is None else (rel['release_call_started_ns']-nearest['capture_ns'])/1e6,
             'scorer_missed_sample_periods':(scorer.get('scheduler') or {}).get('missed_sample_periods'),'controller_scorer_leak_count':leak,
             'score':{k:score.get(k) for k in ('health','kill_count','death_count','map_exit','episode_finished','player_dead')}}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
