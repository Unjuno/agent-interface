"""Synthetic surface-contract T0 for Issue #5800; no GUI or human participant."""

from __future__ import annotations

from itertools import product


DIMENSIONS = (
    "focus_owner_ok",
    "focus_order_ok",
    "keyboard_exit_ok",
    "at_tree_unchanged",
    "pointer_target_unchanged",
    "warning_visible",
    "cue_removed",
    "nonvisual_route_operable",
    "task_effect_exact",
)


def score(observation: dict) -> dict:
    if observation.get("at_backend_available") is not True:
        return {"decision": "HOLD_AT_ORACLE_UNAVAILABLE", "violations": []}
    signals = observation.get("signals")
    if not isinstance(signals, dict):
        return {"decision": "HOLD_MISSING_OBSERVATION", "violations": []}
    violations = [name for name in DIMENSIONS if signals.get(name) is not True]
    return {
        "decision": "FAIL_NONINTERFERENCE" if violations else "METHOD_PASS_SCOPED",
        "violations": violations,
    }


def observations():
    clean = {name: True for name in DIMENSIONS}
    none = {"at_backend_available": True, "signals": dict(clean), "shared_cue_visible": False,
            "private_model_cue_visible": False, "shared_state_changed": False}
    model_only = {"at_backend_available": True, "signals": dict(clean), "shared_cue_visible": False,
                  "private_model_cue_visible": True, "shared_state_changed": False}
    passive = {"at_backend_available": True, "signals": dict(clean), "shared_cue_visible": True,
               "private_model_cue_visible": False, "shared_state_changed": False}
    harmful = dict(clean)
    for name in ("focus_owner_ok", "focus_order_ok", "keyboard_exit_ok", "at_tree_unchanged",
                 "pointer_target_unchanged", "warning_visible", "cue_removed",
                 "nonvisual_route_operable", "task_effect_exact"):
        harmful[name] = False
    intrusive = {"at_backend_available": True, "signals": harmful, "shared_cue_visible": True,
                 "private_model_cue_visible": False, "shared_state_changed": True}
    unavailable = {"at_backend_available": False, "signals": None, "shared_cue_visible": True,
                   "private_model_cue_visible": False, "shared_state_changed": None}
    return {"no_cue": none, "model_only": model_only, "shared_passive": passive,
            "shared_intrusive_negative_control": intrusive, "at_backend_unavailable": unavailable}


def run():
    controls = observations()
    control_results = {name: score(obs) for name, obs in controls.items()}
    profiles = []
    for bits in product((False, True), repeat=len(DIMENSIONS)):
        mutated = {name: value for name, value in zip(DIMENSIONS, bits)}
        mask = sum((1 << i) for i, name in enumerate(DIMENSIONS) if not mutated[name])
        result = score({"at_backend_available": True, "signals": mutated})
        profiles.append({"mutation_mask": mask,
                         "false_dimensions": [name for name in DIMENSIONS if not mutated[name]],
                         **result})
    return {
        "dimensions": list(DIMENSIONS),
        "controls": control_results,
        "model_only_shared_state_unchanged": controls["model_only"]["shared_state_changed"] is False,
        "passive_overlay_has_no_interaction_delta": controls["shared_passive"]["shared_state_changed"] is False,
        "profile_count": len(profiles),
        "mutation_profiles": profiles,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
