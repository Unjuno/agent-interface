from __future__ import annotations
import json,pathlib,shutil,subprocess,time,statistics,os
ROOT=pathlib.Path('/tmp/lab/src');DOOM=ROOT/'research/doom';LIVE=ROOT/'research/live_control';DUAL=pathlib.Path('/tmp/lab/dual_lifetime');PY='/tmp/lab/venv/bin/python';FIXTURE=DOOM/'fixtures/map01-threat-contact-v2/fixture.json';OUTROOT=DUAL/'guard-runs';AUTH_MS=600

def send(p,o):p.stdin.write(json.dumps(o,separators=(',',':'))+'\n');p.stdin.flush()
def read(p,deadline):
 while time.monotonic()<deadline:
  line=p.stdout.readline()
  if not line:
   if p.poll() is not None:return None
   continue
  try:return json.loads(line)
  except json.JSONDecodeError:continue
 return None
def direct(out):
 p=out/'scorer-samples.jsonl';rows=[]
 if not p.exists():return None
 for l in p.read_text().splitlines():
  try:rows.append(json.loads(l))
  except:pass
 return next((x['payload'] for x in reversed(rows) if x.get('direct_final_sample') is True),None)
def score_ok(out):
 s=json.loads((out/'score.json').read_text());d=direct(out);return d is not None and all(s[k]==d[k] for k in ('map_exit','episode_finished','player_dead','death_count','kill_count'))

def run_one(seed,arm,label):
 out=OUTROOT/label;shutil.rmtree(out,ignore_errors=True)
 script=DUAL/('session_map01_dual_lifetime_v1.py' if arm=='capture_hold' else 'session_map01_dual_guard_v1.py')
 env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(DUAL),str(LIVE),str(DOOM),env.get('PYTHONPATH','')])
 p=subprocess.Popen([PY,str(script),'--out',str(out),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIXTURE)],cwd=DOOM,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 events=[];last=None;clock=None;term=None;ident=f'{label}-cmp'
 try:
  dl=time.monotonic()+20
  while time.monotonic()<dl and last is None:
   r=read(p,dl)
   if r is None:break
   events.append(r)
   if r.get('event')=='observation':last=r['sequence']
  if last is None:raise RuntimeError('initial obs missing')
  send(p,{'op':'clock'});dl=time.monotonic()+3
  while time.monotonic()<dl:
   r=read(p,dl)
   if r is None:break
   events.append(r)
   if r.get('event')=='observation':last=r['sequence']
   if r.get('event')=='clock':clock=r;break
  if clock is None:raise RuntimeError('clock missing')
  valid=int(clock['runtime_ns'])+AUTH_MS*1_000_000
  send(p,{'op':'submit','id':ident,'expected_sequence':last,'valid_until_ns':valid,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':2000}]})
  obs=[];dl=time.monotonic()+8
  while time.monotonic()<dl:
   r=read(p,dl)
   if r is None:break
   events.append(r)
   if r.get('event')=='observation' and r.get('id')==ident:obs.append(r)
   if r.get('event')=='terminal' and r.get('id')==ident:term=r;break
  if term is None:raise RuntimeError('terminal missing')
  send(p,{'op':'finish'})
  try:p.wait(timeout=8)
  except subprocess.TimeoutExpired:p.kill();p.wait()
  (out/'harness-stderr.txt').write_text(p.stderr.read())
  owner=json.loads((out/'owner-events.json').read_text());rel=next((x for x in owner if x.get('event')=='owner_release' and x.get('reason')=='expired'),None)
  if rel is None:raise RuntimeError('release missing')
  v=rel['verified_ns'];post=term.get('post_authority_observation') or {};seq=post.get('sequence');fresh=next((o for o in obs if o.get('sequence')==seq and o.get('capture_ns',0)>=v),None)
  if fresh is None:raise RuntimeError('post obs missing')
  after=sum(1 for e in events if e.get('event') in ('input_admission','pointer_admission') and (e.get('admitted_ns') or 0)>v)
  guard=next((e for e in events if e.get('event')=='hold_guard_summary' and e.get('id')==ident),None)
  pre=sum(1 for o in obs if o.get('capture_ns',0)<v)
  return {'seed':seed,'arm':arm,'label':label,'terminal_status':term.get('status'),'release_verified':rel.get('verified'),'keys_down':rel.get('keys_down'),'buttons_down':rel.get('buttons_down'),'deadline_to_empty_ms':(v-valid)/1e6,'release_to_fresh_capture_ms':(fresh['capture_ns']-v)/1e6,'post_release_input_admissions':after,'post_authority':post,'pre_release_observations':pre,'guard_summary':guard,'score_agreement':score_ok(out)}
 finally:
  if p.poll() is None:
   try:send(p,{'op':'finish'})
   except:pass
   try:p.wait(timeout=2)
   except:p.kill();p.wait()

def aggregate(rs):
 c=[r for r in rs if r['arm']=='capture_hold'];g=[r for r in rs if r['arm']=='guard_hold'];pairs=[]
 for seed in (993300,993301,993302):
  a=next(r for r in c if r['seed']==seed);b=next(r for r in g if r['seed']==seed);pairs.append({'seed':seed,'capture_ms':a['release_to_fresh_capture_ms'],'guard_ms':b['release_to_fresh_capture_ms'],'improvement_ms':a['release_to_fresh_capture_ms']-b['release_to_fresh_capture_ms']})
 hard=all(r['release_verified'] is True and r['keys_down']==[] and r['buttons_down']==[] and r['post_release_input_admissions']==0 and r['terminal_status']=='authority_ended' and r['score_agreement'] and r['post_authority'].get('captures')==1 and r['post_authority'].get('within_lifecycle_deadline') is True for r in rs) and all(r['pre_release_observations']>=1 and isinstance(r['guard_summary'],dict) for r in g)
 sm={'capture_release_to_fresh_median_ms':statistics.median(r['release_to_fresh_capture_ms'] for r in c),'guard_release_to_fresh_median_ms':statistics.median(r['release_to_fresh_capture_ms'] for r in g),'paired_improvement_median_ms':statistics.median(p['improvement_ms'] for p in pairs),'capture_deadline_to_empty_median_ms':statistics.median(r['deadline_to_empty_ms'] for r in c),'guard_deadline_to_empty_median_ms':statistics.median(r['deadline_to_empty_ms'] for r in g),'capture_pre_release_observations_median':statistics.median(r['pre_release_observations'] for r in c),'guard_pre_release_observations_median':statistics.median(r['pre_release_observations'] for r in g)}
 sm['release_regression_ms']=sm['guard_deadline_to_empty_median_ms']-sm['capture_deadline_to_empty_median_ms']
 dec='REJECT' if not hard else ('PROMOTE_GUARD_BAND' if sm['paired_improvement_median_ms']>=10 and sm['release_regression_ms']<=2 else 'HOLD')
 return {'schema':'dual-lifetime-guard-band-development-result-v1','results':rs,'pairs':pairs,'hard_gates_pass':hard,'summary':sm,'decision':dec}
def main():
 OUTROOT.mkdir(parents=True,exist_ok=True);sched=[(993300,'capture_hold'),(993300,'guard_hold'),(993301,'guard_hold'),(993301,'capture_hold'),(993302,'capture_hold'),(993302,'guard_hold')];rs=[]
 for i,(seed,arm) in enumerate(sched,1):
  r=run_one(seed,arm,f'{i:02d}-{seed}-{arm}');rs.append(r);print(json.dumps({k:r[k] for k in ('label','arm','deadline_to_empty_ms','release_to_fresh_capture_ms','pre_release_observations','post_release_input_admissions','score_agreement')},sort_keys=True),flush=True)
 agg=aggregate(rs);(DUAL/'guard-result.json').write_text(json.dumps(agg,indent=2)+'\n');print(json.dumps({'decision':agg['decision'],**agg['summary'],'hard_gates_pass':agg['hard_gates_pass']},sort_keys=True))
if __name__=='__main__':main()
