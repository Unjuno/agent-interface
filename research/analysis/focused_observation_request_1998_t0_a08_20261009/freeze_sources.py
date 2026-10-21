#!/usr/bin/env python3
"""Freeze A08 source, domains, predecessor provenance, inputs, and host."""
import hashlib,json,os,pathlib,platform,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]; PKG=pathlib.Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 design=(PKG/"design.json").read_bytes(); codes={p:sha((PKG/p).read_bytes()) for p in ("candidate.py","auditor.py","formal_runner.py","freeze_sources.py","test_construction.py")}
 previous="research/analysis/focused_observation_request_successor_1935_v1"
 current="research/analysis/focused_observation_request_1998_t0_a08_20261009"
 paths=[previous+"/PLAN.md",previous+"/REPORT.md",previous+"/MANIFEST.json",previous+"/experiment.py",previous+"/audit.py",previous+"/RESULT.json"]+[current+"/"+n for n in ("design.json","README.md","A07_PREDECESSOR.md","ENVIRONMENT.md")]
 inputs={p:sha((ROOT/p).read_bytes()) for p in paths}
 main_sha=subprocess.run(["git","-C",str(ROOT),"rev-parse","origin/main"],stdout=subprocess.PIPE,check=True).stdout.decode().strip()
 f={"schema":"a08-freeze-v1","allocation":"LABEL-CONTROL-AMBIGUITY-1998-T0-A08-20261009","base_main_commit":main_sha,"predecessor_a07_commit":"67b342e7c7a5e5a1353348dde1e91e62081cdaf1","predecessor_a07_freeze_sha256":"b57e7a6e809b03413eb0f54107c2e7c97f98b60879013f12396fe75ece34cbf2","design_sha256":sha(design),"expected_case_count":27664,"expected_focused_request_count":27648,"expected_valid_focus_count":16,"python_executable":os.path.realpath(sys.executable),"python_version":sys.version,"platform":platform.platform(),"machine":platform.machine(),"kernel_release":platform.release(),"runtime":"native Python under macOS network-denial sandbox; pure standard-library finite fixture","candidate_invocations":1,"auditor_invocations":1,"retries":0,"inputs":inputs,"code_sources":codes,"scope":"exhaustive finite synthetic freshness/identity/focus/region/bounds request semantics only"}
 b=(json.dumps(f,sort_keys=True,indent=2)+"\n").encode(); (PKG/"FREEZE.json").write_bytes(b); (PKG/"FREEZE.sha256").write_text(sha(b)+"  FREEZE.json\n"); print(json.dumps({"freeze_sha256":sha(b),"input_count":len(inputs),"code_count":len(codes),"base_main_commit":main_sha,"expected_case_count":f["expected_case_count"]},sort_keys=True))
if __name__=="__main__": main()
