from __future__ import annotations
import argparse, hashlib, json, sys, time
from lease import Lease, Expired


def nsleep(ms: int) -> None:
    if ms:
        time.sleep(ms / 1000.0)


def send(row: dict) -> None:
    sys.stdout.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offset-ns", type=int, required=True)
    args = ap.parse_args()
    offset = args.offset_ns
    clock = lambda: time.perf_counter_ns() + offset
    tokens: dict[str, dict] = {}
    for raw in sys.stdin:
        request = json.loads(raw)
        cmd = request["cmd"]
        if cmd == "calibrate":
            nsleep(request["inbound_ms"])
            c2 = clock()
            nsleep(request["processing_ms"])
            c3 = clock()
            nsleep(request["outbound_ms"])
            send({"cmd":"calibrate_reply","request_id":request["request_id"],"c2_ns":c2,"c3_ns":c3})
        elif cmd == "check_abs":
            check_started = clock()
            lease = Lease(request["deadline_ns"], clock=clock)
            try:
                lease.check(); status = "LIVE"
            except Expired:
                status = "EXPIRED"
            send({"cmd":"check_abs_reply","request_id":request["request_id"],"status":status,
                  "check_ns":check_started,"deadline_ns":request["deadline_ns"],
                  "task_input_authority":False,"task_success":None})
        elif cmd == "issue_token":
            nsleep(request["inbound_ms"])
            received_ns = clock()
            nsleep(request["processing_ms"])
            issued_ns = clock()
            material = f"{request['request_id']}|{request['generation']}|{issued_ns}|{request['ttl_ns']}".encode()
            token_id = hashlib.sha256(material).hexdigest()[:32]
            tokens[token_id] = {"request_id":request["request_id"],"generation":request["generation"],
                                "issued_ns":issued_ns,"ttl_ns":request["ttl_ns"],"used":False}
            nsleep(request["outbound_ms"])
            send({"cmd":"issue_token_reply","request_id":request["request_id"],"token_id":token_id,
                  "received_ns":received_ns,"issued_ns":issued_ns,"lease_activated":False,
                  "task_input_authority":False,"semantic_authority":False,"task_success":None})
        elif cmd == "activate_token":
            now = clock(); token = tokens.get(request["token_id"])
            reason = None
            if token is None: reason = "UNKNOWN_TOKEN"
            elif token["request_id"] != request["request_id"]: reason = "WRONG_REQUEST"
            elif token["generation"] != request["generation"]: reason = "WRONG_GENERATION"
            elif token["used"]: reason = "REPLAY"
            elif now - token["issued_ns"] > request["activation_window_ns"]: reason = "STALE_TOKEN"
            if reason is not None:
                send({"cmd":"activate_token_reply","request_id":request["request_id"],"status":"REJECTED",
                      "reason":reason,"activation_check_ns":now,"lease_activated":False,
                      "task_input_authority":False,"semantic_authority":False,"task_success":None})
                continue
            token["used"] = True
            deadline = now + token["ttl_ns"]
            lease = Lease(deadline, clock=clock)
            lease.check()
            send({"cmd":"activate_token_reply","request_id":request["request_id"],"status":"ACTIVATED",
                  "reason":None,"activation_check_ns":now,"issued_ns":token["issued_ns"],
                  "token_age_ns":now-token["issued_ns"],"deadline_ns":deadline,"ttl_ns":token["ttl_ns"],
                  "lease_activated":True,"task_input_authority":False,"semantic_authority":False,"task_success":None})
        elif cmd == "shutdown":
            send({"cmd":"shutdown_reply"}); return 0
        else:
            send({"cmd":"error","error":"UNKNOWN_COMMAND"}); return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
