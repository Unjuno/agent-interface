#!/usr/bin/env python3
"""Freeze fixture, source, predecessor provenance and local host before execution."""
import hashlib,json,os,pathlib,platform,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]; PKG=pathlib.Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 design=(PKG/"design.json").read_bytes(); codepaths=("candidate.py","auditor.py","formal_runner.py","freeze_sources.py","test_construction.py"); codes={p:sha((PKG/p).read_bytes()) for p in codepaths}
 prior="research/analysis/focused_observation_request_successor_1935_v1"
 paths=[prior+"/PLAN.md",prior+"/REPORT.md",prior+"/MANIFEST.json",prior+"/experiment.py",prior+"/audit.py",prior+"/RESULT.json","research/analysis/focused_observation_request_1998_t0_a07_20261009/design.json","research/analysis/focused_observation_request_1998_t0_a07_20261009/ENVIRONMENT.md"]
 inputs={p:sha((ROOT/p).read_bytes()) for p in paths}
 main_sha=subprocess.run(["git","-C",str(ROOT),"rev-parse","HEAD"],stdout=subprocess.PIPE,check=True).stdout.decode().strip()
 docker=subprocess.run(["docker","version","--format","{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 image=subprocess.run(["docker","image","inspect","python:3.11-slim","--format","{{.Id}} {{.Os}}/{{.Architecture}}"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 f={"schema":"a07-freeze-v1","allocation":"LABEL-CONTROL-AMBIGUITY-1998-T0-A07-20261009","base_main_commit":main_sha,"predecessor":"focused_observation_request_successor_1935_v1","design_sha256":sha(design),"case_count":22,"frame_count":2,"request_templates_per_frame":11,"python_executable":os.path.realpath(sys.executable),"python_version":sys.version,"platform":platform.platform(),"machine":platform.machine(),"kernel_release":platform.release(),"runtime":{"mode":"native-host-fallback","container_engine_probe_sha256":sha(docker.stdout+docker.stderr),"container_engine_probe":{"exit":docker.returncode,"output":(docker.stdout+docker.stderr).decode("utf-8","replace")},"python_image_probe_sha256":sha(image.stdout+image.stderr),"python_image_probe":{"exit":image.returncode,"output":(image.stdout+image.stderr).decode("utf-8","replace")}},"candidate_invocations":1,"auditor_invocations":1,"retries":0,"inputs":inputs,"code_sources":codes,"scope":"finite synthetic focused-observation request semantics only"}
 b=(json.dumps(f,sort_keys=True,indent=2)+"\n").encode(); (PKG/"FREEZE.json").write_bytes(b); (PKG/"FREEZE.sha256").write_text(sha(b)+"  FREEZE.json\n"); print(json.dumps({"freeze_sha256":sha(b),"input_count":len(inputs),"code_count":len(codes),"base_main_commit":main_sha,"container_engine_probe_exit":docker.returncode,"image_probe_exit":image.returncode},sort_keys=True))
if __name__=="__main__": main()
