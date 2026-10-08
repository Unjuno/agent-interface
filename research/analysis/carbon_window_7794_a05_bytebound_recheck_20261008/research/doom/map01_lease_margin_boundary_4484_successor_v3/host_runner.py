#!/usr/bin/env python3
"""One-shot real AF_UNIX bridge: frozen sender -> production exchange -> production Lease."""
import argparse, ast, hashlib, json, os, pathlib, subprocess, time, uuid
from unix_json_deadline import exchange

EXPECTED={"effective-controller.py":"edd4cea89c541d42457e8c48992d3efe1bcb0ab7610489b47e8efa60660aab3a"}
CASES=[("deadline-5s",5_000_000_000),("deadline-5s249ms",5_249_000_000),
       ("deadline-5s250ms",5_250_000_000),("deadline-6s",6_000_000_000),
       ("deadline-31s",31_000_000_000)]

class HostClock:
    def __init__(self): self.reads=[]
    def perf_counter_ns(self):
        n=time.perf_counter_ns(); self.reads.append(n); return n

class Pipe:
    def __init__(self,sock,clock): self.sock=sock; self.clock=clock; self.pending=None; self.rows=[]; self.idx=0
    def write(self,line):
        msg=json.loads(line)
        if msg.get("op")=="clock":
            h1=self.clock.reads[-1]; rid="clock-%d"%self.idx; self.idx+=1
            resp=exchange(self.sock,{"kind":"clock","request_id":rid,"host_send_ns":h1},timeout=2)
            self.pending={"event":"clock","runtime_ns":resp["container_send_ns"],"response":resp}
            self.rows.append({"request":msg,"response":resp})
        elif msg.get("op")=="submit":
            rid=msg.get("id","lease-%d"%self.idx)
            resp=exchange(self.sock,{"kind":"lease","request_id":rid,"deadline_ns":msg["valid_until_ns"]},timeout=2)
            self.pending={"event":"accepted" if resp.get("decision")=="accepted" else "rejected",
                          "id":rid,"response":resp}
            self.rows.append({"request":msg,"response":resp})
        else: raise ValueError("unexpected protocol operation")
        return len(line)
    def flush(self): return None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source",required=True); ap.add_argument("--socket",required=True)
    ap.add_argument("--out",required=True); ap.add_argument("--image-id",required=True); a=ap.parse_args()
    src=pathlib.Path(a.source); b=src.read_bytes(); sha=hashlib.sha256(b).hexdigest()
    if sha!=EXPECTED["effective-controller.py"]: raise SystemExit("STOP_SOURCE_SHA256_MISMATCH")
    matches=[n for n in ast.walk(ast.parse(b.decode())) if isinstance(n,ast.ClassDef) and n.name=="_LeaseClockStdin"]
    if len(matches)!=1: raise SystemExit("STOP_SENDER_CLASS_COUNT")
    out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    ready=out/"server-ready.json"; journal=out/"server.jsonl"
    deadline=time.monotonic()+15
    while not ready.exists() and time.monotonic()<deadline: time.sleep(.02)
    if not ready.exists(): raise SystemExit("STOP_CONTAINER_SERVER_NOT_READY")
    outcomes=[]; started=False
    for cid,margin in CASES:
        clock=HostClock(); pipe=Pipe(a.socket,clock); log=out/(cid+".translations.jsonl")
        ns={"json":json,"time":clock,"wait":lambda predicate,s=pipe:s.pending}
        exec(compile(ast.Module(body=[matches[0]],type_ignores=[]),str(src),"exec"),ns)
        h0=time.perf_counter_ns(); host_deadline=h0+margin; sender=ns["_LeaseClockStdin"](pipe,0,log)
        error=None; started=True
        try:
            sender.write(json.dumps({"op":"submit","id":cid,"valid_until_ns":host_deadline,
                 "steps":[{"op":"observe"}]})+"\n"); sender.flush()
        except Exception as e: error={"type":type(e).__name__,"message":str(e)}
        translations=[json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
        outcomes.append({"case_id":cid,"margin_ns":margin,"host_deadline_ns":host_deadline,
            "host_clock_reads_ns":clock.reads,"rows":pipe.rows,"translation_rows":translations,
            "exception":error,"final_response":pipe.pending})
    shutdown=exchange(a.socket,{"kind":"shutdown","request_id":"shutdown"},timeout=2)
    raw={"schema":"issue-5062-real-socket-v1","source_commit":"defb4b5b27d6e2faf39c7d8a4a08dfa279ca0bd6",
         "sender_blob":"096adf9b60eaf6a31fe92c836f57d1a4d26b177e","sender_sha256":sha,
         "exchange_blob":"267b5ccce24ca43b8a6e9b36219d50342888aa27",
         "lease_blob":"b9dac6bb4063928354733d79bf371909a288a3d1",
         "server_blob":"7f1230258d52e567c2a05ea9b9852138cfbfd206",
         "image_id":a.image_id,"docker_context":"default","network":"none","cases":outcomes,
         "shutdown_response":shutdown,"container_ready":json.loads(ready.read_text()),
         "server_journal":journal.read_text() if journal.exists() else ""}
    (out/"raw.json").write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
    print("REAL_SOCKET_CASES_COMPLETED",len(outcomes))
if __name__=="__main__": main()

