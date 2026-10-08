#!/usr/bin/env python3
"""Independent audit of the one-shot T2c trace and both earlier STOPs."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_inventory_auditor():
    spec = importlib.util.spec_from_file_location("t2b_independent_auditor", ROOT / "independent_audit_v2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_v1_stop(inventory):
    r = json.loads((ROOT / "candidate.preflight_stop.raw.json").read_text(encoding="utf-8"))
    return r.get("status") == "STOP_CANDIDATE_PREFLIGHT_INVENTORY_PREDICATE" and r.get("tar_members_total") == inventory["tar_member_count"] and r.get("regular_files") == inventory["regular_file_count"] and r.get("x_test_events_dispatched") == 0 and r.get("run_directory_created") is False


def audit_v2_stop():
    candidate = json.loads((ROOT / "candidate.v2.raw.json").read_text(encoding="utf-8"))
    t = ROOT / "run_v2" / "trace"
    app = jsonl(t / "tk" / "app_events.jsonl")
    obs = jsonl(t / "observer_events.jsonl")
    driver = jsonl(t / "actions.jsonl")
    run = json.loads((t / "run.raw.json").read_text(encoding="utf-8"))
    ok = (
        candidate.get("runner", {}).get("status") == "STOP"
        and run.get("status") == "STOP"
        and any(r.get("kind") == "arm_ack" for r in app)
        and any(r.get("kind") == "arm_ack" for r in obs)
        and not any(r.get("source") == "app" for r in app)
        and not any(r.get("source") == "observer" for r in obs)
        and not any(r.get("phase") == "dispatch_request" for r in driver)
        and candidate.get("runner_stderr_tail") == ""
    )
    return ok, {"app_ack_count": sum(r.get("kind") == "arm_ack" for r in app), "observer_ack_count": sum(r.get("kind") == "arm_ack" for r in obs), "dispatch_count": sum(r.get("phase") == "dispatch_request" for r in driver), "app_log_actual_path": "run_v2/trace/tk/app_events.jsonl"}


def audit_v3(candidate, trace):
    errors = []
    app = jsonl(trace / "tk" / "app_events.jsonl")
    obs = jsonl(trace / "observer_events.jsonl")
    actions = jsonl(trace / "actions.jsonl")
    run = json.loads((trace / "run.raw.json").read_text(encoding="utf-8"))
    if candidate.get("app_rows") != app or candidate.get("observer_rows") != obs or candidate.get("driver_rows") != actions:
        errors.append("candidate-v3 summary disagrees with retained raw streams")
    if run.get("status") != "RUN_COMPLETE" or run.get("terminal_shift_down") is not False:
        errors.append("run did not finish with neutral terminal keymap")
    if run.get("app_returncode") != 0 or run.get("observer_returncode") != 0:
        errors.append("fixture processes did not exit successfully")
    ae = [r for r in app if r.get("source") == "app"]
    oe = [r for r in obs if r.get("source") == "observer"]
    if len(ae) != 2 or len(oe) != 2:
        errors.append("expected exactly two app and two observer key events")
    if [r.get("source_seq") for r in ae] != [1, 2]:
        errors.append("app event sequence is not [1,2]")
    oseq = [r.get("source_seq") for r in oe]
    if oseq != sorted(set(oseq)) or len(oseq) != 2:
        errors.append("observer event sequence is not strictly increasing")
    if len({r.get("event_id") for r in ae}) != 2 or len({r.get("event_id") for r in oe}) != 2:
        errors.append("source-local event ids are not unique")
    for kind, suffix in (("KeyPress", "shift-1"), ("KeyRelease", "shift-2")):
        ids = {r.get("actuation_id") for r in actions if r.get("actuation_id", "").endswith(suffix)}
        if len(ids) != 1:
            errors.append(f"driver ID missing/ambiguous for {suffix}")
            continue
        act_id = next(iter(ids))
        stages = [r.get("phase") for r in actions if r.get("actuation_id") == act_id]
        if stages != ["arm_request", "both_armed", "dispatch_request", "dispatch_sync_complete"]:
            errors.append(f"driver stage sequence invalid for {act_id}")
        app_rows = [r for r in app if r.get("actuation_id") == act_id]
        obs_rows = [r for r in obs if r.get("actuation_id") == act_id]
        app_acks = [i for i, r in enumerate(app) if r.get("kind") == "arm_ack" and r.get("actuation_id") == act_id]
        obs_acks = [i for i, r in enumerate(obs) if r.get("kind") == "arm_ack" and r.get("actuation_id") == act_id]
        if len(app_rows) != 1 or len(obs_rows) != 1 or len(app_acks) != 1 or len(obs_acks) != 1:
            errors.append(f"missing/duplicate ack or event for {act_id}")
            continue
        a, o = app_rows[0], obs_rows[0]
        if app_acks[0] >= app.index(a) or obs_acks[0] >= obs.index(o):
            errors.append(f"arm ack not earlier in stream order for {act_id}")
        if a.get("kind") != kind or o.get("kind") != kind:
            errors.append(f"event kind mismatch for {act_id}")
        if a.get("keycode") != o.get("keycode") or a.get("x_time") != o.get("x_time"):
            errors.append(f"X event identity differs across streams for {act_id}")
        parent = [f"act:{act_id}"]
        if a.get("causal_parent_ids") != parent or o.get("causal_parent_ids") != parent:
            errors.append(f"explicit parent edge missing for {act_id}")
        if a.get("event_id") == o.get("event_id"):
            errors.append(f"event ids are not distinct by source for {act_id}")
        if o.get("epoch") != run.get("epoch") or not act_id.startswith(run.get("epoch", "") + ":"):
            errors.append(f"observer epoch binding mismatch for {act_id}")
        dispatch = [r for r in actions if r.get("phase") == "dispatch_request" and r.get("actuation_id") == act_id]
        if len(dispatch) != 1 or dispatch[0].get("event_kind") != kind or dispatch[0].get("keycode") != a.get("keycode"):
            errors.append(f"captured record disagrees with dispatch receipt for {act_id}")
    if any("mono_ns" not in r for r in app + obs + actions):
        errors.append("diagnostic monotonic fields absent")
    return errors, app, obs, actions, run


def main():
    freeze = json.loads((ROOT / "FREEZE_V3.json").read_text(encoding="utf-8"))
    source_auditor = load_inventory_auditor()
    inventory = source_auditor.source_inventory(freeze)
    stop1_ok = audit_v1_stop(inventory)
    stop2_ok, stop2 = audit_v2_stop()
    errors = []
    if not inventory["parts_match"] or not inventory["archive_match"] or not inventory["counts_match"] or not all(inventory["upstream_source_matches"].values()):
        errors.append("frozen upstream archive/inventory/source audit failed")
    if not stop1_ok:
        errors.append("T2 initial preflight STOP does not match archive counts")
    if not stop2_ok:
        errors.append("T2b no-dispatch STOP not independently confirmed")
    candidate_path = ROOT / "candidate.v3.raw.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    trace_errors, app, obs, actions, run = audit_v3(candidate, ROOT / "run_v3" / "trace")
    errors.extend(trace_errors)
    if candidate.get("disposition") != "PASS_PROSPECTIVE_CAUSAL_IDS":
        errors.append("T2c candidate did not pass")
    result = {
        "schema": "blackstart-prospective-trace-independent-audit-v3",
        "status": "PASS_AUDIT_PROSPECTIVE_CAUSAL_IDS" if not errors else "FAIL_OR_STOP_AUDIT",
        "errors": errors,
        "t2_stop_verified": stop1_ok,
        "t2b_stop_verified": stop2_ok,
        "t2b_partial_evidence": stop2,
        "archive_inventory": inventory,
        "candidate_v3_sha256": sha(candidate_path.read_bytes()),
        "candidate_v3_disposition": candidate.get("disposition"),
        "app_tagged_events": len([r for r in app if r.get("source") == "app"]),
        "observer_tagged_events": len([r for r in obs if r.get("source") == "observer"]),
        "driver_rows": len(actions),
        "neutral_terminal_keymap": run.get("terminal_shift_down") is False,
        "timestamps_used_to_infer_causality": False,
    }
    (ROOT / "audit.v3.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_AUDIT_PROSPECTIVE_CAUSAL_IDS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
