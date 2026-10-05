import hashlib
import json
import subprocess
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


require(subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT,
                                text=True).strip() == freeze["main_commit"],
        "current main commit matches freeze")
for relative, expected in freeze["sha256"].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    require(actual == expected, f"source hash matches: {relative}")
    if relative in freeze["main_sources"]:
        blob = subprocess.check_output(["git", "show", f"origin/main:{relative}"],
                                       cwd=ROOT)
        require(hashlib.sha256(blob).hexdigest() == expected,
                f"source matches frozen current main: {relative}")

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
    "schema": "v39-executor-v12-current-main-audit-v1",
    "result": "PASS_CURRENT_MAIN_SOURCE_AND_COMPOSITION_REVALIDATION",
    "checks": len(checks),
    "main_commit": freeze["main_commit"],
    "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "scope": "same deterministic fake-display composition, exact current-main ExecutorV12 closure",
    "unverified": ["real X11", "application effect", "live control", "recovery efficacy"],
}
(HERE / freeze["audit_file"]).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
print(json.dumps(audit, sort_keys=True))
