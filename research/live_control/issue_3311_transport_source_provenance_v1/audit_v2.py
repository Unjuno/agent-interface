"""Snapshot-backed successor audit for retained Issue #3311 transport runs."""
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
MANIFEST=json.loads((HERE/"SOURCE_SNAPSHOT_MANIFEST.json").read_text(encoding="utf-8"))
LEGACY_PATH=HERE/"source_snapshots"/"audit_v1_frozen.py"
spec=importlib.util.spec_from_file_location("issue3311_frozen_audit_v1",LEGACY_PATH)
legacy=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(legacy)

def snapshot_sha(revision: str, repository_path: str) -> str:
    for run in MANIFEST.values():
        if run["commit"] != revision: continue
        for item in run["files"].values():
            if item["path"] == repository_path:
                path=HERE/item["snapshot"]
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                if digest != item["sha256"]: raise ValueError("source snapshot hash mismatch")
                return digest
    raise ValueError("source snapshot missing for revision/path")

legacy.git_source_sha=snapshot_sha

def audit(root: Path) -> dict:
    report=legacy.audit(root)
    report["provenance"]="frozen source snapshot bundle; no git object lookup"
    return report

def main() -> int:
    import sys
    if len(sys.argv)!=2: print(f"usage: {sys.argv[0]} EVIDENCE_DIR"); return 2
    report=audit(Path(sys.argv[1]))
    print(json.dumps(report,indent=2))
    return 0 if report["disposition"].startswith("PASS_") else 1
if __name__=="__main__": raise SystemExit(main())
