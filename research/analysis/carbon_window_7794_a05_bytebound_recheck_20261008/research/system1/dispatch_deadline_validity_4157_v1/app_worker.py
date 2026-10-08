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
    if msg.get("type") != "DISPATCH":
        print(json.dumps({"type":"ERROR","reason":"bad_message","receive_ns":recv}), flush=True)
        return 3
    effect=recv
    out={
        "type":"EFFECT",
        "pid":os.getpid(),
        "case_id":msg["case_id"],
        "receive_ns":recv,
        "effect_ns":effect,
        "start_ns":msg["start_ns"],
        "deadline_ns":msg["deadline_ns"],
        "within_deadline": effect <= msg["deadline_ns"],
        "payload": msg["payload"],
    }
    print(json.dumps(out, sort_keys=True), flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
