"""Independent v2 raw/source audit; does not import either candidate."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
def audit(raw, freeze, root=ROOT):
    errors = []
    for name, key in (("controller_main_c107.py", "main_controller_sha256"),
                      ("controller_pr7589.py", "pr_controller_sha256"),
                      ("wait_test_pr7589.py", "pr_wait_test_sha256")):
        got = hashlib.sha256((root / name).read_bytes()).hexdigest().upper()
        if got != freeze[key]:
            errors.append(f"{name} hash mismatch: {got}")

    events = raw.get("events")
    if not isinstance(events, list) or [r.get("event") for r in events] != ["accepted", "observation"]:
        errors.append("raw does not contain the frozen accept-then-observation FIFO")
        events = []
    if not events or events[-1].get("sequence") != 9:
        errors.append("hard observation sequence mismatch")
    if events and raw.get("accepted_returned") != events[0]:
        errors.append("acceptance was not returned first")
    if raw.get("latest_observation_at_accept_return") is not None:
        errors.append("latest observation incorrectly claims the later event was seen at acceptance")
    if raw.get("monitor_sequences_at_accept_return") != []:
        errors.append("monitor unexpectedly consumed an event before acceptance")
    if raw.get("planner_started_before_hard_invalidation_observed") is not True:
        errors.append("planner-start ordering not reproduced")
    if raw.get("monitor_sequences_after_next_wait") != [9]:
        errors.append("subsequent monitor observation mismatch")
    if events and raw.get("latest_observation_after_next_wait") != events[-1]:
        errors.append("latest observation after monitored wait mismatch")
    if raw.get("status") != "FAIL_ACCEPT_THEN_HARD_BEFORE_PLANNER_MONITOR":
        errors.append("candidate disposition mismatch")

    source = (root / "controller_pr7589.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    calls = [(n.func.id, n.lineno) for n in ast.walk(main)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id in {"submit_cover", "begin_model_turn"}]
    submit_lines = [line for name, line in calls if name == "submit_cover"]
    planner_lines = [line for name, line in calls if name == "begin_model_turn"]
    if not submit_lines or not planner_lines or min(submit_lines) >= min(planner_lines):
        errors.append(f"source call order mismatch: {calls}")
    if not ("wait_for_cover_acceptance(wait,identifier,validity_monitor)" in
            "".join(source.split())):
        errors.append("initial cover admission helper is not monitor-enabled")
    return errors


freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
raw = json.loads((ROOT / "raw_v2.json").read_text(encoding="utf-8"))
errors = audit(raw, freeze)

if errors:
    print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
    raise SystemExit(1)
print(json.dumps({
    "status": "PASS_RAW_SOURCE_AUDIT_SCOPED",
    "checks": 12,
    "errors": [],
    "claim": "accept-first hard-health sequence starts planner before the next monitored wait observes invalidation",
    "scope": freeze["scope"]
}, indent=2))
