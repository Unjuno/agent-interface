"""Read-only replay of one retained scorer stream through the frozen A01 helper."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
for relative, expected in FREEZE["sources"].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"source hash mismatch: {relative}: {actual}")
for relative, expected in FREEZE["package_sources"].items():
    actual = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"package hash mismatch: {relative}: {actual}")

helper_path = ROOT / "research/doom/scorer_feedback_attribution_59_t0_a01_20261004/scorer_feedback_attribution_v1.py"
spec = importlib.util.spec_from_file_location("frozen_attribution_a01", helper_path)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)

base = ROOT / "research/doom/map01_r133_recovery_coast_t1_v1/scorer_wait_construction_v1/results/formal-01"
sample_rows = [json.loads(line) for line in (base / "scorer/scorer-samples.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
samples = [row["payload"] for row in sample_rows]
events = [json.loads(line) for line in (base / "scorer/scorer-events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
raw = json.loads((base / "RAW.json").read_text(encoding="utf-8"))
original_audit = json.loads((base / "AUDIT.json").read_text(encoding="utf-8"))

event_hash = hashlib.sha256((base / "scorer/scorer-events.jsonl").read_bytes()).hexdigest()
positive = [event for event in events if event.get("polarity") == "positive" and event.get("useful") is True]
negative = [event for event in events if event.get("polarity") == "negative"]
attributions = helper.attribute_positive_events(samples, events, intervals=[])
result = {
    "schema": "scorer-feedback-attribution-t0-a02-v1",
    "status": "PASS_SCOPED" if (
        len(positive) == FREEZE["expected"]["positive_scorer_events"]
        and len(negative) == FREEZE["expected"]["negative_scorer_events"]
        and all(row.get("observed_ns") in {sample.get("sample_ns") for sample in samples} for row in events)
        and "plan/actuation binding" in original_audit.get("scope", "")
        and len(attributions) == len(positive)
        and all(row["status"] == "UNRESOLVED" and row["intent_token"] is None for row in attributions)
    ) else "FAIL",
    "source_hashes": FREEZE["sources"],
    "sample_count": len(samples),
    "positive_event_count": len(positive),
    "negative_event_count": len(negative),
    "event_sha256": event_hash,
    "candidate_exit_code": raw.get("candidate_exit_code"),
    "historical_audit_status": original_audit.get("status"),
    "historical_scope": original_audit.get("scope"),
    "positive_event_attribution": attributions,
    "negative_event_timestamps_ns": [row.get("observed_ns") for row in negative],
    "actuation_intervals_supplied": 0,
    "causation_claim": "NOT_ESTABLISHED",
    "scope": "saved scorer-wait construction stream only; no MAP01/controller/game/model/input replay",
}
(HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
if result["status"] != "PASS_SCOPED":
    raise SystemExit(1)
