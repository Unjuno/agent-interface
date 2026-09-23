"""O1/O2 serialized transport ablation on the frozen A1 public controller.

The original O1 in-process gate remains common instrumentation in both arms.
The final transport receiver output is the controller's actual observation.
All PNG and wire archiving/audits occur after controller timing.
"""
import argparse
import hashlib
import json
import random
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
import numpy as np

from tile_transport import Encoder, Decoder
import gui_suite as suite
import motor_feedback

HERE=Path(__file__).resolve().parent
OriginalObserver=suite.Observer
original_archive=suite.audit_and_archive


class WireObserver(OriginalObserver):
    def __init__(self,session,strategy,stream):
        super().__init__(session,"O1",stream)
        self.encoder=Encoder(stream,strategy,64)
        self.decoder=Decoder(stream)
        self.wires=[]

    def sample(self,action_id,reason):
        super().sample(action_id,reason)
        row=self.samples[-1]
        wire=self.encoder.encode(row["source"],action_id=action_id,
                                 observed_ns=row["update"].observed_ns,
                                 context=row["update"].context)
        encoded=time.perf_counter_ns()
        delivered=self.decoder.accept(wire)
        ready=time.perf_counter_ns()
        self.wires.append(dict(wire=wire,**self.encoder.last,decode_ns=ready-encoded))
        row["sample_ns"] += ready-row["ready_ns"]
        row["ready_ns"]=ready
        row["delivered"]=delivered
        self.last=delivered
        return delivered


def archive(observer,out):
    result=original_archive(observer,out)
    records=[]
    decoder=Decoder(observer.encoder.stream)
    for index,(wire,row) in enumerate(zip(observer.wires,observer.samples),1):
        path=out/f"{index:03d}.ait"
        path.write_bytes(wire["wire"])
        # Independent archival receiver roundtrip compared with raw source.
        actual=decoder.accept(path.read_bytes())
        expected=row["source"]
        if actual != expected: raise AssertionError("Wire reconstruction mismatch")
        records.append({k:v for k,v in wire.items() if k!="wire"})
    suite.write_json(out/"wire.json",records)
    result.update(transport=observer.encoder.strategy,
                  wire_bytes=sum(r["wire_bytes"] for r in records),
                  wire_reconstruction_errors=0,
                  wire_encode_ms=float(sum(r["encode_ns"] for r in records)/1e6),
                  wire_decode_ms=float(sum(r["decode_ns"] for r in records)/1e6))
    return result


def sources():
    paths=[HERE/n for n in ("tile_transport.py","test_transport.py","live_suite.py","motor_feedback.py","analyze.py","PROTOCOL.md")]
    paths += [HERE.parent/n for n in suite.code_hashes()]
    return {str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--worker",action="store_true")
    ap.add_argument("--freeze",action="store_true")
    ap.add_argument("--manifest",type=Path)
    ap.add_argument("--phase",choices=("development","fresh"),default="development")
    ap.add_argument("--seed",type=int,default=740101)
    ap.add_argument("--pairs",type=int,default=2)
    ap.add_argument("--app",choices=suite.APPS)
    ap.add_argument("--strategy",choices=("O1","O2"))
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--chromium",default="/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome")
    args=ap.parse_args(); args.out=args.out.resolve()
    if args.worker:
        def interrupted(*_): raise TimeoutError("Worker interrupted")
        signal.signal(signal.SIGTERM,interrupted)
        suite.Observer=WireObserver; suite.audit_and_archive=archive
        suite.controller=motor_feedback.controller
        result=suite.episode(args.app,args.seed,args.strategy,args.chromium,args.out)
        print(json.dumps({k:result.get(k) for k in ("app","seed","strategy","success","audit_pass","wire_bytes","error")}),flush=True)
        return
    environment=suite.environment(args.chromium)
    environment["transport_sources"]=sources()
    environment["transport_parameters"]={"tile_size":64,"zlib_level":1,"fallback":"smallest actual wire packet"}
    if args.phase=="fresh":
        if args.manifest is None: ap.error("Fresh needs a freeze")
        frozen=json.loads(args.manifest.read_text())
        for key in ("versions","transport_sources","transport_parameters"):
            if frozen[key]!=environment[key]: ap.error("Freeze mismatch: "+key)
    args.out.mkdir(parents=True,exist_ok=False)
    suite.write_json(args.out/"environment.json",environment)
    if args.freeze:
        suite.write_json(args.out/"freeze.json",environment)
        for name in sources():
            target=args.out/"source"/name; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(HERE.parent/name,target)
        return
    schedule=[(app,args.seed+i) for i in range(args.pairs) for app in suite.APPS]
    random.Random(args.seed).shuffle(schedule)
    suite.write_json(args.out/"schedule.json",dict(phase=args.phase,pairs=schedule,seed=args.seed,
                                                manifest=str(args.manifest),pairs_per_app=args.pairs))
    results=[]
    for app,seed in schedule:
        order=["O1","O2"] if (seed-args.seed)%2==0 else ["O2","O1"]
        for strategy in order:
            path=args.out/f"{app}-{seed}-{strategy}"
            command=[sys.executable,str(HERE/"live_suite.py"),"--worker","--app",app,"--seed",str(seed),
                     "--strategy",strategy,"--chromium",args.chromium,"--out",str(path)]
            process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try: stdout,stderr=process.communicate(timeout=90)
            except subprocess.TimeoutExpired:
                process.terminate()
                try: stdout,stderr=process.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill(); stdout,stderr=process.communicate()
            if path.exists(): (path/"worker.txt").write_text(stdout+stderr)
            result=json.loads((path/"result.json").read_text()) if (path/"result.json").exists() else dict(success=False,error=stderr)
            result["relative_path"]=path.name; results.append(result)
            with (args.out/"runs.jsonl").open("a") as log: log.write(json.dumps(result)+"\n")
            print(json.dumps({k:result.get(k) for k in ("app","seed","strategy","success","audit_pass","wire_bytes","error")}),flush=True)
            if process.returncode or not result.get("success") or not result.get("audit_pass") or result.get("wire_reconstruction_errors")!=0:
                suite.write_json(args.out/"STOPPED.json",dict(failed=path.name))
                raise SystemExit(2)
    suite.write_json(args.out/"COMPLETE.json",dict(runs=len(results),success=sum(r["success"] for r in results)))


if __name__=="__main__": main()
