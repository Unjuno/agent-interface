"""Raw-only independent auditor for the Issue #8397 T0 trace fixture."""
import argparse
import json
from pathlib import Path

EXPECTED = {
    "pre_decision": {"arms": {"baseline", "omission"}, "effect": "A_applied", "recovery": 0},
    "cross_transition": {"arms": {"baseline", "omission"}, "effect": None, "recovery": None},
    "post_completion": {"arms": {"baseline", "omission"}, "effect": "A_applied", "recovery": 0},
    "captured_undelivered": {"arms": {"transport_control"}},
    "mandatory_safety": {"arms": {"omission_request_rejected"}},
}


EXPECTED_ROWS = {
    ("pre_decision", "baseline"): {"state": "before_observation_sensitive_decision", "interval": [0, 0], "captured": 3, "delivered": 3, "visible_bytes": 300, "mandatory_cue_delivered": True, "decision": "act_on_current_A", "task_effect": "A_applied", "recovery_steps": 0, "stop_outcome": "completed_exactly"},
    ("pre_decision", "omission"): {"state": "before_observation_sensitive_decision", "interval": [0, 1], "captured": 2, "delivered": 2, "visible_bytes": 200, "mandatory_cue_delivered": True, "decision": "act_on_current_A_after_resume", "task_effect": "A_applied", "recovery_steps": 0, "stop_outcome": "completed_exactly"},
    ("cross_transition", "baseline"): {"state": "crosses_target_change_before_decision", "interval": [0, 0], "captured": 3, "delivered": 3, "visible_bytes": 300, "mandatory_cue_delivered": True, "decision": "act_on_current_B", "task_effect": "B_applied", "recovery_steps": 0, "stop_outcome": "completed_exactly"},
    ("cross_transition", "omission"): {"state": "crosses_target_change_before_decision", "interval": [1, 2], "captured": 2, "delivered": 2, "visible_bytes": 200, "mandatory_cue_delivered": True, "decision": "act_on_stale_A_then_recover_to_B", "task_effect": "wrong_A_then_B_recovered", "recovery_steps": 1, "stop_outcome": "completed_after_recovery"},
    ("post_completion", "baseline"): {"state": "after_independently_verified_terminal_effect", "interval": [0, 0], "captured": 3, "delivered": 3, "visible_bytes": 300, "mandatory_cue_delivered": True, "decision": "terminal_already_verified", "task_effect": "A_applied", "recovery_steps": 0, "stop_outcome": "completed_exactly"},
    ("post_completion", "omission"): {"state": "after_independently_verified_terminal_effect", "interval": [2, 3], "captured": 2, "delivered": 2, "visible_bytes": 200, "mandatory_cue_delivered": True, "decision": "terminal_already_verified", "task_effect": "A_applied", "recovery_steps": 0, "stop_outcome": "completed_exactly"},
    ("captured_undelivered", "transport_control"): {"state": "target_changes_after_capture_before_decision", "interval": [1, 2], "captured": 1, "delivered": 0, "visible_bytes": 0, "mandatory_cue_delivered": True, "decision": "act_on_stale_A", "task_effect": "wrong_A_applied", "recovery_steps": 1, "stop_outcome": "completed_after_recovery"},
    ("mandatory_safety", "omission_request_rejected"): {"state": "mandatory_safety_cue_pending", "interval": [0, 1], "captured": 1, "delivered": 1, "visible_bytes": 80, "mandatory_cue_delivered": True, "decision": "no_action_until_safety_cue", "task_effect": "no_external_effect", "recovery_steps": 0, "stop_outcome": "omission_rejected_mandatory_cue"},
}


def audit(raw):
    errors = []
    rows = raw.get("episodes")
    if raw.get("allocation") != "OBS-OMISSION-REGRET-8397-T0-A02-20261008":
        errors.append("allocation identity mismatch")
    if not isinstance(rows, list) or len(rows) != 8:
        return ["wrong episode row count"]
    by_id = {}
    for row in rows:
        by_id.setdefault(row.get("id"), []).append(row)
    if set(by_id) != set(EXPECTED):
        errors.append("episode id universe mismatch")
    for row in rows:
        key = (row.get("id"), row.get("arm"))
        expected = EXPECTED_ROWS.get(key)
        if expected is None:
            errors.append(f"unexpected row key: {key}")
            continue
        for field, value in expected.items():
            if row.get(field) != value:
                errors.append(f"{key}: {field} mismatch")
    if {(r.get("id"), r.get("arm")) for r in rows} != set(EXPECTED_ROWS):
        errors.append("row key universe mismatch")
    expected_states = {
        "pre_decision": "before_observation_sensitive_decision",
        "cross_transition": "crosses_target_change_before_decision",
        "post_completion": "after_independently_verified_terminal_effect",
        "captured_undelivered": "target_changes_after_capture_before_decision",
        "mandatory_safety": "mandatory_safety_cue_pending",
    }
    for case, spec in EXPECTED.items():
        group = by_id.get(case, [])
        if {r.get("arm") for r in group} != spec["arms"]:
            errors.append(f"{case}: arm universe mismatch")
        for r in group:
            if r.get("state") != expected_states[case]:
                errors.append(f"{case}: state/interval stratum mismatch")
            if r.get("captured", -1) < r.get("delivered", -1):
                errors.append(f"{case}: delivered exceeds captured")
            if r.get("visible_bytes", -1) < 0:
                errors.append(f"{case}: negative visible bytes")
            if not r.get("mandatory_cue_delivered"):
                errors.append(f"{case}: mandatory cue absent")
    pre = {r["arm"]: r for r in by_id.get("pre_decision", [])}
    if set(pre) == {"baseline", "omission"}:
        if pre["baseline"]["task_effect"] != pre["omission"]["task_effect"]:
            errors.append("pre-decision omission changed task effect")
        if not pre["omission"]["visible_bytes"] < pre["baseline"]["visible_bytes"]:
            errors.append("pre-decision omission did not reduce model-visible bytes")
        if not pre["omission"]["delivered"] < pre["baseline"]["delivered"]:
            errors.append("pre-decision omission did not reduce delivered calls")
        if pre["omission"]["state"] != "before_observation_sensitive_decision":
            errors.append("pre-decision interval state mismatch")
    cross = {r["arm"]: r for r in by_id.get("cross_transition", [])}
    if set(cross) == {"baseline", "omission"}:
        if cross["baseline"]["task_effect"] != "B_applied":
            errors.append("cross-transition baseline oracle mismatch")
        if cross["omission"]["task_effect"] != "wrong_A_then_B_recovered":
            errors.append("cross-transition omission regret missing")
        if cross["omission"]["recovery_steps"] <= 0:
            errors.append("cross-transition recovery cost missing")
    post = {r["arm"]: r for r in by_id.get("post_completion", [])}
    if set(post) == {"baseline", "omission"}:
        if post["baseline"]["task_effect"] != post["omission"]["task_effect"]:
            errors.append("post-completion omission changed verified effect")
        if not post["omission"]["visible_bytes"] < post["baseline"]["visible_bytes"]:
            errors.append("post-completion omission did not reduce model-visible bytes")
        if post["omission"]["state"] != "after_independently_verified_terminal_effect":
            errors.append("post-completion interval state mismatch")
    undelivered = by_id.get("captured_undelivered", [])
    if len(undelivered) == 1:
        r = undelivered[0]
        if (r["captured"], r["delivered"], r["visible_bytes"]) != (1, 0, 0):
            errors.append("captured-but-undelivered control collapsed into omission")
    safety = by_id.get("mandatory_safety", [])
    if len(safety) == 1:
        r = safety[0]
        if r["arm"] != "omission_request_rejected" or not r["mandatory_cue_delivered"]:
            errors.append("mandatory safety omission was not rejected")
        if r["stop_outcome"] != "omission_rejected_mandatory_cue":
            errors.append("mandatory safety rejection outcome missing")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    errors = audit(raw)
    result = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL", "rows": len(raw.get("episodes", [])), "errors": errors}
    with Path(args.output).open("x", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
