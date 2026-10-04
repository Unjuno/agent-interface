import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
freeze = json.loads((out / "FREEZE.json").read_text(encoding="utf-8"))
cause_raw = (out / "CAUSE.stdout.txt").read_text(encoding="utf-8")
integrated_raw = (out / "INTEGRATION.stdout.txt").read_text(encoding="utf-8")
cause_exit = int((out / "CAUSE.exit.txt").read_text(encoding="utf-8"))
integrated_exit = int((out / "INTEGRATION.exit.txt").read_text(encoding="utf-8"))
candidate = (root / "research/live_control/input_owner_v12.py").read_bytes().replace(b"\r\n", b"\n")
before = (root / "research/doom/results/map01-v39-cancel-release-cause-pr7449-c05-20261004/PR-SOURCE-input_owner_v12.py").read_bytes().replace(b"\r\n", b"\n")
old = b"                        result = release(op)"
new = (b"                        reason = ('cancelled' if op == 'release' and active is lease and lease is not None and lease.cancel.is_set() else op)\n"
       b"                        result = release(reason)")
checks = {
    "all_frozen_sources_match": all(
        hashlib.sha256((root / path).read_bytes()).hexdigest() == digest
        for path, digest in freeze["source_sha256"].items()),
    "all_frozen_tests_match": all(
        hashlib.sha256((root / path).read_bytes()).hexdigest() == digest
        for path, digest in freeze["test_sha256"].items()),
    "candidate_is_exact_one_delta_from_pr7449_source": candidate.replace(new, old, 1) == before and candidate.count(new) == 1,
    "cause_test_both_cases_pass": cause_exit == 0 and "test_cancel_arriving_after_dequeue_is_preserved_as_release_cause (__main__.CancellationReleaseCauseTests.test_cancel_arriving_after_dequeue_is_preserved_as_release_cause) ... ok" in cause_raw and "test_ordinary_release_remains_ordinary (__main__.CancellationReleaseCauseTests.test_ordinary_release_remains_ordinary) ... ok" in cause_raw and "Ran 2 tests" in cause_raw and cause_raw.rstrip().endswith("OK"),
    "integrated_executor_test_passes": integrated_exit == 0 and "test_cancelled_release_is_published_before_terminal" in integrated_raw and "Ran 1 test" in integrated_raw and integrated_raw.rstrip().endswith("OK"),
    "pre_fix_reproduction_audit_passes": json.loads((root / "research/doom/results/map01-v39-cancel-release-cause-pr7449-c05-20261004/AUDIT.json").read_text(encoding="utf-8"))["pass"] is True,
}
result = {"schema": "map01-v39-cancel-release-cause-pr7449-c06-audit-v1",
          "checks": checks, "pass": all(checks.values()),
          "scope": "versioned owner candidate and fake-Xlib ExecutorV12 integration only"}
(out / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
sys.exit(0 if result["pass"] else 1)
