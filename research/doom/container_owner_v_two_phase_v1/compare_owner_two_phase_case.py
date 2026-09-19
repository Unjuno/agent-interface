from __future__ import annotations
import argparse,json,queue,subprocess,threading,time
from pathlib import Path
SRC=Path('/mnt/data/release_real_setup/src'); DOOM=SRC/'research/doom'; FIX=DOOM/'fixtures/map01-threat-contact-v2/fixture.json'; PY=Path('/mnt/data/two-phase-map01-venv/bin/python'); CAND=Path('/mnt/data/session_map01_two_phase_dev_v1.py')

def rows(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['owner_deadline','two_phase'],required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seed',type=int,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);runtime=a.out/'runtime'
 script=DOOM/'session_map01_v13.py' if a.mode=='owner_deadline' else CAND
 cmd=[str(PY),str(script),'--out',str(runtime),'--seed',str(a.seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIX)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1);q=queue.Queue();latest=None
 def rd():
  try:
   for line in p.stdout:
    try:q.put(json.loads(line))
    except:q.put({'event':'nonjson','line':line})
  finally:q.put(None)
 threading.Thread(target=rd,daemon=True).start()
 def send(x): p.stdin.write(json.dumps(x)+'\n');p.stdin.flush()
 def take(timeout=30):
  nonlocal latest
  r=q.get(timeout=timeout)
  if r is None: raise RuntimeError('closed '+p.stderr.read())
  if r.get('event')=='observation':latest=r
  return r
 def wait(pred,timeout=30):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   r=take(max(.01,end-time.monotonic()))
   if pred(r):return r
  raise TimeoutError('predicate')
 try:
  wait(lambda r:r.get('event')=='ready');wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
  send({'op':'clock'});clk=wait(lambda r:r.get('event')=='clock');pid=f'owner-v-two-phase-{a.mode}'
  if a.mode=='owner_deadline':
   valid=clk['runtime_ns']+50_000_000; steps=[{'op':'hold','keys':['d'],'duration_ms':2000}]
  else:
   valid=clk['runtime_ns']+3_000_000_000; steps=[{'op':'hold','keys':['d'],'duration_ms':50}]
  send({'op':'submit','id':pid,'expected_sequence':latest['sequence'],'valid_until_ns':valid,'steps':steps})
  term=wait(lambda r:r.get('event')=='terminal' and r.get('id')==pid)
  time.sleep(.1);send({'op':'finish'});wait(lambda r:r.get('event')=='post_control_score');p.stdin.close();rc=p.wait(timeout=10)
  if rc: raise RuntimeError('session rc '+str(rc)+' '+p.stderr.read())
 finally:
  if p.poll() is None:p.kill();p.wait()
 ev=rows(runtime/'events.jsonl');ad=next(r for r in ev if r.get('event')=='input_admission' and r.get('key')=='d');ack=ad['input_ack_ns']
 obs=[r for r in ev if r.get('event')=='observation' and r.get('id')==pid and isinstance(r.get('artifact_ready_ns'),int)]
 typed=[r for r in ev if r.get('event')=='typed_observation' and r.get('id')==pid and isinstance(r.get('emit_ns'),int)]
 if a.mode=='owner_deadline':
  intr=(term.get('interruption') or {}).get('record') or {}
  if intr.get('reason')!='expired': raise AssertionError(('owner reason',intr))
  empty=intr['verified_ns']; release_verified=intr.get('verified') is True; deadline_to_empty=(empty-intr['valid_until_ns'])/1e6
 else:
  rel=next(r for r in ev if r.get('event')=='input_release_transition' and r.get('release_batch_identifier')==pid and r.get('key')=='d')
  empty=rel['release_call_returned_ns']; release_verified=rel.get('owner_transition_verified') is True; deadline_to_empty=None
 first_art=min(r['artifact_ready_ns'] for r in obs); first_typed=min(r['emit_ns'] for r in typed)
 crossing=[r for r in obs if r['capture_ns']<=empty<=r['artifact_ready_ns']]
 summary={'mode':a.mode,'seed':a.seed,'terminal_status':term['status'],'release_verified':release_verified,
  'ack_to_empty_ms':(empty-ack)/1e6,'ack_to_first_full_artifact_ms':(first_art-ack)/1e6,'ack_to_first_typed_emit_ms':(first_typed-ack)/1e6,'ack_to_terminal_ms':(term['terminal_ns']-ack)/1e6,
  'deadline_to_empty_ms':deadline_to_empty,'crossing_observation_count':len(crossing),'empty_precedes_first_full_artifact':empty<first_art,
  'scorer_missed_sample_periods':json.loads((runtime/'scorer-summary.json').read_text()).get('scheduler',{}).get('missed_sample_periods'),
  'controller_scorer_leak_count':sum(1 for r in ev if isinstance(r.get('schema'),str) and r['schema'].startswith('independent-progress-'))}
 (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
