"""Verify the retained A02 package file manifest and freeze links."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/"SHA256SUMS.json").read_text(encoding="utf-8"))
actual={}
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or "__pycache__" in path.parts or path.name=="SHA256SUMS.json":
        continue
    actual[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
if actual != manifest:
    missing=sorted(set(manifest)-set(actual)); unlisted=sorted(set(actual)-set(manifest))
    mismatched=sorted(k for k in set(actual)&set(manifest) if actual[k]!=manifest[k])
    raise SystemExit(json.dumps({"missing":missing,"unlisted":unlisted,"mismatched":mismatched}))
freeze=json.loads((ROOT/"GUARD_FREEZE.json").read_text(encoding="utf-8"))
for name,digest in freeze["prior_a01_inputs"].items():
    if actual.get(name)!=digest: raise SystemExit(f"freeze input mismatch: {name}")
if actual[freeze["runtime_guard"]["snapshot"]]!=freeze["runtime_guard"]["sha256"]:
    raise SystemExit("guard source snapshot mismatch")
print(json.dumps({"verified":True,"files":len(actual),"bytes":sum((ROOT/k).stat().st_size for k in actual)},sort_keys=True))
