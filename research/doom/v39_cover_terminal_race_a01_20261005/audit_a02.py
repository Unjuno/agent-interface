import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE_A01.json").read_text(encoding="utf-8"))
REPLAY_FREEZE = json.loads((ROOT / "REPLAY_FREEZE.json").read_text(encoding="utf-8"))
repo = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
                     check=True, capture_output=True, text=True).stdout.strip()
source_path = "research/doom/map01_overlap_controller_v39.py"
source_blob = subprocess.run(["git", "show", f"{FREEZE['source_commit']}:{source_path}"],
                             cwd=repo, check=True, capture_output=True).stdout
original_probe = (ROOT / "probe_as_run.py").read_bytes()
original = json.loads((ROOT / "result_a01.json").read_text(encoding="utf-8"))
reproduce_bytes = (ROOT / "reproduce.py").read_bytes()
reproduction = json.loads((ROOT / "reproduction_a01.json").read_text(encoding="utf-8"))
current_source = (ROOT.parent / "map01_overlap_controller_v39.py").read_text(encoding="utf-8")

checks = []
def check(condition, name):
    if not condition: raise AssertionError(name)
    checks.append(name)

check(hashlib.sha256(source_blob).hexdigest() == FREEZE["source_sha256"], "frozen base source blob hash")
check(hashlib.sha256(original_probe).hexdigest() == FREEZE["probe_sha256"], "as-run probe source hash")
check(hashlib.sha256(reproduce_bytes).hexdigest() == REPLAY_FREEZE["reproduction_sha256"], "portable replay source hash")
check(REPLAY_FREEZE["source_commit"] == FREEZE["source_commit"], "replay uses same frozen source commit")
check(reproduction["source_sha256"] == FREEZE["source_sha256"], "replay source hash recorded")
check(reproduction["reproduction_sha256"] == REPLAY_FREEZE["reproduction_sha256"], "replay result binds portable script")
check(hashlib.sha256((ROOT / "result_a01.json").read_bytes()).hexdigest()
      == json.loads((ROOT / "audit_a01.json").read_text(encoding="utf-8"))["result_sha256"],
      "initial raw result hash matches its audit")

expected = {
    "cancelled_neutral": ("accepted", "accepted"),
    "completed_neutral": ("raised", "accepted"),
    "completed_nonempty": ("raised", "raised"),
    "failed_neutral": ("raised", "raised"),
}
def audit_cases(result, *, portable):
    rows = {item["case"]: item for item in result["cases"]}
    check(set(rows) == set(expected), "case set retained" + (" replay" if portable else " initial"))
    for case, outcomes in expected.items():
        row = rows[case]
        for arm, want in zip(("baseline", "candidate"), outcomes):
            observed = row[arm]["result"]["outcome"] if not portable else row[arm]["outcome"]["outcome"]
            check(observed == want, f"{case} {arm} outcome" + (" replay" if portable else " initial"))
            ops = [entry["event"] for entry in row[arm]["operations"]]
            check(ops == ["interrupt", "write", "flush", "wait"], f"{case} {arm} operation order")
            payload = json.loads(row[arm]["operations"][1]["value"])
            check(payload == {"op": "cancel", "id": "cover-race"}, f"{case} {arm} matched cancellation ID")

audit_cases(original, portable=False)
audit_cases(reproduction, portable=True)
check('terminal.get("status") not in ("cancelled", "completed", "expired")' in current_source,
      "current implementation accepts only cancel/complete/expire terminals before empty-release gate")
check('release.get("verified") is not True' in current_source
      and 'release.get("buttons_down") != []' in current_source
      and 'release.get("keys_down") != []' in current_source,
      "current implementation still requires verified empty keyboard and buttons")

# Result-level mutation controls reject the unsafe promotions and the original regression.
controls = {}
for name, case, arm in (
    ("promote_nonempty", "completed_nonempty", "candidate"),
    ("promote_failed", "failed_neutral", "candidate"),
    ("hide_regression", "completed_neutral", "baseline"),
):
    mutated = json.loads(json.dumps(reproduction))
    target = next(row for row in mutated["cases"] if row["case"] == case)
    target[arm]["outcome"]["outcome"] = "accepted"
    want = expected[case][0 if arm == "baseline" else 1]
    controls[name] = target[arm]["outcome"]["outcome"] != want
    check(controls[name], f"mutation control {name} detected")

report = {
    "schema": "v39-cover-terminal-race-audit-a02-v1",
    "checks_passed": len(checks),
    "checks": checks,
    "mutation_controls_detected": controls,
    "disposition": "NARROW_CONTROLLER_LIVENESS_RACE_REPRODUCED; VERIFIED_EMPTY_COMPLETED_TERMINAL_ACCEPTED; NONEMPTY_OR_FAILED_TERMINALS_STILL_REJECTED",
    "limitations": ["AST helper and test doubles only", "does not measure race frequency or live-game effect"],
}
(ROOT / "audit_a02.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"schema": report["schema"], "checks_passed": report["checks_passed"],
                  "mutation_controls_detected": controls,
                  "disposition": report["disposition"]}, indent=2))
