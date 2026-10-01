#!/usr/bin/env python3
"""Audit the actual T2c fail-closed outcome; accepts the preregistered HOLD."""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def module(path):
    spec = importlib.util.spec_from_file_location("audit_source_inventory", ROOT / path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def audit():
    audit_freeze = json.loads((ROOT / "AUDIT_FREEZE_V3.json").read_text(encoding="utf-8"))
    frozen_inputs = {}
    for rel, expected in audit_freeze["input_sha256"].items():
        actual = digest((ROOT / rel).read_bytes())
        frozen_inputs[rel] = actual == expected
    freeze = json.loads((ROOT / "FREEZE_V3.json").read_text(encoding="utf-8"))
    frozen_sources = {rel: digest((ROOT / rel).read_bytes()) == expected for rel, expected in freeze["analysis_sources_sha256"].items()}
    frozen_prior = {rel: digest((ROOT / rel).read_bytes()) == expected for rel, expected in freeze["prior_artifacts_sha256"].items()}
    prior_auditor = module("independent_audit_v2.py")
    inventory = prior_auditor.source_inventory(freeze)
    candidate = json.loads((ROOT / "candidate.v3.raw.json").read_text(encoding="utf-8"))
    trace = ROOT / "run_v3" / "trace"
    app = rows(trace / "tk" / "app_events.jsonl")
    observer = rows(trace / "observer_events.jsonl")
    actions = rows(trace / "actions.jsonl")
    run = json.loads((trace / "run.raw.json").read_text(encoding="utf-8"))
    errors = []

    if digest((ROOT / "independent_audit_hold.py").read_bytes()) != audit_freeze["auditor_sha256"]:
        errors.append("independent auditor source changed after freeze")
    if not all(frozen_inputs.values()) or not all(frozen_sources.values()) or not all(frozen_prior.values()):
        errors.append("one or more frozen audit inputs changed")
    if not inventory["parts_match"] or not inventory["archive_match"] or not inventory["counts_match"] or not all(inventory["upstream_source_matches"].values()):
        errors.append("upstream archive/source integrity did not independently verify")
    stop1 = json.loads((ROOT / "candidate.preflight_stop.raw.json").read_text(encoding="utf-8"))
    stop1_ok = stop1.get("tar_members_total") == inventory["tar_member_count"] and stop1.get("regular_files") == inventory["regular_file_count"] and stop1.get("x_test_events_dispatched") == 0 and stop1.get("run_directory_created") is False
    stop2 = json.loads((ROOT / "candidate.v2.raw.json").read_text(encoding="utf-8"))
    trace2 = ROOT / "run_v2" / "trace"
    app2 = rows(trace2 / "tk" / "app_events.jsonl")
    obs2 = rows(trace2 / "observer_events.jsonl")
    act2 = rows(trace2 / "actions.jsonl")
    stop2_ok = stop2.get("runner", {}).get("status") == "STOP" and any(r.get("kind") == "arm_ack" for r in app2) and any(r.get("kind") == "arm_ack" for r in obs2) and not any(r.get("phase") == "dispatch_request" for r in act2) and not any(r.get("source") == "app" for r in app2) and not any(r.get("source") == "observer" for r in obs2)
    if not stop1_ok:
        errors.append("first inventory-preflight STOP not supported by archive counts")
    if not stop2_ok:
        errors.append("second runner STOP did not fail before XTest dispatch")

    if candidate.get("app_rows") != app or candidate.get("observer_rows") != observer or candidate.get("driver_rows") != actions:
        errors.append("candidate-v3 summary differs from raw JSONL")
    if run.get("status") != "STOP" or run.get("error") != "TimeoutError" or candidate.get("runner_returncode") != 2:
        errors.append("T2c runner failure was not an observer/event collection timeout")
    if candidate.get("disposition") != "HOLD_INCOMPLETE_OR_NONNEUTRAL":
        errors.append("candidate did not fail closed on the missing observer record")

    app_ack = [r for r in app if r.get("kind") == "arm_ack" and r.get("consumer") == "app"]
    obs_ack = [r for r in observer if r.get("kind") == "arm_ack" and r.get("consumer") == "observer"]
    app_events = [r for r in app if r.get("source") == "app"]
    obs_events = [r for r in observer if r.get("source") == "observer"]
    if len(app_ack) != 1 or len(obs_ack) != 1 or len(app_events) != 1 or len(obs_events) != 0:
        errors.append("raw logs do not show the expected two acks / app-only KeyPress")
    dispatch = [r for r in actions if r.get("phase") == "dispatch_request"]
    if len(dispatch) != 1 or dispatch[0].get("event_kind") != "KeyPress":
        errors.append("expected exactly one dispatched Shift KeyPress")
    elif app_events:
        act_id = dispatch[0].get("actuation_id")
        ev = app_events[0]
        if ev.get("actuation_id") != act_id or ev.get("kind") != "KeyPress" or ev.get("keycode") != dispatch[0].get("keycode") or ev.get("causal_parent_ids") != [f"act:{act_id}"]:
            errors.append("Tk app record does not match the XTest dispatch parent")
    if any(r.get("phase") == "dispatch_request" and r.get("event_kind") == "KeyRelease" for r in actions):
        errors.append("runner dispatched release despite missing observer record")
    if run.get("terminal_shift_down") is not None:
        errors.append("candidate should not claim a terminal keymap it never queried")

    xvfb = subprocess.run(["pgrep", "-a", "Xvfb"], capture_output=True, text=True)
    no_xvfb_listed = xvfb.returncode == 1 and not xvfb.stdout.strip()
    result = {
        "schema": "blackstart-prospective-trace-audit-hold-v1",
        "status": "PASS_AUDIT_HOLD_OBSERVER_EVENT_MISSING" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "frozen_inputs_match": frozen_inputs,
        "frozen_source_hashes_match": frozen_sources,
        "prior_attempt_hashes_match": frozen_prior,
        "archive_inventory": inventory,
        "t2_preflight_stop_supported": stop1_ok,
        "t2b_no_dispatch_stop_supported": stop2_ok,
        "app_arm_ack_count": len(app_ack),
        "observer_arm_ack_count": len(obs_ack),
        "app_key_event_count": len(app_events),
        "observer_key_event_count": len(obs_events),
        "dispatched_keypress_count": len(dispatch),
        "dispatched_keyrelease_count": sum(r.get("phase") == "dispatch_request" and r.get("event_kind") == "KeyRelease" for r in actions),
        "neutral_terminal_keymap_verified": False,
        "no_xvfb_process_listed_after_candidate": no_xvfb_listed,
        "candidate_disposition": candidate.get("disposition"),
        "timestamps_used_to_infer_causality": False,
    }
    (ROOT / "audit.hold.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_AUDIT_HOLD_OBSERVER_EVENT_MISSING" else 2


if __name__ == "__main__":
    raise SystemExit(audit())
