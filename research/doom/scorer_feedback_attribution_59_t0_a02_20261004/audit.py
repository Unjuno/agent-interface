"""Independent saved-result audit; does not run the attribution helper."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def audit():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["sources"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, (relative, actual)
    for relative, expected in freeze["package_sources"].items():
        actual = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        assert actual == expected, (relative, actual)
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    assert result["status"] == "PASS_SCOPED"
    assert result["source_hashes"] == freeze["sources"]
    assert result["sample_count"] == 18
    assert result["positive_event_count"] == 1
    assert result["negative_event_count"] == 1
    assert result["actuation_intervals_supplied"] == 0
    assert result["historical_audit_status"] == "PASS_SCORER_EVENTS_RETAINED_DURING_COMMAND_WAIT_CONSTRUCTION"
    assert "plan/actuation binding" in result["historical_scope"]
    assert len(result["positive_event_attribution"]) == 1
    row = result["positive_event_attribution"][0]
    assert row["status"] == "UNRESOLVED"
    assert row["intent_token"] is None
    assert row["causal_attribution"] == "NOT_ESTABLISHED"
    return {
        "schema": "scorer-feedback-attribution-t0-a02-audit-v1",
        "status": "PASS_SCOPED",
        "independent_checks": ["frozen inputs", "18 exact scorer samples", "one positive and one negative event", "historical no-actuation-binding scope", "positive outcome remains unresolved", "no causal promotion"],
        "scope": "saved construction artifact only",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
