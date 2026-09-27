#!/usr/bin/env python3
import argparse, json, pathlib, subprocess, sys, time, hashlib
DEADLINE_MS=120
SCHEDULES={
 'ON_TIME_FAST_RECEIPT':(60,80,True),
 'ON_TIME_LATE_RECEIPT':(60,170,True),
 'LATE_COMMIT_FAST_RECEIPT':(150,170,True),
 'NO_COMMIT':(20,80,False),
}
POLICIES=('RECEIPT_ARRIVAL_DEADLINE','OWNER_COMMIT_DEADLINE','COMMIT_FIELD_UNVERIFIED')
def classify(policy, receipt, deadline_ns, journal):
    if receipt['status']=='NO_COMMIT': return 'NO_EFFECT'
    if policy=='RECEIPT_ARRIVAL_DEADLINE': return 'ON_TIME' if receipt['receipt_ns']<=deadline_ns else 'LATE'
    if policy=='OWNER_COMMIT_DEADLINE':
        if not journal or journal.get('session')!=receipt['session'] or journal.get('request')!=receipt['request'] or journal.get('commit_ns')!=receipt['commit_ns']:
            return 'UNKNOWN'
        return 'ON_TIME' if receipt['commit_ns']<=deadline_ns else 'LATE'
    return 'UNKNOWN'
def run_case(root,policy,sched,rep,mode):
    cid=f'{mode}-{rep}-{policy}-{sched}'; cdir=root/cid; cdir.mkdir()
    cd,rd,do=SCHEDULES[sched]; session=f's{rep}-{policy[:3]}-{sched[:3]}'; request=f'r{rep}-{sched}'
    p=subprocess.Popen([sys.executable,'-B','owner.py'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    ready=json.loads(p.stdout.readline())
    if ready.get('type')!='READY': raise RuntimeError('owner not ready')
    start=time.monotonic_ns(); deadline=start+DEADLINE_MS*1_000_000
    msg={'start_ns':start,'deadline_ns':deadline,'commit_delay_ms':cd,'receipt_delay_ms':rd,'do_commit':do,'out':str(cdir/'owner'),'session':session,'request':request}
    p.stdin.write(json.dumps(msg)+'\n'); p.stdin.flush(); p.stdin.close()
    stdout=p.stdout.read(); stderr=p.stderr.read(); p.wait(timeout=3)
    receipt=json.loads(stdout.strip())
    journal=None; jp=cdir/'owner'/'journal.json'
    if jp.exists(): journal=json.loads(jp.read_text())
    visible_journal = None if policy=='COMMIT_FIELD_UNVERIFIED' else journal
    decision=classify(policy,receipt,deadline,visible_journal)
    effect=(cdir/'owner'/'effect.txt').exists()
    row={'case_id':cid,'mode':mode,'rep':rep,'policy':policy,'schedule':sched,'deadline_ms':DEADLINE_MS,'start_ns':start,'deadline_ns':deadline,'receipt':receipt,'journal':journal,'decision':decision,'effect_exists':effect,'owner_exit':p.returncode,'owner_stderr':stderr,'authority':False,'retry_authority':False}
    (cdir/'row.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    return row
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--mode',required=True); ap.add_argument('--reps',type=int,required=True); a=ap.parse_args()
    root=pathlib.Path(a.out); root.mkdir(parents=True)
    rows=[]
    for rep in range(a.reps):
      for sched in SCHEDULES:
       for pol in POLICIES: rows.append(run_case(root,pol,sched,rep,a.mode))
    (root/'ROWS.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rows':len(rows)}))
if __name__=='__main__': main()
