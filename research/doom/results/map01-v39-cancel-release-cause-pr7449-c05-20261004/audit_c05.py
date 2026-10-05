import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
freeze = json.loads((out / "FREEZE.json").read_text(encoding="utf-8"))
source = (out / "PR-SOURCE-input_owner_v12.py").read_bytes()
test = (out / "FROZEN-C02-test.py").read_bytes()
raw = (out / "RAW.stdout.txt").read_text(encoding="utf-8")
exit_code = int((out / "RAW.exit.txt").read_text(encoding="utf-8"))
current_blob = subprocess.check_output(
    ["git", "rev-parse", f"{freeze['pr_head']}:{freeze['source_path']}"],
    cwd=root, text=True).strip()
checks = {
    "pr_source_snapshot_hash_matches": hashlib.sha256(source).hexdigest() == freeze["source_sha256"],
    "pr_source_blob_matches": current_blob == freeze["source_git_blob"],
    "frozen_c02_test_hash_matches": hashlib.sha256(test).hexdigest() == freeze["frozen_test_sha256"],
    "expected_cancel_cause_failure": "test_cancel_arriving_after_dequeue" in raw and "FAIL: test_cancel_arriving_after_dequeue" in raw and "'release' != 'cancelled'" in raw,
    "ordinary_release_control_passes": "test_ordinary_release_remains_ordinary" in raw and "... ok" in raw,
    "one_expected_failing_case": "Ran 2 tests" in raw and "FAILED (failures=1)" in raw and exit_code == 1,
}
result = {"schema": "map01-v39-cancel-release-cause-pr7449-c05-audit-v1",
          "checks": checks, "pass": all(checks.values()),
          "scope": "source-bound expected defect reproduction; not a candidate PASS"}
(out / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
sys.exit(0 if result["pass"] else 1)
