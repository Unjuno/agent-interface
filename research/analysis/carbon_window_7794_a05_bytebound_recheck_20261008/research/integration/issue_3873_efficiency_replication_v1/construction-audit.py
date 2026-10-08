"""Independent construction gate audit. Performs no model calls."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LOCK=json.loads((HERE/"formal-source-lock.json").read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
errors=[]
if LOCK["base_commit"]!="fab3b392fb854696312a85a6b859a78369c3e737":errors.append("base_commit")
for group,base in (("protocol_sources",ROOT/"research/live_control"),("harness_sources",HERE),("support_sources",ROOT)):
    for name,digest in LOCK[group].items():
        p=base/name
        if not p.is_file() or sha(p)!=digest:errors.append(group+":"+name)
if LOCK["seed"]!=284937:errors.append("seed")
for name,digest in LOCK["environment_sources"].items():
    if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:errors.append("environment_sources:"+name)
for name,digest in LOCK["construction_audit"]["files"].items():
    if not (HERE/name).is_file() or sha(HERE/name)!=digest:errors.append("construction_audit:"+name)
if len(LOCK["smoke_evidence"]["files"])<1:errors.append("smoke_files")
for group in ("smoke_evidence","runtime_startup_smoke"):
    for name,digest in LOCK[group]["files"].items():
        if not (HERE/name).is_file() or sha(HERE/name)!=digest:errors.append(group+":"+name)
result={"status":"PASS_CONSTRUCTION_LOCK" if not errors else "STOP_CONSTRUCTION_LOCK",
        "model_calls":0,"errors":errors,"base_commit":LOCK["base_commit"],"seed":LOCK["seed"]}
(HERE/"evidence/construction-audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
raise SystemExit(0 if not errors else 1)
