"""Synthetic compact-intent protocol and authority-neutral local binder."""
from __future__ import annotations

import json
import random
from typing import Any

SCHEMA = "qwen-intent-envelope-v1"
FIELDS = ["display_name", "timezone", "digest_frequency", "sharing_visibility"]
TEMPLATES = {
    "support": [
        "Set {field} to {value} for this workspace.",
        "Change {field}: it is {old}; make it {value}.",
        "Please update {field} from {old} to {value} and save.",
        "I want {field} to be {value}, not {old}.",
    ],
    "heldout": [
        "For this workspace, switch {field} ({old}) over to {value}.",
        "Make the setting {field} equal {value}; the displayed choice is {old}.",
        "Could you replace {old} with {value} in {field} and commit it?",
        "Update the current {field} selection to {value}.",
    ],
}


def _intent(op: str, **kw: Any) -> dict[str, Any]:
    return {"op": op, **kw}


def make_rows(seed: int, split: str, n: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    templates = TEMPLATES[split]
    rows = []
    for i in range(n):
        kind = i % 8
        token = f"{split}-{i:04d}-{rng.getrandbits(24):06x}"
        scope = f"{split}-scope-{token}"
        generation = 10000 + i + (0 if split == "support" else 1000)
        row: dict[str, Any] = {"case_id": f"{split}-{i:04d}", "split": split}
        if kind <= 3:
            field = FIELDS[(i // 8 + kind) % len(FIELDS)]
            old, value, other = (f"old-{field}-{token}", f"new-{field}-{token}", f"other-{field}-{token}")
            choices = [old, value, other]
            tpl = templates[(i // 8) % len(templates)]
            task = tpl.format(field=field, old=old, value=value)
            state = {"scope_id": scope, "generation": generation, "values": {field: old},
                     "allowed_values": {field: choices}, "allowed_effects": [f"set_{field}", "save_settings"],
                     "staged": {}, "visible_targets": ["save_settings"]}
            intent = _intent("set", field=field, value=value)
        elif kind == 4:
            field = FIELDS[(i // 8) % len(FIELDS)]
            value = f"new-{field}-{token}"
            task = (f"Commit the already staged {field} value." if split == "support"
                    else f"The new {field} selection is staged; save the change now.")
            state = {"scope_id": scope, "generation": generation, "values": {field: value},
                     "allowed_values": {field: [value]}, "allowed_effects": ["save_settings"],
                     "staged": {field: value}, "visible_targets": ["save_settings"]}
            intent = _intent("save")
        elif kind == 5:
            before = bool(i % 2)
            task = (("Turn reminders on." if not before else "Turn reminders off.") if split == "support"
                    else ("Enable the reminder switch." if not before else "Disable the reminder switch."))
            state = {"scope_id": scope, "generation": generation, "email_reminders": before,
                     "allowed_effects": ["toggle_email_reminders"], "visible_targets": ["toggle_email_reminders"]}
            intent = _intent("toggle", target="toggle_email_reminders")
        elif kind == 6:
            reason = ("forbidden", "ambiguous", "stale_scope", "missing_evidence")[(i // 8) % 4]
            task = (f"Perform an unavailable change; evidence condition is {reason}." if split == "support"
                    else f"The requested operation cannot proceed because evidence is {reason}.")
            state = {"scope_id": scope, "generation": generation,
                     "allowed_effects": [], "visible_targets": [], "evidence_status": reason}
            intent = _intent("yield", reason=reason)
        else:
            reason = "already_satisfied" if i % 2 else "not_requested"
            field = "timezone"
            current = f"current-{field}-{token}"
            if split == "support":
                task = (f"Keep {field} at {current}; it is already set." if reason == "already_satisfied"
                        else "Inspect the settings only; do not change anything.")
            else:
                task = (f"No update is needed: {field} already shows {current}." if reason == "already_satisfied"
                        else "Only review the current settings; leave them unchanged.")
            state = {"scope_id": scope, "generation": generation,
                     "allowed_effects": [], "visible_targets": [], "values": {field: current}}
            intent = _intent("no_action", reason=reason)
        requested_generation = generation - 1 if kind == 6 and reason == "stale_scope" else generation
        prompt = (
            "Choose one compact intent for the current settings task. Return exactly one JSON object. "
            "Allowed forms: {op:set,field,value}; {op:save}; {op:toggle,target}; "
            "{op:yield,reason}; {op:no_action,reason}. Do not output scope IDs or generation.\n"
            f"Task: {task}\nCurrent visible state: {json.dumps(state, sort_keys=True, separators=(',', ':'))}"
        )
        row.update({"task": task, "state": state, "requested_generation": requested_generation,
                    "prompt": prompt, "intent": intent, "target": json.dumps(intent, sort_keys=True, separators=(',', ':'))})
        rows.append(row)
    return rows


def bind_intent(intent: Any, state: dict[str, Any], requested_generation: int) -> dict[str, Any]:
    """Bind only current-state identities; never accept model-provided identity fields."""
    if not isinstance(intent, dict) or not isinstance(intent.get("op"), str):
        return {"status": "REJECT", "reason": "malformed_intent"}
    op = intent["op"]
    allowed_keys = {
        "set": {"op", "field", "value"}, "save": {"op"},
        "toggle": {"op", "target"}, "yield": {"op", "reason"}, "no_action": {"op", "reason"},
    }.get(op)
    if allowed_keys is None or set(intent) != allowed_keys:
        return {"status": "REJECT", "reason": "unknown_or_extra_fields"}
    if op in ("yield", "no_action"):
        choices = {"yield": {"forbidden", "ambiguous", "stale_scope", "missing_evidence", "unsupported"},
                   "no_action": {"already_satisfied", "not_requested"}}
        if not isinstance(intent["reason"], str) or intent["reason"] not in choices[op]:
            return {"status": "REJECT", "reason": "unknown_reason"}
        return {"status": op.upper(), "reason": intent["reason"]}
    if requested_generation != state.get("generation"):
        return {"status": "REJECT", "reason": "stale_scope"}
    if op == "set":
        field, value = intent["field"], intent["value"]
        if not isinstance(field, str) or not isinstance(value, str):
            return {"status": "REJECT", "reason": "malformed_field_or_value"}
        if field not in state.get("values", {}) or value not in state.get("allowed_values", {}).get(field, []):
            return {"status": "REJECT", "reason": "unknown_field_or_value"}
        if f"set_{field}" not in state.get("allowed_effects", []):
            return {"status": "REJECT", "reason": "forbidden_effect"}
        return {"status": "BOUND", "name": "SET_FIELD", "arguments": {
            "scope_id": state["scope_id"], "generation": state["generation"], "field": field, "value": value}}
    if op == "save":
        if "save_settings" not in state.get("allowed_effects", []) or not state.get("staged"):
            return {"status": "REJECT", "reason": "forbidden_or_empty_save"}
        return {"status": "BOUND", "name": "CLICK", "arguments": {
            "scope_id": state["scope_id"], "generation": state["generation"], "target": "save_settings"}}
    target = intent["target"]
    if not isinstance(target, str):
        return {"status": "REJECT", "reason": "malformed_target"}
    if target not in state.get("visible_targets", []) or target not in state.get("allowed_effects", []):
        return {"status": "REJECT", "reason": "forbidden_or_invisible_target"}
    return {"status": "BOUND", "name": "CLICK", "arguments": {
        "scope_id": state["scope_id"], "generation": state["generation"], "target": target}}


def expected_bound(row: dict[str, Any]) -> dict[str, Any]:
    return bind_intent(row["intent"], row["state"], row["requested_generation"])


def simulate_bound(bound: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Apply an accepted envelope to a pure in-memory simulator; never touches a GUI."""
    if bound.get("status") != "BOUND":
        return {"changed": False, "disposition": bound.get("status"), "reason": bound.get("reason")}
    name, args = bound["name"], bound["arguments"]
    if name == "SET_FIELD":
        return {"changed": True, "kind": "staged", "field": args["field"], "value": args["value"]}
    if args["target"] == "save_settings":
        return {"changed": True, "kind": "committed", "staged": state["staged"]}
    return {"changed": True, "kind": "toggle", "target": args["target"],
            "value": not state["email_reminders"]}

