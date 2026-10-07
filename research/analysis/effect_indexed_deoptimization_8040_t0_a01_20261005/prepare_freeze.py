"""Build FROZEN.json once; never rerun after formal start."""
from __future__ import annotations
import hashlib,json,os,platform,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE="d3a51bc4c962b223d05280225042b96a033df8bf"
ALLOCATION="UNJUNO-8040-EFFECT-INDEXED-DEOPT-T0-A01-20261005"
FILES=["README.md","protocol.md","CONSTRUCTION_RECORD.md","preflight.json","build_fixture.py","candidate.py","audit.py","test_construction.py","run_formal.py","prepare_freeze.py","public_trace.json","truth_sidecar.json","construction.build.log","construction.normal.log","construction.optimized.log","construction.pycompile.log"]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    missing=[n for n in FILES if not (ROOT/n).is_file()]
    if missing: raise SystemExit(f"missing freeze input(s): {missing}")
    record={"allocation":ALLOCATION,"issue":8040,"base_commit":BASE,"branch":"research/8040-effect-indexed-deopt-t0-a01-20261005","package_path":"research/analysis/effect_indexed_deoptimization_8040_t0_a01_20261005","formal_invocations_before_freeze":{"driver":0,"candidate":0,"auditor":0},"environment":{"host":platform.platform(),"machine":platform.machine(),"python":sys.version,"execution":"native host substitution after retained OrbStack image-content STOP; one low-priority sequential process","container":"none","network_enforcement":"none"},"files":{n:sha(ROOT/n) for n in FILES}}
    target=ROOT/"FROZEN.json"
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o444)
    with os.fdopen(fd,"w") as f: json.dump(record,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps({"created":"FROZEN.json","sha256":sha(target),"files":len(FILES)},sort_keys=True))
if __name__=="__main__": main()
