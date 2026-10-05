"""Read-only replacement audit; original v1 and all original results stay frozen."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FREEZE_PATH = HERE / "EXECUTOR_V12_CURRENT_MAIN_FREEZE.json"
freeze = json.loads(FREEZE_PATH.read_text())
checks = []


def require(ok, message):
    if not ok:
        raise SystemExit(message)
    checks.append(message)


# Verify the historical c1074 record against committed snapshots, without
# fetching Git objects, consulting a moving origin/main, or changing old outputs.
lock = json.loads((HERE / "EXECUTOR_V12_SOURCE_LOCK.json").read_text())
snapshot_paths = dict(lock["snapshot_paths"])
snapshot_paths[freeze["test"]] = str(
    (HERE / "frozen_live_control/test_executor_v12_c1074.py.txt").relative_to(ROOT))
for relative, expected in freeze["sha256"].items():
    source = ROOT / snapshot_paths.get(relative, relative)
    require(source.is_file(), f"frozen source is retained: {relative}")
    require(hashlib.sha256(source.read_bytes()).hexdigest() == expected,
            f"source matches the historical freeze: {relative}")
for relative, expected in lock["snapshot_sha256"].items():
    source = HERE / "frozen_live_control" / relative
    require(hashlib.sha256(source.read_bytes()).hexdigest() == expected,
            f"frozen transitive dependency matches: {relative}")

raw_path = HERE / freeze["raw_file"]
raw_bytes = raw_path.read_bytes()
result = json.loads((HERE / freeze["result_file"]).read_text())
raw = json.loads(raw_bytes)
require(hashlib.sha256(raw_bytes).hexdigest() == result["raw_sha256"],
        "raw artifact hash matches result record")
partial = raw["partial_owner_release"]
require(partial.get("verified") is False
        and partial.get("release_error_type") == "RuntimeError",
        "partial owner record remains unverified and labeled")
require([(r.get("key"), r.get("step"))
         for r in partial["per_key_release_measurements"]] == [("F8", 4)],
        "partial record retains only the confirmed F8 prefix")
require(raw["key_release_attempts"] == [74, 75, 75],
        "F9 is retried exactly once by terminal cleanup")
require([(r.get("key"), r.get("step")) for r in raw["release_measurements"]]
        == [("F8", 4), ("F9", 5)],
        "bridge retains both contextual release receipts")
require(all(r["physical_key_measurement"]["classification"] ==
            "CONFIRMED_PHYSICAL_UP" for r in raw["release_measurements"]),
        "both retained rows carry confirmed per-key classifications")
positions = [i for i, event in enumerate(raw["event_order"])
             if event == "input_release_measurement"]
require(len(positions) == 2 and
        positions[-1] < raw["event_order"].index("terminal"),
        "both up receipts precede terminal publication")
require(raw["terminal"]["status"] == "expired"
        and raw["terminal"]["release"]["verified"] is True,
        "terminal reports verified neutral recovery")
require(raw["fake_physical_after_terminal"] == []
        and raw["bridge_held_after_terminal"] == [],
        "fake physical and bridge held sets are empty")
require(raw["later_down_rejected"] is True
        and raw["injections_before_rejected_down"] ==
        raw["injections_after_rejected_down"],
        "later down is rejected without injection")
output = (HERE / freeze["output_file"]).read_text()
require(hashlib.sha256(output.encode()).hexdigest() == result["output_sha256"],
        "runner output hash matches result record")
require("Ran 1 test" in output and "OK" in output and "FAILED" not in output,
        "current-main revalidation test output is green")
require((HERE / freeze["exit_file"]).read_text().strip() == "0",
        "current-main revalidation exit code is zero")
require(result["exit_code"] == 0, "result records zero runner exit")

audit = {
    "schema": "v39-executor-v12-retained-c1074-audit-v2",
    "result": "PASS_RETAINED_C1074_SOURCE_AND_RAW",
    "checks": len(checks),
    "main_commit": freeze["main_commit"],
    "current_main_continuity_checked": False,
    "candidate_rerun": False,
    "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "scope": "historical c1074 fake-display composition; frozen source/raw consistency only",
    "unverified": ["real X11", "application effect", "live control", "recovery efficacy"],
}
print(json.dumps(audit, sort_keys=True))
