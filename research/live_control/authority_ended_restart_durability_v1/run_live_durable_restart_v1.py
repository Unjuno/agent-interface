from __future__ import annotations
import json,os,pathlib,shutil,subprocess,time,sys
HERE=pathlib.Path(__file__).resolve().parent
DUAL=pathlib.Path('/tmp/lab/dual_lifetime'); SRC=pathlib.Path('/tmp/lab/src'); DOOM=SRC/'research/doom'; LIVE=SRC/'research/live_control'
PYTHON='/tmp/lab/venv/bin/python'; SESSION=DUAL/'session_map01_dual_quiet_v1.py'; FIXTURE=DOOM/'fixtures/map01-threat-contact-v2/fixture.json'; CHILD=HERE/'ledger_child.py'
def send(p,o):p.stdin.write(json.dumps(o,separators=(',',':'))+'\n');p.stdin.flush()
def next_json(p):
 while True:
  line=p.stdout.readline()
  if not line:
   if p.poll() is not None:return None
   continue
  try:return json.loads(line)
  except json.JSONDecodeError:continue
def start(out,seed):
 shutil.rmtree(out,ignore_errors=True)
 env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(DUAL),str(DOOM),str(LIVE),env.get('PYTHONPATH','')])
 return subprocess.Popen([PYTHON,str(SESSION),'--out',str(out),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIXTURE)],cwd=DOOM,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def until(p,pred,ev,limit=30):
 end=time.monotonic()+limit
 while time.monotonic()<end:
  r=next_json(p)
  if r is None:break
  ev.append(r)
  if pred(r):return r
 raise RuntimeError('event timeout')
def clock(p,ev):send(p,{'op':'clock'});return until(p,lambda r:r.get('event')=='clock',ev,5)
def last_seq(ev):return max(r['sequence'] for r in ev if r.get('event')=='observation')
def call_child(*args):
 q=subprocess.run([PYTHON,str(CHILD),*map(str,args)],capture_output=True,text=True)
 try:o=json.loads(q.stdout.strip().splitlines()[-1])
 except:o={'stdout':q.stdout,'stderr':q.stderr}
 return q.returncode,o
def score_ok(out):
 s=json.loads((out/'score.json').read_text());rows=[json.loads(x) for x in (out/'scorer-samples.jsonl').read_text().splitlines()];d=next(x['payload'] for x in reversed(rows) if x.get('direct_final_sample') is True);return all(s[k]==d[k] for k in ('map_exit','episode_finished','player_dead','death_count','kill_count'))
def make_receipt(term,ev):
 intr=term['interruption'];rel=intr['record'];v=rel['verified_ns'];return {'terminal_status':term['status'],'steps_completed':term['steps_completed'],'release_verified':rel['verified'],'keys_down':rel['keys_down'],'buttons_down':rel['buttons_down'],'post_release_input_admissions':sum(x.get('event')=='input_admission' and x.get('admitted_ns',0)>v for x in ev),'post_authority':term['post_authority_observation'],'authority_end_id':intr['intent_token']},rel
def run(out,seed):
 p=start(out,seed);ev=[];state=out/'durable-token-state.json';receipt_path=out/'first-caller-receipt.json'
 try:
  until(p,lambda r:r.get('event')=='observation',ev,25);c=clock(p,ev);seq=last_seq(ev);deadline=int(c['runtime_ns'])+600_000_000
  send(p,{'op':'submit','id':'first','expected_sequence':seq,'valid_until_ns':deadline,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':2000}]})
  term=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='first',ev,10);receipt,rel=make_receipt(term,ev);receipt_path.write_text(json.dumps(receipt,sort_keys=True))
  rc_issue,o_issue=call_child('issue',state,receipt_path);rid=receipt['authority_end_id']
  rc_recover,o_recover=call_child('recover',state,rid)
  rc_dup_before,o_dup_before=call_child('issue',state,receipt_path)
  input_after_dup=sum(x.get('event')=='input_admission' and x.get('admitted_ns',0)>rel['verified_ns'] for x in ev)
  post_seq=receipt['post_authority']['sequence'];c=clock(p,ev);send(p,{'op':'submit','id':'observe2','expected_sequence':post_seq,'valid_until_ns':int(c['runtime_ns'])+1_000_000_000,'steps':[{'op':'observe'}]})
  obs=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='observe2',ev,8);current=last_seq(ev)
  rc_reval,o_reval=call_child('revalidate',state,rid,current);rc_consume,o_consume=call_child('consume',state,rid)
  input_before_second=sum(x.get('event')=='input_admission' and x.get('admitted_ns',0)>rel['verified_ns'] for x in ev)
  c=clock(p,ev);send(p,{'op':'submit','id':'second','expected_sequence':current,'valid_until_ns':int(c['runtime_ns'])+1_000_000_000,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':80}]})
  acc=until(p,lambda r:r.get('event')=='accepted' and r.get('id')=='second',ev,5);second=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='second',ev,8)
  rc_recover_after,o_recover_after=call_child('recover',state,rid);rc_dup_after,o_dup_after=call_child('issue',state,receipt_path);rc_load,o_load=call_child('load',state)
  input_after_second=sum(x.get('event')=='input_admission' and x.get('admitted_ns',0)>second['release']['verified_ns'] for x in ev)
  send(p,{'op':'finish'});p.wait(timeout=10)
  post_inputs=[x for x in ev if x.get('event')=='input_admission' and x.get('admitted_ns',0)>rel['verified_ns']];second_inputs=[x for x in post_inputs if x.get('admitted_ns',0)>=acc['accepted_ns']]
  return {'schema':'authority-ended-live-durable-restart-v1-result','seed':seed,'authority_end_id':rid,'first_status':term['status'],'post_sequence':post_seq,
   'issue_process':{'rc':rc_issue,'result':o_issue},'restart_recover_process':{'rc':rc_recover,'result':o_recover},'duplicate_before_process':{'rc':rc_dup_before,'result':o_dup_before},'input_after_duplicate_before':input_after_dup,
   'observe2_status':obs['status'],'current_sequence':current,'revalidate_process':{'rc':rc_reval,'result':o_reval},'consume_process':{'rc':rc_consume,'result':o_consume},'input_before_second':input_before_second,
   'second_status':second['status'],'second_release':second['release'],'second_input_admissions':len(second_inputs),
   'restart_recover_after_consume':{'rc':rc_recover_after,'result':o_recover_after},'duplicate_after_process':{'rc':rc_dup_after,'result':o_dup_after},'load_after':{'rc':rc_load,'result':o_load},'input_after_second_release_before_finish':input_after_second,
   'total_post_first_release_input_admissions':len(post_inputs),'score_agreement':score_ok(out),'event_count':len(ev)}
 finally:
  if p.poll() is None:
   try:send(p,{'op':'finish'})
   except:pass
   try:p.wait(timeout=3)
   except:p.kill();p.wait()
  try:(out/'harness-stderr.txt').write_text(p.stderr.read())
  except:pass
if __name__=='__main__':print(json.dumps(run(pathlib.Path(sys.argv[1]),int(sys.argv[2])),indent=2,sort_keys=True))
