"""Strict construction auditor for ordered Tk Ctrl+S witnesses and effects."""
from __future__ import annotations

from typing import Any


KEY_PRESS = "2"
CONTROL_MASK = 0x4


def audit_row(
    events: list[dict[str, Any]], effects: list[dict[str, Any]], marker: str
) -> dict[str, Any]:
    key_events = [event for event in events if event.get("type") == KEY_PRESS]
    controls = [event for event in key_events if event.get("keysym") == "Control_L"]
    chord_s = [
        event
        for event in key_events
        if event.get("keysym") == "s"
        and type(event.get("state")) is int
        and event["state"] & CONTROL_MASK
    ]
    indexed_controls = [(i, event) for i, event in enumerate(key_events) if event in controls]
    indexed_s = [(i, event) for i, event in enumerate(key_events) if event in chord_s]
    ordered_pairs = [
        (control, key)
        for control_index, control in indexed_controls
        for key_index, key in indexed_s
        if key_index == control_index + 1
        and type(control.get("monotonic_ns")) is int
        and type(key.get("monotonic_ns")) is int
        and control["monotonic_ns"] < key["monotonic_ns"]
    ]
    exact_witness = len(controls) == 1 and len(chord_s) == 1 and len(ordered_pairs) == 1
    effect = effects[0] if len(effects) == 1 else None
    exact_effect = (
        isinstance(effect, dict)
        and effect.get("saved") is True
        and effect.get("text") == marker
        and type(effect.get("save_callback_count")) is int
        and effect.get("save_callback_count") == 1
        and type(effect.get("save_callback_monotonic_ns")) is int
    )
    effect_follows_witness = bool(
        exact_effect
        and exact_witness
        and ordered_pairs[0][1]["monotonic_ns"] < effect["save_callback_monotonic_ns"]
    )
    return {
        "exact_witness": exact_witness,
        "exact_effect": exact_effect,
        "effect_follows_witness": effect_follows_witness,
        "pass": exact_witness and exact_effect and effect_follows_witness,
        "control_keypresses": len(controls),
        "control_s_keypresses": len(chord_s),
        "effect_receipts": len(effects),
    }
