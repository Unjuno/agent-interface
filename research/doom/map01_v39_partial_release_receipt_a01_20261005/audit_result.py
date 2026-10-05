import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
checked = []


def require(condition, message):
    if not condition:
        raise SystemExit(message)
    checked.append(message)


freeze = json.loads((HERE / "FREEZE.json").read_text())
for relative, expected in freeze["sha256"].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    require(actual == expected, f"source hash mismatch: {relative}")
baseline = ROOT / "research/doom/map01_v39_cancel_release_fix_a01_20261005/input_owner_v13_candidate.py"
candidate = HERE / "input_owner_v13_candidate.py"
require(hashlib.sha256(baseline.read_bytes()).hexdigest() ==
        freeze["baseline_source_sha256"], "baseline source mismatch")
require(hashlib.sha256(candidate.read_bytes()).hexdigest() ==
        freeze["candidate_source_sha256"], "candidate source mismatch")

raw_bytes = (HERE / "raw.json").read_bytes()
raw = json.loads(raw_bytes)
require((HERE / "RED_EXIT.txt").read_text().strip() == "1", "RED exit mismatch")
red = (HERE / "RED_OUTPUT.txt").read_text()
require("AssertionError: 0 != 1" in red, "RED did not show missing partial record")
require((HERE / "GREEN_EXIT.txt").read_text().strip() == "0", "GREEN exit mismatch")
green = (HERE / "GREEN_OUTPUT.txt").read_text()
require("Ran 1 test" in green and "OK" in green and "FAIL" not in green,
        "GREEN output is not a clean one-test pass")

validation = json.loads((HERE / "LOCAL_VALIDATION.json").read_text())
expected_tests = {
    "focused-candidate-normal": 14,
    "focused-candidate-optimized": 14,
    "executor-v12-expiry-composition": 3,
    "owner-compatibility": 10,
    "existing-v39-bridge": 2,
}
require({run["name"] for run in validation["runs"]} == set(expected_tests),
        "local validation inventory mismatch")
for run in validation["runs"]:
    require(run["exit"] == 0, f"local suite failed: {run['name']}")
    output = (HERE / run["output"]).read_text()
    expected_count = expected_tests.get(run["name"])
    if expected_count is not None:
        require(f"Ran {expected_count} test" in output,
                f"wrong test count: {run['name']}")
        require("OK" in output and "FAILED" not in output,
                f"suite output is not green: {run['name']}")

records = raw["owner_release_records"]
emitted = raw["emitted_release_rows"]
require(len(records) == 1, "expected one partial owner release")
record = records[0]
require(record.get("event") == "owner_release" and record.get("verified") is False,
        "partial aggregate record must remain unverified")
require("keys_down" not in record, "partial record fabricated aggregate key state")
require(record.get("release_error_type") == "RuntimeError",
        "partial owner record does not identify its failure class")
rows = record.get("per_key_release_measurements")
require(isinstance(rows, list) and len(rows) == 1, "expected exactly one retained key row")
row = rows[0]
require(row.get("key") == "F8" and row.get("id") == "partial-release"
        and row.get("step") == 10, "retained up lost its admission context")
measurement = row.get("physical_key_measurement", {})
require(measurement.get("classification") == "CONFIRMED_PHYSICAL_UP"
        and measurement.get("identity_status") == "RETIRED",
        "retained row is not the confirmed F8 up")
pre, post = measurement.get("pre_sample", {}), measurement.get("post_sample", {})
require(pre.get("available") is True and pre.get("down") is True
        and post.get("available") is True and post.get("down") is False,
        "physical sample states do not support the confirmed-up label")
times = [pre.get("started_ns"), pre.get("finished_ns"),
         measurement.get("release_request_ns"), measurement.get("sync_return_ns"),
         post.get("started_ns"), post.get("finished_ns")]
require(all(type(value) is int for value in times)
        and times == sorted(times), "per-key timing bracket is incomplete or unordered")
require(measurement.get("bracket", {}).get("physical_up_interval") ==
        [pre["finished_ns"], post["finished_ns"]], "up interval mismatches samples")
require(len(emitted) == 1 and emitted[0] == row,
        "bridge output does not preserve the owner release row")
require(raw["release_exception"] == "injected second key release",
        "original release exception was not preserved")
require(raw["backend_held_after_failure"] == ["F9"]
        and raw["fake_physical_after_failure"] == [75],
        "remaining F9 hold was lost or mislabeled empty")
require(raw["subsequent_down_error"] == "input owner failed closed"
        and raw["injection_count_after_cleanup_failure"] ==
        raw["injection_count_after_rejected_down"],
        "owner admitted a later down after partial cleanup failure")

result = {
    "schema": "v39-partial-release-receipt-audit-v1",
    "result": "PASS_PARTIAL_RECEIPT_CUSTODY",
    "checks": len(checked),
    "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "scope": "one deterministic fake-display two-key cleanup exception schedule",
    "local_validation": expected_tests,
    "unverified": ["real X11", "application consumption", "useful feedback",
                   "bounded recovery", "threat control", "gameplay", "MAP01",
                   "latency", "live allocation"],
}
(HERE / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
