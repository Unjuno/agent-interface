import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def check(condition, message):
    if not condition:
        raise SystemExit(message)


lock = json.loads((HERE / "EXECUTOR_V12_SOURCE_LOCK.json").read_text())
for relative, expected in lock["sha256"].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    check(actual == expected, f"source hash mismatch: {relative}")

raw = json.loads((HERE / "executor-v12-partial-release-raw.json").read_text())
partial = raw["partial_owner_release"]
check(partial["verified"] is False, "partial aggregate release was marked verified")
check(partial["release_error_type"] == "RuntimeError", "wrong partial failure class")
rows = partial["per_key_release_measurements"]
check([(row["key"], row["step"]) for row in rows] == [("F8", 4)],
      "partial record did not retain exactly the F8 prefix")
check([row["key"] for row in raw["release_measurements"]] == ["F8", "F9"],
      "bridge did not publish both confirmed UP receipts")
check([row["physical_key_measurement"]["classification"]
       for row in raw["release_measurements"]] ==
      ["CONFIRMED_PHYSICAL_UP", "CONFIRMED_PHYSICAL_UP"],
      "release rows lack confirmed per-key state")
check(raw["key_release_attempts"] == [74, 75, 75],
      "second key was not retried exactly once at terminal cleanup")
release_positions = [i for i, name in enumerate(raw["event_order"])
                     if name == "input_release_measurement"]
check(len(release_positions) == 2
      and release_positions[-1] < raw["event_order"].index("terminal"),
      "both release receipts did not precede terminal publication")
check(raw["terminal"]["status"] == "expired"
      and raw["terminal"]["release"]["verified"] is True,
      "terminal did not reflect verified recovery")
check(raw["fake_physical_after_terminal"] == []
      and raw["bridge_held_after_terminal"] == [],
      "terminal recovery left held input in the harness")
check(raw["later_down_rejected"] is True
      and raw["injections_before_rejected_down"] ==
      raw["injections_after_rejected_down"],
      "owner admitted input after its cleanup fault")
check((HERE / "EXECUTOR_V12_RED_EXIT.txt").read_text().strip() == "1",
      "baseline RED exit mismatch")
red = (HERE / "EXECUTOR_V12_RED.txt").read_text()
check("AssertionError: 0 != 1" in red, "baseline did not expose missing partial record")
for suffix in ("GREEN", "GREEN_OPT"):
    check((HERE / f"EXECUTOR_V12_{suffix}_EXIT.txt").read_text().strip() == "0",
          f"{suffix} exit mismatch")
    output = (HERE / f"EXECUTOR_V12_{suffix}.txt").read_text()
    check("Ran 1 test" in output and "OK" in output and "FAILED" not in output,
          f"{suffix} output is not a clean one-test pass")

print(json.dumps({
    "result": "PASS_EXECUTOR_V12_PARTIAL_RELEASE_COMPOSITION",
    "checks": 20,
    "raw_sha256": hashlib.sha256(
        (HERE / "executor-v12-partial-release-raw.json").read_bytes()).hexdigest(),
    "scope": "one fake-display expiry cleanup exception with one successful terminal retry",
    "unverified": ["real X11", "application effect", "live control", "recovery efficacy"],
}, sort_keys=True))
