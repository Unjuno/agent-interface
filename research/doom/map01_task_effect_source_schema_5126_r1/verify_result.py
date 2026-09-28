"""Independent result and source-freeze verifier; does not import run_audit."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
while not (ROOT / ".git").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
freeze = json.loads((HERE / "SOURCE_FREEZE.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
assert result["main_sha"] == freeze["main_sha"]
assert result["disposition"] == "HOLD_SOURCE_IDENTITY_INSUFFICIENT"
assert result["live_calls"] == result["gpu_calls"] == result["docker_calls"] == 0
assert "source_event_id" not in result["scorer_event_keys"]
assert "scorer_epoch_id" not in result["scorer_event_keys"]
assert "source_event_id" not in result["v13_release_receipt_keys"]
assert result["checks"] and all(result["checks"].values())
assert result["legacy_internal_edge_ids_not_in_adapter"] == ["press_id", "release_id"]
for source in freeze["sources"]:
    data = subprocess.check_output(
        ["git", "cat-file", "blob", f"{freeze['main_sha']}:{source['path']}"], cwd=ROOT
    )
    assert len(data) == source["bytes"], source["path"]
    assert hashlib.sha256(data).hexdigest() == source["sha256"], source["path"]
    assert subprocess.check_output(["git", "rev-parse", f"{freeze['main_sha']}:{source['path']}"], cwd=ROOT, text=True).strip() == source["git_blob"]
print(json.dumps({"independent_verification": "PASS", "sources": len(freeze["sources"]),
                  "checks": len(result["checks"]), "disposition": result["disposition"]}, sort_keys=True))
