"""Verify frozen inputs, outputs, and hashes for T7."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
assert result["main_commit"] == freeze["current_main_commit"]
assert result["adapter_source_sha256"] == freeze["adapter_source_sha256"]
blob = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"{freeze['current_main_commit']}:{freeze['current_backend_path']}"], text=True).strip()
assert blob == freeze["current_backend_blob"]
assert (HERE / "normal.stdout").read_bytes() == (HERE / "optimized.stdout").read_bytes()
assert result["before_accept_failure"]["attribution"] == "UNRESOLVED"
assert result["before_accept_failure"]["trace_integrity"] == "HOLD_INCOMPLETE_RELEASE_BATCH"
assert result["after_accept_failure"]["attribution"] == "TEMPORALLY_UNIQUE"
assert result["after_accept_failure"]["causal_attribution"] == "NOT_ESTABLISHED"
assert result["after_accept_failure"]["producer_ledger_states"] == ["confirmed", "unknown"]
manifest = json.loads((HERE / "SHA256SUMS.json").read_text(encoding="utf-8"))
for name, digest in manifest.items():
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
print(json.dumps({"verified": True, "files_hashed": len(manifest), "disposition": result["disposition"]}, sort_keys=True))
