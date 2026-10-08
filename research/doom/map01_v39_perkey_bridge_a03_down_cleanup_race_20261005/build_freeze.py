from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCES=[".gitattributes","README.md","scenario.json","bridge_a03.py","probe_a03.py","audit_a03.py","test_a03.py","build_freeze.py","SOURCE/A02/bridge.py"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=json.loads((HERE/"scenario.json").read_text());f={"schema":"map01_v39_perkey_bridge_a03_race_freeze_v1","run_id":s["run_id"],"H":"Cleanup created during the down owner call must resolve using the returned admission's context.","T":"One deterministic in-memory owner stub appends matching confirmed-up cleanup before returning down admission; compare frozen A02 and repaired successor.","D":"PASS only if A02 reproduces unscoped cleanup plus NOOP and A03 emits admission then one contextual confirmed release with neutral state.","C":"Finite stub-controlled ordering witness; does not measure live scheduler incidence.","U":"No real owner, OS input, GUI, game, model, application effect, recovery, threat response, or MAP01 progress.","input_sha256":sha(HERE/"scenario.json"),"source_sha256":{p:sha(HERE/p) for p in SOURCES},"baseline_and_successor_invocations":1,"python_version":"3.12.11","image":"python:3.12.11-slim","image_id":"sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f","platform":"linux/arm64","container":{"network":"none","root_read_only":True,"cpus":1,"memory_mib":512},"scope":"in-memory owner-call ordering stub; no OS or GUI input"}
 (HERE/"FREEZE.json").write_text(json.dumps(f,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n");print(json.dumps(f,sort_keys=True))
if __name__=="__main__":main()
