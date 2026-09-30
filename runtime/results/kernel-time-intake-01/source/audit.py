"""Independent, source-free oracle for the retained #5215 probe record."""
from __future__ import annotations

import json
from pathlib import Path


def audit(record: dict[str, bool]) -> dict[str, object]:
    required_controls = {
        "execution_end_700": True,
        "execution_end_999": True,
        "execution_wrong_command": False,
        "effect_at_700": True,
        "effect_at_701": True,
    }
    errors = [key for key, expected in required_controls.items() if record.get(key) is not expected]
    gap = any(record.get(key) is True for key in (
        "execution_end_1000", "execution_end_1001", "effect_at_499", "effect_at_699"
    ))
    return {
        "errors": errors,
        "invalid_temporal_cases_accepted": [
            key for key in ("execution_end_1000", "execution_end_1001", "effect_at_499", "effect_at_699")
            if record.get(key) is True
        ],
        "disposition": "PASS_TEMPORAL_RECEIPT_GAP_SCOPED" if not errors and gap else (
            "NO_GAP_OBSERVED" if not errors else "HOLD_AUDIT_MISMATCH"
        ),
    }


if __name__ == "__main__":
    data = json.loads(Path(__file__).with_name("probe-output.json").read_text(encoding="utf-8"))
    print(json.dumps(audit(data), sort_keys=True, separators=(",", ":")))
