"""Verify recorded V39 dispatch outputs and package hashes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
audit = json.loads((HERE / "AUDIT.json").read_text(encoding="utf-8"))
assert result["disposition"] == "PASS_FUTURE_DISPATCH_CONSTRUCTION_ONLY"
assert result["modes"][0]["session"] == "session_map01_v12.py"
assert result["modes"][1]["session"] == "session_map01_v15.py"
assert result["modes"][0]["report_label"] == "v12_default"
assert result["modes"][1]["report_label"] == "v15_scorer_only_per_key_release"
assert audit["status"] == "PASS_DISPATCH_CONSTRUCTION"
assert audit["checks_passed"] == audit["checks_total"] == 11
assert (HERE / "normal.stdout").read_bytes() == (HERE / "optimized.stdout").read_bytes()
manifest = json.loads((HERE / "SHA256SUMS.json").read_text(encoding="utf-8"))
for name, digest in manifest.items():
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
print(json.dumps({"verified": True, "files_hashed": len(manifest), "disposition": result["disposition"]}, sort_keys=True))
