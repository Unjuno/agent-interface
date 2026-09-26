#!/usr/bin/env python3
import hashlib, json, os, subprocess, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
POLICIES=['EXISTING_CURRENTNESS_ONLY','EXPLICIT_DECISION_DEADLINE']
SCENARIOS=[('ON_TIME',20_000_000),('NEAR_BEFORE',90_000_000),('NEAR_AFTER',150_000_000),('WELL_AFTER',260_000_000)]
REPS=3

def wait_until_ns(target):
    while True:
        now=time.monotonic_ns(); rem=target-now
        if rem<=0: return now
        if rem>2_000_000: time.sleep((rem-1_000_000)/1e9)
        else: time.sleep(0)

def read_line(p, timeout_s=2.0):
    deadline=time.monotonic()+timeout_s
    while time.monotonic()<deadline:
        line=p.stdout.readline()
        if line: return line
    raise TimeoutError('missing line')

def run_case(index, policy, scenario, target_delay_ns, rep):
    case_id=f'{index:02d}-{policy}-{scenario}-r{rep}'
    env={'PATH':os.environ.get('PATH',''), 'PYTHONPATH':''}
    app=subprocess.Popen([sys.executable,'-I','-S','-B',str(HERE/'app.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    obs_id=f'obs-{index:02d}'
    app.stdin.write(json.dumps({'op':'observe','observation_id':obs_id})+'\n'); app.stdin.flush()
    obs_msg=json.loads(read_line(app)); obs=obs_msg['observation']
    target=obs['observation_available_ns']+target_delay_ns
    wait_until_ns(target)
    proposal_ready=time.monotonic_ns()
    packet={
        'policy':policy,'scope':obs['scope'],'observation_id':obs['observation_id'],'expected_observation_id':obs_id,
        'epoch':obs['epoch'],'expected_epoch':7,'observation_available_ns':obs['observation_available_ns'],
        'proposal_ready_ns':proposal_ready,'decision_deadline_ns':obs['decision_deadline_ns'],
        'lease_valid_until_ns':obs['lease_valid_until_ns'],'freshness_budget_ns':obs['freshness_budget_ns'],
        'proposal':'TURN_LEFT'
    }
    cp=subprocess.run([sys.executable,'-I','-S','-B',str(HERE/'policy.py')],input=json.dumps(packet),text=True,capture_output=True,timeout=3,env=env)
    if cp.returncode!=0: raise RuntimeError(f'policy exit {cp.returncode}: {cp.stderr}')
    decision=json.loads(cp.stdout)
    effect=None
    dispatch_ns=None
    if decision['decision']=='ADMIT':
        dispatch_ns=time.monotonic_ns()
        app.stdin.write(json.dumps({'op':'act','action':'TURN_LEFT'})+'\n'); app.stdin.flush()
        effect=json.loads(read_line(app))
    app.stdin.write(json.dumps({'op':'close'})+'\n'); app.stdin.flush()
    closed=json.loads(read_line(app))
    app.stdin.close(); rc=app.wait(timeout=3); stderr=app.stderr.read()
    return {
        'case_id':case_id,'index':index,'policy':policy,'scenario':scenario,'rep':rep,'requested_delay_ns':target_delay_ns,
        'observation':obs,'proposal_ready_ns':proposal_ready,'actual_ready_delay_ns':proposal_ready-obs['observation_available_ns'],
        'packet':packet,'policy_stdout':cp.stdout,'policy_stderr':cp.stderr,'policy_exit':cp.returncode,'decision':decision,
        'dispatch_ns':dispatch_ns,'effect':effect,'closed':closed,'app_exit':rc,'app_stderr':stderr
    }

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: run.py OUTDIR')
    out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False)
    rows=[]; index=0
    # deterministic interleaving prevents all late/on-time cases clustering by policy
    for rep in range(REPS):
        for sidx,(scenario,delay) in enumerate(SCENARIOS):
            order=POLICIES if (rep+sidx)%2==0 else list(reversed(POLICIES))
            for policy in order:
                row=run_case(index,policy,scenario,delay,rep); rows.append(row); index+=1
                (out/f'case-{index-1:02d}.json').write_text(json.dumps(row,sort_keys=True,indent=2)+'\n')
    raw={'schema':'decision-deadline-formal-v1','rows':rows,'formal_reruns':0,'created_end_ns':time.monotonic_ns()}
    (out/'RAW.json').write_text(json.dumps(raw,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'FORMAL_COMPLETE','cases':len(rows)},sort_keys=True))
if __name__=='__main__': main()
