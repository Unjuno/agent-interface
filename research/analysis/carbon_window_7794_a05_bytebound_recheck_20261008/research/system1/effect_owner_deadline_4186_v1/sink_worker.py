#!/usr/bin/env python3
import json, os, pathlib, sys, time

def fsync_write(path, obj):
    p=pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data=(json.dumps(obj, sort_keys=True)+"\n").encode()
    fd=os.open(p, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    try:
        os.write(fd,data); os.fsync(fd)
    finally:
        os.close(fd)

def main():
    effect_path=sys.argv[1]
    print(json.dumps({"type":"SINK_READY","pid":os.getpid(),"ready_ns":time.monotonic_ns()}),flush=True)
    line=sys.stdin.readline()
    if not line:
        return 0
    msg=json.loads(line)
    receive=time.monotonic_ns()
    time.sleep(int(msg["processing_ms"])/1000.0)
    precommit=time.monotonic_ns()
    deadline=int(msg["deadline_ns"])
    policy=msg["policy"]
    if policy=="SINK_PRECOMMIT_DEADLINE" and precommit>deadline:
        out={"type":"SINK_REFUSED_DEADLINE","sink_pid":os.getpid(),"case_id":msg["case_id"],
             "receive_ns":receive,"precommit_ns":precommit,"effect_ns":None,"deadline_ns":deadline,
             "effect_committed":False,"within_deadline":False,"posthoc":None}
        print(json.dumps(out,sort_keys=True),flush=True); return 0
    effect=time.monotonic_ns()
    effect_obj={"case_id":msg["case_id"],"sink_pid":os.getpid(),"effect_ns":effect,"deadline_ns":deadline}
    fsync_write(effect_path,effect_obj)
    posthoc=None
    if policy=="SINK_POSTHOC_CHECK":
        posthoc="ON_TIME" if effect<=deadline else "LATE"
    out={"type":"SINK_EFFECT","sink_pid":os.getpid(),"case_id":msg["case_id"],
         "receive_ns":receive,"precommit_ns":precommit,"effect_ns":effect,"deadline_ns":deadline,
         "effect_committed":True,"within_deadline":effect<=deadline,"posthoc":posthoc}
    print(json.dumps(out,sort_keys=True),flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
