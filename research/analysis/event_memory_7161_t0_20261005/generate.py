"""Create five same-looking terminal frames with distinct action histories."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = {
    "not_run": [],
    "pending": [
        {"kind": "action_dispatch", "action": "save", "receipt": "dispatch-1"},
        {"kind": "effect_prediction", "value": "saved", "source": "model"},
    ],
    "success": [
        {"kind": "action_dispatch", "action": "save", "receipt": "dispatch-1"},
        {"kind": "effect_observation", "value": "saved", "source": "ui-receipt-1"},
    ],
    "success_then_revert": [
        {"kind": "action_dispatch", "action": "save", "receipt": "dispatch-1"},
        {"kind": "effect_observation", "value": "saved", "source": "ui-receipt-1"},
        {"kind": "external_change_observation", "value": "unsaved", "source": "ui-receipt-2"},
    ],
    "failed_action": [
        {"kind": "action_dispatch", "action": "save", "receipt": "dispatch-1"},
        {"kind": "effect_observation", "value": "save_rejected", "source": "ui-receipt-1"},
    ],
}
raw = {"schema": "event-memory-t0-v1", "cases": [
    {"case_id": key, "final_visual_state": "dialog_closed", "events": events}
    for key, events in CASES.items()
]}
(HERE / "INPUT.json").write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps({"cases": len(CASES), "final_state_unique_values": 1,
                  "events": sum(map(len, CASES.values()))}, sort_keys=True))
