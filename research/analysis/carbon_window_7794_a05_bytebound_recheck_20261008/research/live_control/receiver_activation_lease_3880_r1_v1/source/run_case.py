from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

OFFSET_NS = 5_000_000_000
TTL_NS = 160_000_000
ACTIVATION_WINDOW_NS = 250_000_000

PROFILES = {
    "BASELINE": (0,0,0,100),
    "INBOUND_QUEUE_80MS": (80,0,0,100),
    "PROCESSING_80MS": (0,80,0,100),
    "OUTBOUND_QUEUE_80MS": (0,0,80,100),
    "STALE_300MS": (0,0,0,300),
}


def wire(proc, row, journal):
    sent_ns=time.perf_counter_ns(); data=json.dumps(row,sort_keys=True,separators=(",",":"))
    proc.stdin.write(data+"\n"); proc.stdin.flush()
    reply_raw=proc.stdout.readline(); recv_ns=time.perf_counter_ns()
    if not reply_raw: raise RuntimeError("server EOF")
    reply=json.loads(reply_raw)
    journal.append({"request":row,"request_wire":data,"sent_ns":sent_ns,
                    "reply":reply,"reply_wire":reply_raw.rstrip("\n"),"recv_ns":recv_ns})
    return reply,sent_ns,recv_ns


def source_hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--arm",choices=["TRANSLATED_LOWER","RECEIVER_ACTIVATION_TOKEN"],required=True)
    ap.add_argument("--condition",choices=sorted(PROFILES),required=True); ap.add_argument("--rep",type=int,required=True)
    ap.add_argument("--out",required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=False)
    inbound,processing,outbound,wait_ms=PROFILES[a.condition]
    case_id=f"{a.arm}-{a.condition}-r{a.rep}"
    server=Path(__file__).with_name("server.py"); lease=Path(__file__).with_name("lease.py")
    proc=subprocess.Popen([sys.executable,"-S","-B",str(server),"--offset-ns",str(OFFSET_NS)],
                          stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    journal=[]; result={"case_id":case_id,"arm":a.arm,"condition":a.condition,"rep":a.rep,
                        "offset_ns":OFFSET_NS,"ttl_ns":TTL_NS,"activation_window_ns":ACTIVATION_WINDOW_NS,
                        "profile":{"inbound_ms":inbound,"processing_ms":processing,"outbound_ms":outbound,"wait_ms":wait_ms}}
    try:
        if a.arm=="TRANSLATED_LOWER":
            rid=case_id+"-cal"; h1=time.perf_counter_ns()
            cal,_,h4=wire(proc,{"cmd":"calibrate","request_id":rid,"inbound_ms":inbound,
                              "processing_ms":processing,"outbound_ms":outbound},journal)
            lower=cal["c3_ns"]-h4; upper=cal["c2_ns"]-h1
            host_deadline=time.perf_counter_ns()+TTL_NS
            runtime_deadline=host_deadline+lower
            time.sleep(wait_ms/1000.0)
            reply,_,_=wire(proc,{"cmd":"check_abs","request_id":case_id+"-check","deadline_ns":runtime_deadline},journal)
            true_host_check=reply["check_ns"]-OFFSET_NS
            result.update({"h1_ns":h1,"h4_ns":h4,"c2_ns":cal["c2_ns"],"c3_ns":cal["c3_ns"],
                           "lower_ns":lower,"upper_ns":upper,"host_deadline_ns":host_deadline,
                           "runtime_deadline_ns":runtime_deadline,"check_reply":reply,
                           "true_host_check_ns":true_host_check,
                           "actually_live":true_host_check<host_deadline,
                           "deadline_extension_ns":runtime_deadline-(host_deadline+OFFSET_NS)})
        else:
            rid=case_id+"-issue"
            token,_,_=wire(proc,{"cmd":"issue_token","request_id":rid,"generation":1,"ttl_ns":TTL_NS,
                                "inbound_ms":inbound,"processing_ms":processing,"outbound_ms":outbound},journal)
            time.sleep(wait_ms/1000.0)
            reply,_,_=wire(proc,{"cmd":"activate_token","request_id":rid,"generation":1,
                                "token_id":token["token_id"],"activation_window_ns":ACTIVATION_WINDOW_NS},journal)
            result.update({"token_reply":token,"activation_reply":reply})
        shut,_,_=wire(proc,{"cmd":"shutdown"},journal)
        proc.wait(timeout=2)
        stderr=proc.stderr.read()
        result.update({"journal":journal,"shutdown_reply":shut,"server_exit":proc.returncode,"server_stderr":stderr,
                       "source_sha256":{"server.py":source_hash(server),"run_case.py":source_hash(__file__),"lease.py":source_hash(lease)}})
        (out/"record.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        return 0
    finally:
        if proc.poll() is None:
            proc.kill(); proc.wait()

if __name__=="__main__": raise SystemExit(main())
