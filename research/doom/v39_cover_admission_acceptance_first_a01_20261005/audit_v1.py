"""Independent raw/source audit for A01; does not import candidate.py."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
raw = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))
errors = []

for name, key in (("controller_main_c107.py", "main_controller_sha256"),
                  ("controller_pr7589.py", "pr_controller_sha256"),
                  ("wait_test_pr7589.py", "pr_wait_test_sha256")):
    got = hashlib.sha256((ROOT / name).read_bytes()).hexdigest().upper()
    if got != freeze[key]:
        errors.append(f"{name} hash mismatch: {got}")

events = raw.get("events")
if not isinstance(events, list) or [r.get("event") for r in events] != ["accepted", "observation"]:
    errors.append("raw does not contain the frozen accept-then-observation FIFO")
if not events or events[-1].get("sequence") != 9:
    errors.append("hard observation sequence mismatch")
if raw.get("accepted_returned", {}).get("event") != "accepted":
    errors.append("acceptance was not returned first")
if raw.get("monitor_sequences_before_accept_return") != []:
    errors.append("monitor unexpectedly consumed an event before acceptance")
if raw.get("planner_started_before_hard_invalidation_observed") is not True:
    errors.append("planner-start ordering not reproduced")
if raw.get("monitor_sequences_after_next_wait") != [9]:
    errors.append("subsequent monitor observation mismatch")
if raw.get("status") != "FAIL_ACCEPT_THEN_HARD_BEFORE_PLANNER_MONITOR":
    errors.append("candidate disposition mismatch")

source = (ROOT / "controller_pr7589.py").read_text(encoding="utf-8")
tree = ast.parse(source)
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
positions = {}
for n in ast.walk(main):
    if isinstance(n, ast.Call):
        name = n.func.id if isinstance(n.func, ast.Name) else None
        if name in {"submit_cover", "begin_model_turn"} and name not in positions:
            positions[name] = n.lineno
if set(positions) != {"submit_cover", "begin_model_turn"} or positions["submit_cover"] >= positions["begin_model_turn"]:
    errors.append(f"source call order mismatch: {positions}")
if not ("wait_for_cover_acceptance(wait,identifier,validity_monitor)" in
        "".join(source.split())):
    errors.append("initial cover admission helper is not monitor-enabled")
if errors:
    print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
    raise SystemExit(1)
print(json.dumps({
    "status": "PASS_RAW_SOURCE_AUDIT_SCOPED",
    "checks": 10,
    "errors": [],
    "claim": "accept-first hard-health sequence starts planner before the next monitored wait observes invalidation",
    "scope": freeze["scope"]
}, indent=2))
