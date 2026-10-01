from __future__ import annotations
import argparse, json, os, pathlib, random, signal, subprocess, sys, tempfile, time
from Xlib import display, X, Xatom
from Xlib.ext import xtest
from policy import classify, coarse
SCENARIOS=['SUCCESS','IN_PROGRESS','BLOCKED','AUTHORITY_REQUIRED','TARGET_NOT_FOUND','CAPABILITY_UNSUPPORTED','IMPOSSIBLE_UNDER_CONSTRAINTS','FAILED_UNKNOWN','CONFLICT']
def rpc(p,obj,timeout=2.0):
    p.stdin.write(json.dumps(obj)+'\n'); p.stdin.flush();
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        line=p.stdout.readline()
        if line: return json.loads(line)
    raise TimeoutError(obj)
def click(d,xy):
    xtest.fake_input(d,X.MotionNotify,x=xy[0],y=xy[1]); d.sync()
    xtest.fake_input(d,X.ButtonPress,detail=1); d.sync()
    xtest.fake_input(d,X.ButtonRelease,detail=1); d.sync()
def run_case(root,idx,scenario):
    cdir=root/f'case-{idx:03d}'; cdir.mkdir(parents=True)
    xvfb=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x360x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=open(cdir/'xvfb.stderr','wb'),text=True,start_new_session=True)
    dispnum=xvfb.stdout.readline().strip(); env=os.environ.copy(); env['DISPLAY']=f':{dispnum}'
    auth=cdir/'Xauthority'; cookie=os.urandom(16).hex(); subprocess.run(['xauth','-f',str(auth),'add',f':{dispnum}','MIT-MAGIC-COOKIE-1',cookie],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); env['XAUTHORITY']=str(auth); os.environ['DISPLAY']=env['DISPLAY']; os.environ['XAUTHORITY']=str(auth)
    app=subprocess.Popen([sys.executable,'-B',str(pathlib.Path(__file__).with_name('app.py')),scenario],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=open(cdir/'app.stderr','w'),text=True,bufsize=1,env=env,start_new_session=True)
    ready=json.loads(app.stdout.readline()); snap0=ready['snapshot']; d=display.Display(env['DISPLAY'])
    request_id='req-1'; evidence={
      'request_id':request_id,'target_present':snap0['target_present'],'authority_current':True,'capability_supported':True,
      'constraints_satisfiable':True,'modal_blocking':scenario=='BLOCKED','input_dispatched':False,'app_request_seen':False,
      'pending_receipt':False,'effect_receipts':[],'evidence_complete':True,'deadline_elapsed':False
    }
    if scenario=='AUTHORITY_REQUIRED': evidence['authority_current']=False
    if scenario=='CAPABILITY_UNSUPPORTED': evidence['capability_supported']=False
    if scenario=='IMPOSSIBLE_UNDER_CONSTRAINTS': evidence['constraints_satisfiable']=False
    if scenario=='FAILED_UNKNOWN': evidence['evidence_complete']=False
    pre_negative = scenario in {'BLOCKED','AUTHORITY_REQUIRED','TARGET_NOT_FOUND','CAPABILITY_UNSUPPORTED','IMPOSSIBLE_UNDER_CONSTRAINTS'}
    if not pre_negative:
        click(d,snap0['target_center']); evidence['input_dispatched']=True; time.sleep(0.10)
    snap1=rpc(app,{'cmd':'snapshot'})
    for row in snap1['journal']:
        if row['kind']=='REQUEST_SEEN': evidence['app_request_seen']=True
        elif row['kind']=='PENDING': evidence['pending_receipt']=True
        elif row['kind']=='EFFECT': evidence['effect_receipts'].append({'request_id':row['request_id'],'value':row['value'],'t_ns':row['t_ns']})
    evidence['deadline_elapsed']=scenario in {'IN_PROGRESS','FAILED_UNKNOWN'}
    decision=classify(evidence); baseline=coarse(evidence)
    # scoring-only settle: retain later truth but never feed it back to decision
    if scenario=='IN_PROGRESS': time.sleep(0.28)
    final=rpc(app,{'cmd':'snapshot'})
    expected={
      'SUCCESS':'SUCCEEDED','IN_PROGRESS':'IN_PROGRESS','BLOCKED':'BLOCKED','AUTHORITY_REQUIRED':'AUTHORITY_REQUIRED',
      'TARGET_NOT_FOUND':'TARGET_NOT_FOUND','CAPABILITY_UNSUPPORTED':'CAPABILITY_UNSUPPORTED','IMPOSSIBLE_UNDER_CONSTRAINTS':'IMPOSSIBLE_UNDER_CONSTRAINTS',
      'FAILED_UNKNOWN':'FAILED_UNKNOWN','CONFLICT':'CONFLICT'}[scenario]
    close=rpc(app,{'cmd':'close'}); app.wait(timeout=2)
    d.close(); xvfb.terminate(); xvfb.wait(timeout=2)
    row={'case_index':idx,'scenario':scenario,'evidence':evidence,'decision':decision,'baseline':baseline,'expected':expected,
         'pre':snap0,'snapshot_at_decision':snap1,'scoring_final':final,'close':close,'app_exit':app.returncode,'xvfb_exit':xvfb.returncode}
    (cdir/'raw.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    return row
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--reps',type=int,default=1); args=ap.parse_args()
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False)
    sched=[]
    for r in range(args.reps):
        rot=r%len(SCENARIOS); sched += SCENARIOS[rot:]+SCENARIOS[:rot]
    rows=[]
    for i,s in enumerate(sched): rows.append(run_case(out,i,s))
    summary={'status':'COMPLETE','rows':len(rows),'schedule':sched,'candidate_matches':sum(r['decision']['label']==r['expected'] for r in rows),
      'baseline_identical_retry':sum(r['baseline']['advice']=='RETRY_IDENTICAL' for r in rows),
      'baseline_premature_terminal':sum(r['baseline']['label']=='FAILED' and r['expected'] in {'IN_PROGRESS','FAILED_UNKNOWN'} for r in rows)}
    (out/'RUN.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,sort_keys=True))
if __name__=='__main__': main()
