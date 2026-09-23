#!/usr/bin/env python3
import json, os, pathlib, sys, time
print(json.dumps({'type':'READY','pid':os.getpid(),'ready_ns':time.monotonic_ns()}), flush=True)
msg=json.loads(sys.stdin.readline())
start=msg['start_ns']; deadline=msg['deadline_ns']
commit_delay=msg['commit_delay_ms']/1000; receipt_delay=msg['receipt_delay_ms']/1000
out=pathlib.Path(msg['out']); out.mkdir(parents=True,exist_ok=True)
time.sleep(commit_delay)
commit_ns=None
if msg['do_commit']:
    p=out/'effect.txt'
    with p.open('wb') as f:
        f.write((msg['session']+'|'+msg['request']).encode()); f.flush(); os.fsync(f.fileno())
    commit_ns=time.monotonic_ns()
    j={'session':msg['session'],'request':msg['request'],'commit_ns':commit_ns,'deadline_ns':deadline,'effect_sha256':__import__('hashlib').sha256(p.read_bytes()).hexdigest()}
    with (out/'journal.json').open('w') as f:
        json.dump(j,f,sort_keys=True); f.flush(); os.fsync(f.fileno())
remaining=max(0, receipt_delay - commit_delay)
time.sleep(remaining)
receipt_ns=time.monotonic_ns()
receipt={'session':msg['session'],'request':msg['request'],'commit_ns':commit_ns,'receipt_ns':receipt_ns,'status':'COMMITTED' if commit_ns else 'NO_COMMIT'}
print(json.dumps(receipt,sort_keys=True),flush=True)
