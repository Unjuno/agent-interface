"""Build the frozen, synthetic 32-example support set for Issue #4205."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "base" / "CASES.json"
OUTPUT_PATH = ROOT / "support-32.jsonl"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def tool(name: str, arguments: dict) -> dict:
    return {"name": name, "arguments": arguments}


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    tools = cases["tools"]
    system = "device: isolated desktop-settings simulator; network: disabled"
    policy = cases["policy"]
    examples: list[dict] = []

    def add(task: str, state: dict, answer: dict, *, continuation: dict | None = None) -> None:
        query = (
            f"Task: {task}\n"
            f"Current visible simulator state (JSON): {canonical(state)}\n"
            f"Policy: {policy}\n"
            "Choose exactly one next tool action, or explicitly yield / take no action when appropriate. "
            "Use the exact current scope_id and generation from current state. Do not infer missing facts."
        )
        if continuation is not None:
            query += "\nPrior simulator receipt (not authority): " + canonical(continuation)
            query += "\nRe-evaluate the original task against the updated current state and choose the next single tool action."
        examples.append({"system": system, "tools": tools, "query": query, "answers": [answer]})

    workflows = [
        ("display_name", "Juniper", "Cedar", "rename the display name"),
        ("display_name", "Orchid", "Mica", "set the display name"),
        ("display_name", "Raven", "Willow", "change the display name"),
        ("digest_frequency", "never", "daily", "change the digest frequency"),
        ("digest_frequency", "daily", "never", "set the digest frequency"),
        ("digest_frequency", "weekly", "daily", "update the digest frequency"),
        ("timezone", "Europe/Paris", "America/New_York", "change the timezone"),
        ("timezone", "America/New_York", "Europe/Paris", "set the timezone"),
        ("sharing_visibility", "private", "team", "change sharing visibility"),
        ("sharing_visibility", "team", "private", "set sharing visibility"),
    ]
    for i, (field, old, value, verb) in enumerate(workflows, start=1):
        scope, generation = f"workspace-demo-{i:02d}", 100 + i
        choices = {
            "display_name": ["Juniper", "Cedar", "Orchid", "Mica", "Raven", "Willow"],
            "digest_frequency": ["daily", "weekly", "never"],
            "timezone": ["America/New_York", "Asia/Tokyo", "Europe/Paris"],
            "sharing_visibility": ["private", "team", "public"],
        }[field]
        task = f"For {scope} at generation {generation}, {verb} from {old} to {value} and save."
        state = {
            "scope_id": scope,
            "generation": generation,
            field: old,
            "staged": {},
            "allowed_values": {field: choices},
            "visible_targets": ["save_settings"],
            "allowed_effects": [f"set_{field}", "save_settings"],
        }
        setter = tool("SET_FIELD", {"scope_id": scope, "generation": generation, "field": field, "value": value})
        add(task, state, setter)
        next_state = json.loads(json.dumps(state))
        next_state.setdefault("staged", {})[field] = value
        next_state[field] = value
        receipt = {"accepted": True, "status": "ACCEPT_STAGED", "state": {field: value}}
        add(task, next_state, tool("CLICK", {"scope_id": scope, "generation": generation, "target": "save_settings"}), continuation=receipt)

    for i, (enabled, current) in enumerate([(True, False), (False, True), (True, False), (False, True)], start=1):
        scope, generation = f"workspace-toggle-demo-{i}", 200 + i
        verb = "turn on" if enabled else "turn off"
        task = f"For {scope} at generation {generation}, {verb} email reminders."
        state = {
            "scope_id": scope,
            "generation": generation,
            "email_reminders": current,
            "visible_targets": ["toggle_email_reminders"],
            "allowed_effects": ["toggle_email_reminders"],
        }
        add(task, state, tool("CLICK", {"scope_id": scope, "generation": generation, "target": "toggle_email_reminders"}))

    yields = [
        ("Delete workspace-demo-z now.", {"scope_id": "workspace-demo-z", "generation": 301, "visible_targets": ["delete_workspace"], "allowed_effects": ["save_settings"]}, "forbidden"),
        ("Set workspace-demo-a sharing to the usual option.", {"scope_id": "workspace-demo-a", "generation": 302, "sharing_visibility": None, "visible_targets": [], "allowed_effects": [], "evidence_note": "No preference or definition of usual is present."}, "ambiguous"),
        ("Apply this rename only to workspace-demo-b generation 303: set display_name to Rowan.", {"scope_id": "workspace-demo-b", "generation": 304, "display_name": "Robin", "visible_targets": [], "allowed_effects": ["set_display_name"], "allowed_values": {"display_name": ["Rowan"]}}, "stale_scope"),
        ("Set workspace-demo-c timezone to the selected option.", {"scope_id": "workspace-demo-c", "generation": 305, "timezone": None, "visible_targets": [], "allowed_effects": ["set_timezone"], "evidence_note": "No selected timezone is visible."}, "missing_evidence"),
        ("Book a flight for workspace-demo-d.", {"scope_id": "workspace-demo-d", "generation": 306, "visible_targets": [], "allowed_effects": []}, "unsupported"),
    ]
    for task, state, reason in yields:
        add(task, state, tool("YIELD", {"reason": reason}))

    for i, (task, state, reason) in enumerate([
        ("For workspace-demo-e at generation 401, turn on email reminders.", {"scope_id": "workspace-demo-e", "generation": 401, "email_reminders": True, "visible_targets": ["toggle_email_reminders"], "allowed_effects": []}, "already_satisfied"),
        ("Do not change anything for workspace-demo-f.", {"scope_id": "workspace-demo-f", "generation": 402, "visible_targets": [], "allowed_effects": []}, "not_requested"),
        ("Leave workspace-demo-g unchanged; no settings action is requested.", {"scope_id": "workspace-demo-g", "generation": 403, "visible_targets": ["save_settings"], "allowed_effects": []}, "not_requested"),
    ]):
        add(task, state, tool("NO_ACTION", {"reason": reason}))

    assert len(examples) == 32, len(examples)
    assert len({example["query"] for example in examples}) == 32
    payload = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in examples)
    OUTPUT_PATH.write_text(payload, encoding="utf-8", newline="\n")
    print(f"wrote {len(examples)} synthetic support examples to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

