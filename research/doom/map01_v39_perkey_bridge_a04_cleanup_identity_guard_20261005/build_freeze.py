from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCES=[".gitattributes","README.md","scenario.json","bridge_a04.py","probe_a04.py","audit_a04.py","test_a04.py","build_freeze.py","SOURCE/A03/bridge_a03.py"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=json.loads((HERE/"scenario.json").read_text());f={"schema":"map01_v39_perkey_bridge_a04_identity_guard_freeze_v1","run_id":s["run_id"],
  "H":"A cleanup row sharing an actuation ID but disagreeing on owner, intent or key must remain unscoped and must not retire another active actuation.",
  "T":"Seed an admitted F8 actuation and deliver owner/key/intent/bracket mismatched cleanup rows to frozen A03 and guarded A04 bridge methods.",
  "D":"PASS only if A03 contextually forwards mismatches, A04 keeps each mismatch unscoped and preserves F8 state, while a matching control forwards once.",
  "C":"Finite in-memory malformed-source boundary; no InputOwner behavior or incidence claim.",
  "U":"No real owner, OS input, GUI, game, model, application effect, recovery, threat response or MAP01 progress.",
  "input_sha256":sha(HERE/"scenario.json"),"source_sha256":{p:sha(HERE/p) for p in SOURCES},
  "baseline_invocations":5,"successor_invocations":5,"python_version":"3.12.11","image":"python:3.12.11-slim",
  "image_id":"sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f","platform":"linux/arm64",
  "container":{"network":"none","root_read_only":True,"cpus":1,"memory_mib":512,"pids":64},"scope":"in-memory malformed-cleanup identity boundary; no OS or GUI input"}
 (HERE/"FREEZE.json").write_text(json.dumps(f,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n");print(json.dumps(f,sort_keys=True))
if __name__=="__main__":main()
