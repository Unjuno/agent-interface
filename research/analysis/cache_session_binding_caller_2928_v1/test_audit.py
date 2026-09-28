"""Mutation controls for the raw-only #2928 session-binding auditor."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
AUDITOR = ROOT / "audit.py"
RAW = json.loads((ROOT / "RAW.json").read_text(encoding="utf-8"))


def run_audit(value):
    with tempfile.TemporaryDirectory(prefix="2928-session-audit-") as temp:
        path = Path(temp) / "raw.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(AUDITOR), str(path)],
            check=False, capture_output=True, text=True,
        )


positive = run_audit(RAW)
assert positive.returncode == 0, positive.stdout + positive.stderr

mutations = {}
missing = copy.deepcopy(RAW); missing["rows"].pop(); mutations["missing_row"] = missing
duplicate = copy.deepcopy(RAW); duplicate["rows"].append(copy.deepcopy(duplicate["rows"][0])); mutations["duplicate_row"] = duplicate
session = copy.deepcopy(RAW); session["rows"][1]["request_session_id"] = "session-other"; mutations["request_session"] = session
payload = copy.deepcopy(RAW); payload["rows"][1]["reuse_payload"]["target_id"] = "target-corrupt"; mutations["payload"] = payload
execution = copy.deepcopy(RAW); execution["rows"][1]["execute_adapter_calls"] = 0; mutations["execute_count"] = execution

for name, value in mutations.items():
    result = run_audit(value)
    assert result.returncode == 1, f"{name} accepted: {result.stdout} {result.stderr}"
    parsed = json.loads(result.stdout)
    assert parsed["errors"], f"{name} returned no audit errors"

print(json.dumps({"positive": "PASS", "corruptions_rejected": len(mutations),
                  "controls": sorted(mutations)}, sort_keys=True))
