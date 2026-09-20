"""Strict construction auditor for ordered Tk Ctrl+S witnesses and effects."""
from __future__ import annotations

from typing import Any


KEY_PRESS = "2"
CONTROL_MASK = 0x4


def audit_row(events: list[dict[str, Any]], effect: dict[str, Any] | None, marker: str) -> dict[str, Any]:
    key_events = [event for event in events if event.get("type") == KEY_PRESS]
    controls = [event for event in key_events if event.get("keysym") == "Control_L"]
    chord_s = [
        event
        for event in key_events
        if event.get("keysym") == "s"
        and isinstance(event.get("state"), int)
        and event["state"] & CONTROL_MASK
    ]
    indexed_controls = [(i, event) for i, event in enumerate(key_events) if event in controls]
    indexed_s = [(i, event) for i, event in enumerate(key_events) if event in chord_s]
    ordered_pairs = [
        (control, key)
        for control_index, control in indexed_controls
        for key_index, key in indexed_s
        if key_index == control_index + 1
        and isinstance(control.get("monotonic_ns"), int)
        and isinstance(key.get("monotonic_ns"), int)
        and control["monotonic_ns"] < key["monotonic_ns"]
    ]
    exact_witness = len(controls) == 1 and len(chord_s) == 1 and len(ordered_pairs) == 1
    exact_effect = (
        isinstance(effect, dict)
        and effect.get("saved") is True
        and effect.get("text") == marker
        and isinstance(effect.get("save_callback_monotonic_ns"), int)
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
    }
