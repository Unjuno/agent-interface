"""Read-only audit of the retained V10 failed-release admission matrix."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
checks = []
for variant in ("baseline", "candidate"):
    for filename in ("input_owner_v10.py", "test_input_owner_v10_release_retry.py"):
        content = (ROOT / "source" / variant / filename).read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        checks.append(actual == freeze["sources"][variant][filename])
checks.append(
    (ROOT / "source/baseline/test_input_owner_v10_release_retry.py").read_bytes()
    == (ROOT / "source/candidate/test_input_owner_v10_release_retry.py").read_bytes()
)
test_source = (ROOT / "source/candidate/test_input_owner_v10_release_retry.py").read_text()
checks.extend(token in test_source for token in (
    "test_unverified_release_blocks_a_new_lease_admission",
    'assertRaisesRegex(ValueError, "another intent owns input")',
    "self.assertEqual(self.display.keys, {65})",
    "self.assertNotIn(66, self.display.keys)",
))
for variant in ("baseline", "candidate"):
    for mode in ("normal", "optimized"):
        path = ROOT / "results" / f"{variant}-{mode}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        checks.extend((record["variant"] == variant, record["mode"] == mode))
        stream = record["stdout"] + record["stderr"]
        checks.append("test_unverified_release_blocks_a_new_lease_admission" in stream)
        checks.append(
            "test_unverified_release_blocks_a_new_lease_admission" in stream
            and "... ok" in stream.split(
                "test_unverified_release_blocks_a_new_lease_admission", 1
            )[1].splitlines()[0]
        )
        if variant == "candidate":
            checks.extend((record["exit_code"] == 0, "Ran 4 tests" in stream,
                           "OK" in stream))
        else:
            checks.extend((record["exit_code"] == 1, "Ran 4 tests" in stream,
                           "FAILED (failures=1, errors=1)" in stream,
                           "test_cleanup_retries_a_key_still_down_after_explicit_up" in stream,
                           "test_cleanup_retries_a_wheel_release_omitted_by_server" in stream))
checks.append("fake-X" in (ROOT / "README.md").read_text(encoding="utf-8"))
result = {"checks": len(checks), "passed": sum(checks),
          "status": "PASS" if all(checks) else "FAIL",
          "scope": "source and raw-output integrity; no live-game claim"}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks) else 1)
