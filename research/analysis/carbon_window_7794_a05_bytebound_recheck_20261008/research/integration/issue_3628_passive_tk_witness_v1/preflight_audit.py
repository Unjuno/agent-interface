"""Adversarial controls for the passive Tk key-event witness gate."""
from __future__ import annotations

import json
from pathlib import Path
import sys


def witness_gate(events: list[dict], effect: dict | None, marker: str) -> bool:
    chord = [row.get("keysym") for row in events
             if row.get("bindtag") == "AgentInterfacePassiveAudit"]
    exact = chord == ["Control_L", "s"]
    independent_effect = effect == {"saved": True, "text": marker}
    return exact and independent_effect


def main() -> int:
    root = Path(sys.argv[1])
    allocation = json.loads((root / "allocation.json").read_text())
    events = [json.loads(line) for line in (root / "fixture-events.jsonl").read_text().splitlines()]
    effect = json.loads((root / "fixture-effect.json").read_text())
    marker = allocation["marker"]
    witness = [row for row in events if row.get("bindtag") == "AgentInterfacePassiveAudit"
               and row.get("keysym") in {"Control_L", "s"}]

    cases = {
        "valid_ordered_once_with_effect": witness_gate(witness, effect, marker),
        "missing_control": not witness_gate([r for r in witness if r.get("keysym") != "Control_L"], effect, marker),
        "duplicate_control": not witness_gate(witness + [witness[0]], effect, marker),
        "reversed_order": not witness_gate(list(reversed(witness)), effect, marker),
        "wrong_keysym": not witness_gate([dict(witness[0]), {**witness[1], "keysym": "x"}], effect, marker),
        "logged_chord_without_effect": not witness_gate(witness, None, marker),
        "effect_without_preregistered_event": not witness_gate([], effect, marker),
    }
    result = {"schema": "issue-3628/preflight-audit-v1", "allocation_id": allocation["allocation_id"],
              "marker": marker, "witness": witness, "effect": effect,
              "controls": cases, "passed": all(cases.values())}
    out = root / "preflight-audit.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
