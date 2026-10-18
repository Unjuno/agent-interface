#!/usr/bin/env python3
import hashlib, json, platform, subprocess
from datetime import datetime, timezone
from pathlib import Path
import generate

ROOT=Path(__file__).parent.resolve()
A09=ROOT.parent/"looming_yield_5905_image_only_t0_9_a09_20261005"
BASE="f44c5f5724ed2ba1d44cab9a8b3f88f5179c014c"
IMAGE="python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
SOURCE_HASHES={"candidate.py":"caf4a7078edde9164a17ab70d9f59ad868536dc841a33c8840f5784399690465","audit.py":"7ed3a6ebe66994261f56750df75d0ed162c7b0b6d8dfd4596fdc67aa4d771e3d"}
SOURCES=("PROTOCOL.md","CONSTRUCTION_LOG.md","generate.py","test_protocol.py","run_mount_preflight.py","prepare_freeze.py","run_formal.py","PREFLIGHT.json","preflight.stdout.txt","preflight.stderr.txt","bundle/observations/manifest.json","bundle/truth/sealed_truth.json")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    latest=subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip()
    base=subprocess.check_output(["git","merge-base","HEAD","origin/main"],cwd=ROOT,text=True).strip()
    if latest!=BASE or base!=BASE: raise SystemExit(f"STOP_MAIN_CHANGED expected={BASE} latest={latest} merge_base={base}")
    for name,h in SOURCE_HASHES.items():
        if sha(A09/name)!=h: raise SystemExit("STOP_A09_SOURCE_HASH:"+name)
    image=subprocess.check_output(["docker","image","inspect",IMAGE,"--format","{{.Id}} {{.Os}}/{{.Architecture}}"],text=True).strip()
    if not image.startswith(IMAGE.split("@",1)[1]+" linux/arm64"): raise SystemExit("STOP_IMAGE_IDENTITY:"+image)
    data=generate.write(); frames=sorted((ROOT/"bundle/observations").glob("*/*.pgm"))
    if len(frames)!=180: raise SystemExit("STOP_FRAME_COUNT")
    frozen={"allocation":"UNJUNO-8112-BOUNDARY-JITTER-A03-ORBSTACK-20261005","issue":8112,"predecessors":{"A01":"STOP_MAIN_ADVANCED_BEFORE_CANDIDATE","A02":"STOP_MAIN_ADVANCED_BEFORE_CANDIDATE"},"base_commit":BASE,"branch":"research/8112-boundary-jitter-a03-20261005","frozen_at_utc":datetime.now(timezone.utc).isoformat(),"seed":generate.SEED,"sequences":36,"frames":180,"approaches":24,"controls":12,"sample_times_ms":generate.TIMES,"contact_radius_px":generate.CONTACT,"thresholds":{"pixel":[50,100,200,400,800,1600,3200,6400,12800],"area":[0.01,0.02,0.05,0.10,0.20,0.40,0.80],"ttc_ms":[100,200,400,800,1600,3200,6400],"lead_margin_ms":100},"candidate_reference":{"path":"../looming_yield_5905_image_only_t0_9_a09_20261005/candidate.py","sha256":SOURCE_HASHES["candidate.py"]},"auditor_reference":{"path":"../looming_yield_5905_image_only_t0_9_a09_20261005/audit.py","sha256":SOURCE_HASHES["audit.py"]},"image":IMAGE,"image_id":image,"runtime":{"engine":"OrbStack Docker","network":"none","rootfs":"read-only","cpu_requested":1,"memory_requested":"1g","memory_enforcement":"not asserted","candidate_truth_mount":False,"separate_output_mounts":True},"host":{"platform":platform.platform(),"python":platform.python_version()},"source_sha256":{n:sha(ROOT/n) for n in SOURCES},"frame_sha256":{str(p.relative_to(ROOT)):sha(p) for p in frames},"formal_invocations_before_freeze":{"candidate":0,"auditor":0,"retries":0}}
    (ROOT/"FROZEN.json").write_text(json.dumps(frozen,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"freeze":"written","base":BASE,"seed":generate.SEED,"frames":len(frames),"formal_invocations":0}))

if __name__=="__main__": main()
