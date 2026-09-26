#!/usr/bin/env python3
import json, os, subprocess, sys, time

def main():
    effect_path=sys.argv[1]
    sink=subprocess.Popen([sys.executable,"-B","sink_worker.py",effect_path],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    sink_ready=json.loads(sink.stdout.readline())
    if sink_ready.get("type")!="SINK_READY": return 4
    print(json.dumps({"type":"APP_READY","pid":os.getpid(),"sink_ready":sink_ready,"ready_ns":time.monotonic_ns()}),flush=True)
    line=sys.stdin.readline()
    if not line:
        sink.stdin.close(); sink_rc=sink.wait(timeout=3)
        return 0 if sink_rc==0 else 5
    msg=json.loads(line)
    receive=time.monotonic_ns(); app_check=time.monotonic_ns(); deadline=int(msg["deadline_ns"])
    if app_check>deadline:
        print(json.dumps({"type":"APP_REFUSED_DEADLINE","pid":os.getpid(),"receive_ns":receive,"app_check_ns":app_check}),flush=True)
        sink.stdin.close(); sink_rc=sink.wait(timeout=3)
        return 6 if sink_rc!=0 else 0
    forwarded={"case_id":msg["case_id"],"policy":msg["policy"],"processing_ms":msg["processing_ms"],"deadline_ns":deadline}
    sink.stdin.write(json.dumps(forwarded)+"\n"); sink.stdin.flush(); sink.stdin.close()
    sink_line=sink.stdout.readline(); sink_receipt=json.loads(sink_line) if sink_line else None
    sink_stderr=sink.stderr.read(); sink_rc=sink.wait(timeout=3)
    out={"type":"APP_RESULT","pid":os.getpid(),"receive_ns":receive,"app_check_ns":app_check,
         "deadline_ns":deadline,"sink_receipt":sink_receipt,"sink_exit":sink_rc,"sink_stderr":sink_stderr}
    print(json.dumps(out,sort_keys=True),flush=True)
    return 0 if sink_rc==0 else 7
if __name__=='__main__': raise SystemExit(main())
