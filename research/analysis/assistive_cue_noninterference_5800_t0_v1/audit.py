"""Independent raw-only checker for the synthetic #5800 cue surface fixture."""

import itertools
import json
from pathlib import Path


AXES = (
    "focus_owner_ok", "focus_order_ok", "keyboard_exit_ok", "at_tree_unchanged",
    "pointer_target_unchanged", "warning_visible", "cue_removed",
    "nonvisual_route_operable", "task_effect_exact",
)


def main():
    candidate = json.loads(Path("candidate.raw.json").read_text(encoding="utf-8"))
    errors = []
    expected_controls = {
        "no_cue": "METHOD_PASS_SCOPED",
        "model_only": "METHOD_PASS_SCOPED",
        "shared_passive": "METHOD_PASS_SCOPED",
        "shared_intrusive_negative_control": "FAIL_NONINTERFERENCE",
        "at_backend_unavailable": "HOLD_AT_ORACLE_UNAVAILABLE",
    }
    controls = candidate.get("controls", {})
    for label, decision in expected_controls.items():
        if controls.get(label, {}).get("decision") != decision:
            errors.append("control_decision:" + label)
    if candidate.get("model_only_shared_state_unchanged") is not True:
        errors.append("model_only_changed_shared_state")
    if candidate.get("passive_overlay_has_no_interaction_delta") is not True:
        errors.append("passive_overlay_interaction_delta")

    rows = candidate.get("mutation_profiles", [])
    expected_masks = set(range(1 << len(AXES)))
    seen = set()
    fail_count = 0
    pass_count = 0
    for row in rows:
        mask = row.get("mutation_mask")
        if type(mask) is not int or mask not in expected_masks or mask in seen:
            errors.append("invalid_or_duplicate_profile")
            continue
        seen.add(mask)
        # The candidate defines a set bit as an injected false dimension.
        false_axes = [axis for index, axis in enumerate(AXES) if mask & (1 << index)]
        if row.get("false_dimensions") != false_axes:
            errors.append("mutation_identity:" + str(mask))
        expected = "METHOD_PASS_SCOPED" if mask == 0 else "FAIL_NONINTERFERENCE"
        if row.get("decision") != expected:
            errors.append("missed_or_false_alarm:" + str(mask))
        if mask == 0:
            pass_count += row.get("decision") == "METHOD_PASS_SCOPED"
        else:
            fail_count += row.get("decision") == "FAIL_NONINTERFERENCE"
    if seen != expected_masks:
        errors.append("profile_coverage:" + str(len(seen)))
    if candidate.get("profile_count") != len(expected_masks):
        errors.append("profile_count_mismatch")
    result = {
        "decision": "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT",
        "profiles_expected": len(expected_masks),
        "profiles_seen": len(seen),
        "clean_controls_passed": pass_count,
        "injected_harm_profiles_detected": fail_count,
        "injected_harm_profiles_expected": len(expected_masks) - 1,
        "intrusive_negative_control_failed": controls.get("shared_intrusive_negative_control", {}).get("decision") == "FAIL_NONINTERFERENCE",
        "unavailable_at_control_held": controls.get("at_backend_unavailable", {}).get("decision") == "HOLD_AT_ORACLE_UNAVAILABLE",
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
