"""Validate the raw attempt trace, not just summaries derived by its runner."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {"success", "fail_before_accept", "accept_then_raise"}
PREDECESSOR_CANONICAL_SHA256 = "5bb5bdbbe5434eb23441e6e5ae3b32f9380d7cd4ddbc72e37a2e4ebb2f280cc3"


def audit(raw):
    errors = []
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != PREDECESSOR_CANONICAL_SHA256:
        errors.append("predecessor_raw_content")
    if raw.get("source_git_blob") != "7f308a0dd863af534f764f657d603b4921ba1c6a":
        errors.append("source_git_blob")
    if raw.get("schema") != "v39-release-sink-failure-t0-raw-v1":
        errors.append("schema")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != 3:
        errors.append("case_count")
        if not isinstance(rows, list):
            rows = []
    cases = {}
    for row in rows:
        mode = row.get("sink_mode") if isinstance(row, dict) else None
        if mode in cases:
            errors.append("duplicate_case")
        cases[mode] = row
    if set(cases) != EXPECTED:
        errors.append("case_set")
    for mode in EXPECTED & set(cases):
        row = cases[mode]
        attempts = row.get("attempts")
        if not isinstance(attempts, list) or len(attempts) != 2:
            errors.append(mode + ":attempt_count")
            continue
        if [a.get("attempt") for a in attempts] != [1, 2]:
            errors.append(mode + ":attempt_order")
        first, second = attempts
        if first.get("error") != (None if mode == "success" else "OSError"):
            errors.append(mode + ":first_error")
        if second.get("error") is not None or second.get("result") is not None:
            errors.append(mode + ":second_attempt_not_suppressed")
        accepted = row.get("accepted_events")
        expected_accepted = int(mode in ("success", "accept_then_raise"))
        if not isinstance(accepted, list) or len(accepted) != expected_accepted:
            errors.append(mode + ":accepted_event_count")
        elif any(event.get("event") != "input_released" for event in accepted):
            errors.append(mode + ":accepted_event_kind")
        expected_sink_calls = sum(
            1 for attempt in attempts if attempt.get("result") is not None
            or attempt.get("error") is not None
        )
        if row.get("sink_calls") != expected_sink_calls:
            errors.append(mode + ":sink_calls_trace_mismatch")
        derived_suppressed = second.get("result") is None and second.get("error") is None
        if row.get("retry_suppressed") is not derived_suppressed:
            errors.append(mode + ":retry_summary_mismatch")
        if row.get("published_release_marked") is not True:
            errors.append(mode + ":publication_marker")
        unknown = row.get("delivery_unknown_events")
        if not isinstance(unknown, list) or len(unknown) != 0:
            errors.append(mode + ":delivery_unknown_count")
    return {
        "schema": "v39-release-sink-failure-audit-integrity-result-v1",
        "pass": not errors,
        "errors": sorted(set(errors)),
        "finding": "raw traces support retry suppression and missing uncertainty custody"
        if not errors else "AUDIT_FAIL",
        "scope": "saved fake-sink attempt trace consistency; not runtime or delivery evidence",
    }


if __name__ == "__main__":
    result = audit(json.loads((ROOT / "predecessor-raw.json").read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)
