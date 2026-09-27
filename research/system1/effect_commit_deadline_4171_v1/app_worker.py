#!/usr/bin/env python3
import json, os, sys, time

def main():
    print(json.dumps({"type":"READY","pid":os.getpid(),"ready_ns":time.monotonic_ns()}), flush=True)
    line=sys.stdin.readline()
    if not line:
        print(json.dumps({"type":"NO_DISPATCH","pid":os.getpid(),"exit_ns":time.monotonic_ns()}), flush=True)
        return 0
    msg=json.loads(line)
    recv=time.monotonic_ns()
    processing_ms=int(msg["processing_ms"])
    time.sleep(processing_ms/1000.0)
    precommit=time.monotonic_ns()
    deadline=int(msg["deadline_ns"])
    policy=msg["policy"]
    if policy=="APP_COMMIT_DEADLINE" and precommit>deadline:
        print(json.dumps({
            "type":"REFUSED_DEADLINE","case_id":msg["case_id"],"pid":os.getpid(),
            "receive_ns":recv,"precommit_ns":precommit,"effect_ns":None,
            "deadline_ns":deadline,"effect_committed":False,"within_deadline":False
        }, sort_keys=True), flush=True)
        return 0
    effect=time.monotonic_ns()
    print(json.dumps({
        "type":"EFFECT","case_id":msg["case_id"],"pid":os.getpid(),
        "receive_ns":recv,"precommit_ns":precommit,"effect_ns":effect,
        "deadline_ns":deadline,"effect_committed":True,"within_deadline":effect<=deadline
    }, sort_keys=True), flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
