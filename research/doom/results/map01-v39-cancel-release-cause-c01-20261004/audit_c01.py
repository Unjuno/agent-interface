import hashlib
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[4]
base = Path(__file__).resolve().parent
freeze = json.loads((base / "FREEZE.json").read_text(encoding="utf-8"))
raw = (base / "RED-01.stdout.txt").read_text(encoding="utf-8")
exit_code = int((base / "RED-01.exit.txt").read_text(encoding="utf-8"))
checks = {
    "freeze_source_hash_matches": hashlib.sha256((root / freeze["source"]).read_bytes()).hexdigest() == freeze["source_sha256"],
    "freeze_test_hash_matches": hashlib.sha256((root / freeze["test"]).read_bytes()).hexdigest() == freeze["test_sha256"],
    "red_exit_one": exit_code == 1,
    "cancel_case_fails_for_expected_reason": "AssertionError: 'release' != 'cancelled'" in raw,
    "ordinary_release_control_passes": "test_ordinary_release_remains_ordinary (__main__.CancellationReleaseCauseTests.test_ordinary_release_remains_ordinary) ... ok" in raw,
    "verified_release_assertion_not_the_failing_assertion": "self.assertTrue(receipt[\"verified\"])" not in raw,
    "both_cases_executed": "Ran 2 tests" in raw,
}
result = {"schema": "v39-cancel-release-cause-c01-audit-v1", "checks": checks,
          "pass": all(checks.values()), "scope": "frozen source/test hashes and saved host raw output only"}
(base / "AUDIT-01.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
sys.exit(0 if result["pass"] else 1)
