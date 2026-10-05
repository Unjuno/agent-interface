"""Independent v4 audit with seeded prior observation and Git blob checks."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def audit(raw, freeze, root=ROOT):
    errors = []
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    files = (("controller_main_c107.py", "main_controller_sha256", "main_controller_blob"),
             ("wait_test_main_c107.py", "main_wait_test_sha256", "main_wait_test_blob"),
             ("controller_pr7589.py", "pr_controller_sha256", "pr_controller_blob"),
             ("wait_test_pr7589.py", "pr_wait_test_sha256", "pr_wait_test_blob"))
    for name, sha_key, blob_key in files:
        data = (root / name).read_bytes()
        got = hashlib.sha256(data).hexdigest().upper()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        check(got == freeze[sha_key], f"{name} SHA-256 mismatch: {got}")
        check(blob == freeze[blob_key], f"{name} Git blob mismatch: {blob}")

    events = raw.get("events")
    check(isinstance(events, list) and [r.get("event") for r in events] ==
          ["observation", "accepted", "observation"],
          "raw FIFO order is not baseline, accepted, hard observation")
    check(bool(events) and events[0].get("sequence") == 8 and
          events[-1].get("sequence") == 9, "baseline/hard observation identity mismatch")
    if not isinstance(events, list) or len(events) != 3:
        events = []
    expected = {"current_main": "controller_main_c107.py",
                "pr_7589": "controller_pr7589.py"}
    cases = raw.get("cases", {})
    for key, source_name in expected.items():
        case = cases.get(key, {})
        check(case.get("source") == source_name, f"{key} source identity mismatch")
        check(bool(events) and case.get("accepted_returned") == events[1],
              f"{key} did not return the accepted event")
        check(bool(events) and case.get("latest_at_accept_return") == events[0],
              f"{key} did not retain the prior observation at acceptance")
        expected_seen = [8] if key == "pr_7589" else []
        check(case.get("monitor_sequences_at_accept_return") == expected_seen,
              f"{key} monitor sequence at acceptance mismatch")
        check(case.get("planner_started_before_invalidation_observed") is True,
              f"{key} planner did not start before hard-event observation")
        expected_after = [8, 9] if key == "pr_7589" else [9]
        check(case.get("monitor_sequences_after_next_wait") == expected_after,
              f"{key} next-wait monitor sequence mismatch")
        check(case.get("invalidation", {}).get("reason") == "hard_health_loss",
              f"{key} invalidation reason mismatch")
        check(bool(events) and case.get("latest_after_next_wait") == events[-1],
              f"{key} latest observation after next wait mismatch")
    check(raw.get("status") == "FAIL_ACCEPT_THEN_HARD_BEFORE_PLANNER_MONITOR",
          "candidate status mismatch")

    for label, filename in expected.items():
        source = (root / filename).read_text(encoding="utf-8")
        tree = ast.parse(source)
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        body = list(ast.walk(main))
        calls = [n for n in body if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        submit_lines = [n.lineno for n in calls if n.func.id == "submit_cover"]
        planner_lines = [n.lineno for n in calls if n.func.id == "begin_model_turn"]
        monitored_wait_lines = [n.lineno for n in calls if n.func.id == "wait" and
                                any(k.arg == "observation_monitor" for k in n.keywords)]
        check(bool(submit_lines) and bool(planner_lines) and
              min(submit_lines) < min(planner_lines), f"{label} submit/planner order mismatch")
        check(bool(monitored_wait_lines) and min(planner_lines) < min(monitored_wait_lines),
              f"{label} monitored wait does not follow planner start")
        submit_fn = next(n for n in body if isinstance(n, ast.FunctionDef) and
                         n.name == "submit_cover")
        submit_calls = [n for n in ast.walk(submit_fn) if isinstance(n, ast.Call)]
        monitored_admission = any(
            (isinstance(n.func, ast.Name) and n.func.id == "wait_for_cover_acceptance") or
            any(k.arg == "observation_monitor" for k in n.keywords)
            for n in submit_calls)
        check(monitored_admission == (label == "pr_7589"),
              f"{label} admission-monitor wiring differs from expected source")
        compact = "".join(source.split())
        source_input = compact.find("action_source_observation=dict(latest)")
        planner_start = compact.find("planner_handle=begin_model_turn(")
        check(source_input >= 0 and planner_start > source_input,
              f"{label} planner does not use latest observation before turn start")
    return errors, checks


freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
raw = json.loads((ROOT / "raw_v4.json").read_text(encoding="utf-8"))
errors, checks = audit(raw, freeze)
if errors:
    print(json.dumps({"status": "FAIL", "checks": checks, "errors": errors}, indent=2))
    raise SystemExit(1)
print(json.dumps({
    "status": "PASS_RAW_SOURCE_AUDIT_SCOPED",
    "checks": checks,
    "errors": [],
    "claim": "with a seeded prior observation, both current main and PR #7589 start the planner before the next monitored wait consumes the accept-following hard observation",
    "scope": freeze["scope"]
}, indent=2))
