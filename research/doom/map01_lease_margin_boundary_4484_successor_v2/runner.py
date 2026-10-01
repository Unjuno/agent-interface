#!/usr/bin/env python3
"""Deterministic fake-clock test of the exact frozen nested v9 sender class."""
import argparse, ast, hashlib, json
from pathlib import Path

BLOB = "096adf9b60eaf6a31fe92c836f57d1a4d26b177e"
SHA = "edd4cea89c541d42457e8c48992d3efe1bcb0ab7610489b47e8efa60660aab3a"
DURATIONS = [83_333_333, 83_333_333, 83_333_334]
CASES = [
    ("deadline-5s", 5_000_000_000, [300_000_000]*3),
    ("deadline-5s249ms", 5_249_000_000, [300_000_000]*3),
    ("deadline-5s250ms", 5_250_000_000, [300_000_000]*3),
    ("deadline-6s", 6_000_000_000, [300_000_000]*3),
    ("uncertainty-over-1s", 10_000_000_000, [0, 1_200_000_000, 0]),
]
class FakeTime:
    def __init__(self): self.now=10_000_000_000; self.reads=[]
    def perf_counter_ns(self): self.reads.append(self.now); return self.now
class FakeStdin:
    def __init__(self, clock, offsets):
        self.clock=clock; self.offsets=offsets; self.probes=[]; self.pending=None; self.submits=[]
    def write(self, line):
        msg=json.loads(line)
        if msg.get("op")=="clock":
            i=len(self.probes)
            if i>=3: raise AssertionError("unexpected extra clock probe")
            start=self.clock.now; duration=DURATIONS[i]; half=duration//2
            self.clock.now+=half
            runtime=self.clock.now+self.offsets[i]
            self.pending={"event":"clock","runtime_ns":runtime}
            self.probes.append({"host_send_ns":start,"runtime_ns":runtime,
                                "duration_ns":duration,"offset_ns":self.offsets[i]})
            self.clock.now+=duration-half
        else: self.submits.append(msg)
        return len(line)
    def flush(self): return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--image-id",required=True); ap.add_argument("--source-blob",required=True)
    args=ap.parse_args()
    source=Path(args.source); out=Path(args.out); payload=source.read_bytes()
    actual=hashlib.sha256(payload).hexdigest()
    if actual!=SHA or args.source_blob!=BLOB: raise SystemExit("STOP_SOURCE_IDENTITY_MISMATCH")
    tree=ast.parse(payload.decode("utf-8"),filename=str(source))
    matches=[n for n in ast.walk(tree) if isinstance(n,ast.ClassDef) and n.name=="_LeaseClockStdin"]
    if len(matches)!=1: raise SystemExit("STOP_SENDER_CLASS_MATCH_COUNT="+str(len(matches)))
    cls=matches[0]; out.mkdir(parents=True,exist_ok=True); observations=[]
    for cid,lease_ns,offsets in CASES:
        clock=FakeTime(); stream=FakeStdin(clock,offsets)
        log=out/(cid+".translations.jsonl"); log.unlink(missing_ok=True)
        ns={"json":json,"time":clock,"wait":lambda predicate,s=stream:s.pending}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),str(source),"exec"),ns)
        deadline=clock.now+lease_ns
        wrapped=ns["_LeaseClockStdin"](stream,offsets[0],log)
        error=None
        try:
            wrapped.write(json.dumps({"op":"submit","id":cid,"valid_until_ns":deadline,
                                      "steps":[{"op":"observe"}]})+"\n")
            wrapped.flush()
        except Exception as exc: error={"type":type(exc).__name__,"message":str(exc)}
        receipts=[json.loads(s) for s in log.read_text().splitlines()] if log.exists() else []
        observations.append({"case_id":cid,"lease_ns":lease_ns,"host_deadline_ns":deadline,
            "probe_durations_ns":DURATIONS,"probe_rows":stream.probes,
            "host_clock_reads_ns":clock.reads,"exception":error,
            "emitted_submits":stream.submits,"translation_rows":receipts})
    raw={"schema":"issue-5054-frozen-sender-boundary-run-v1",
         "scope":"deterministic fake-clock construction; no game/model/input/network",
         "source_git_blob":args.source_blob,"source_sha256":actual,"image_id":args.image_id,
         "docker_context":"desktop-linux","engine":"28.5.1","network":"none",
         "mounts":"source read-only; root read-only; /out writable","cases":observations}
    (out/"raw.json").write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("CONSTRUCTION_EXECUTED cases="+str(len(observations)))
if __name__=="__main__": main()
