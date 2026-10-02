"""Finite executable tool-surface semantics for Issue #6210 T0."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SURFACES = {
    "canonical": {"target_field": "target_id", "epoch_field": "evidence_epoch", "guards": ["target", "epoch"], "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type", "key_up"], "submit": ["submit", "receipt"]}, "map_wrong_target": False, "hide_release_checkpoint": False},
    "renamed_fields": {"target_field": "control_ref", "epoch_field": "snapshot_generation", "guards": ["target", "epoch"], "calls": ["activate", "enter_value", "commit"], "expansions": {"activate": ["focus"], "enter_value": ["key_down", "type", "key_up"], "commit": ["submit", "receipt"]}, "map_wrong_target": False, "hide_release_checkpoint": False},
    "split_same_checkpoints": {"target_field": "destination", "epoch_field": "source_epoch", "guards": ["target", "epoch"], "calls": ["focus_control", "press_key", "insert_text", "release_key", "submit_form"], "expansions": {"focus_control": ["focus"], "press_key": ["key_down"], "insert_text": ["type"], "release_key": ["key_up"], "submit_form": ["submit", "receipt"]}, "map_wrong_target": False, "hide_release_checkpoint": False},
    "merged_with_full_trace": {"target_field": "target", "epoch_field": "generation", "guards": ["target", "epoch"], "calls": ["save_with_trace"], "expansions": {"save_with_trace": ["focus", "key_down", "type", "key_up", "submit", "receipt"]}, "map_wrong_target": False, "hide_release_checkpoint": False},
    "skip_freshness_guard": {"target_field": "target_id", "epoch_field": "evidence_epoch", "guards": ["target"], "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type", "key_up"], "submit": ["submit", "receipt"]}, "map_wrong_target": False, "hide_release_checkpoint": False},
    "alias_wrong_target": {"target_field": "target_id", "epoch_field": "evidence_epoch", "guards": ["target", "epoch"], "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type", "key_up"], "submit": ["submit", "receipt"]}, "map_wrong_target": True, "hide_release_checkpoint": False},
    "omit_release": {"target_field": "target_id", "epoch_field": "evidence_epoch", "guards": ["target", "epoch"], "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type"], "submit": ["submit", "receipt"]}, "map_wrong_target": False, "hide_release_checkpoint": False},
    "hide_intermediate_release_state": {"target_field": "target_id", "epoch_field": "evidence_epoch", "guards": ["target", "epoch"], "calls": ["focus", "type_text", "submit"], "expansions": {"focus": ["focus"], "type_text": ["key_down", "type", "key_up"], "submit": ["submit", "receipt"]}, "map_wrong_target": False, "hide_release_checkpoint": True},
}


def load_fixture():
    return json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


def expand_calls(surface):
    return [primitive for call in surface["calls"] for primitive in surface["expansions"][call]]


def boundary_profile(surface):
    return [len(surface["expansions"][call]) for call in surface["calls"]]


def execute_case(case, surface, context):
    payload = {
        surface["target_field"]: case["target_id"],
        surface["epoch_field"]: case["evidence_epoch"],
        "cancel_after_type": case["cancel_after_type"],
    }
    target = payload[surface["target_field"]]
    epoch = payload[surface["epoch_field"]]
    steps = expand_calls(surface)
    if surface["map_wrong_target"] and target != context["authorized_target"]:
        target = context["authorized_target"]

    events = ["OBSERVATION_BOUND"]
    observations = [{"checkpoint": "before", "input_empty": True, "effect_count": 0}]
    if "target" in surface["guards"] and target != context["authorized_target"]:
        events.append("YIELD_WRONG_TARGET")
        observations.append({"checkpoint": "terminal", "decision": "YIELD_WRONG_TARGET", "input_empty": True, "effect_count": 0})
        return {"events": events, "observations": observations, "terminal": {"decision": "YIELD_WRONG_TARGET", "input_empty": True, "effect_count": 0, "effect_target": None}}
    if "epoch" in surface["guards"] and epoch != context["current_epoch"]:
        events.append("YIELD_STALE_EVIDENCE")
        observations.append({"checkpoint": "terminal", "decision": "YIELD_STALE_EVIDENCE", "input_empty": True, "effect_count": 0})
        return {"events": events, "observations": observations, "terminal": {"decision": "YIELD_STALE_EVIDENCE", "input_empty": True, "effect_count": 0, "effect_target": None}}

    events.append("ACTION_ADMITTED")
    held = False
    if "focus" in steps:
        events.append("FOCUS_TARGET")
    if "key_down" in steps:
        events.append("KEY_DOWN")
        held = True
    if "type" in steps:
        events.append("TEXT_TYPED")
    if case["cancel_after_type"]:
        events.append("CANCEL_REQUESTED")
        if held:
            events.extend(["KEY_UP_CANCEL_CLEANUP", "INPUT_EMPTY_VERIFIED"])
        held = False
        if not surface["hide_release_checkpoint"]:
            observations.append({"checkpoint": "after_release_before_effect", "input_empty": True, "effect_count": 0})
        events.append("CANCEL_ACK")
        observations.append({"checkpoint": "terminal", "decision": "CANCELLED_NO_EFFECT", "input_empty": not held, "effect_count": 0})
        return {"events": events, "observations": observations, "terminal": {"decision": "CANCELLED_NO_EFFECT", "input_empty": not held, "effect_count": 0, "effect_target": None}}

    if "key_up" in steps and held:
        events.extend(["KEY_UP", "INPUT_EMPTY_VERIFIED"])
        held = False
        if not surface["hide_release_checkpoint"]:
            observations.append({"checkpoint": "after_release_before_effect", "input_empty": True, "effect_count": 0})
    if held:
        events.append("YIELD_INPUT_NOT_EMPTY")
        terminal = {"decision": "YIELD_INPUT_NOT_EMPTY", "input_empty": False, "effect_count": 0, "effect_target": None}
        observations.append({"checkpoint": "terminal", "decision": terminal["decision"], "input_empty": False, "effect_count": 0})
        return {"events": events, "observations": observations, "terminal": terminal}

    if "submit" not in steps:
        events.append("YIELD_NO_SUBMIT")
        terminal = {"decision": "YIELD_NO_SUBMIT", "input_empty": not held, "effect_count": 0, "effect_target": None}
        observations.append({"checkpoint": "terminal", "decision": terminal["decision"], "input_empty": not held, "effect_count": 0})
        return {"events": events, "observations": observations, "terminal": terminal}
    events.extend(["SUBMIT_ADMITTED", "EFFECT_APPLIED"])
    if "receipt" in steps:
        events.append("EFFECT_RECEIPT")
    terminal = {"decision": "EFFECT_RECEIPT", "input_empty": True, "effect_count": 1, "effect_target": target}
    observations.append({"checkpoint": "terminal", "decision": terminal["decision"], "input_empty": True, "effect_count": 1})
    return {"events": events, "observations": observations, "terminal": terminal}


def certify_surfaces(fixture):
    canonical = {
        case["id"]: execute_case(case, SURFACES["canonical"], fixture["context"])
        for case in fixture["cases"]
    }
    decisions = {}
    for name, surface in SURFACES.items():
        same_program = expand_calls(surface) == expand_calls(SURFACES["canonical"])
        same_call_boundaries = boundary_profile(surface) == boundary_profile(SURFACES["canonical"])
        decisions[name] = same_program and same_call_boundaries and all(
            execute_case(case, surface, fixture["context"]) == canonical[case["id"]]
            for case in fixture["cases"]
        )
    return decisions
