"""Repair audit v2: derive sample count from exact frozen raw serialization."""
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

    base = ROOT / "research/doom/map01_r133_recovery_coast_t1_v1/scorer_wait_construction_v1/results/formal-01"
    raw = json.loads((base / "RAW.json").read_text(encoding="utf-8"))
    original = json.loads((base / "AUDIT.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (base / "scorer/scorer-events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    sample_rows = [json.loads(line) for line in (base / "scorer/scorer-samples.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))

    assert events == raw["events"]
    assert sample_rows == raw["samples"]
    samples = [row["payload"] for row in sample_rows]
    sample_times = {row["sample_ns"] for row in samples}
    assert len(sample_rows) == result["sample_count"] == len(raw["samples"])
    assert len(events) == len(raw["events"]) == 2
    assert all(row.get("observed_ns") in sample_times for row in events)
    assert sum(row.get("polarity") == "positive" and row.get("useful") is True for row in events) == 1
    assert sum(row.get("polarity") == "negative" for row in events) == 1
    assert "plan/actuation binding" in original.get("scope", "")
    assert result["status"] == "PASS_SCOPED"
    assert result["positive_event_attribution"][0]["status"] == "UNRESOLVED"
    assert result["positive_event_attribution"][0]["intent_token"] is None
    assert result["positive_event_attribution"][0]["causal_attribution"] == "NOT_ESTABLISHED"
    assert result["causation_claim"] == "NOT_ESTABLISHED"

    return {
        "schema": "scorer-feedback-attribution-t0-a02-audit-v2",
        "status": "PASS_SCOPED",
        "source_sample_count": len(raw["samples"]),
        "original_audit_v1": "FAIL_AUDIT_EXPECTED_18_OBSERVED_13",
        "independent_checks": ["frozen source hashes", "raw/file event equality", "raw/file sample equality", "event-to-sample timestamp membership", "positive event remains unresolved without action intervals", "no causal promotion"],
        "scope": "saved scorer-wait construction stream only",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
