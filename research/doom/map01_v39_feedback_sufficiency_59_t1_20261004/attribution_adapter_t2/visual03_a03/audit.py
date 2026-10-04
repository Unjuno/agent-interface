#!/usr/bin/env python3
"""Independent raw-data audit of the visual03 step-scoped batch replay."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(name):
    return [json.loads(line) for line in (HERE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def audit():
    errors = []
    pins = load_json(HERE / "SOURCE_PINS.json")
    for name, expected in pins["source_files"].items():
        copied_name = name.rsplit("/", 1)[-1]
        raw = (HERE / copied_name).read_bytes()
        if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
            errors.append("raw_source_pin_mismatch:" + copied_name)

    samples = load_jsonl("scorer-samples.jsonl")
    events = load_jsonl("scorer-events.jsonl")
    inputs = load_jsonl("input-rows.jsonl")
    original_lines = (HERE / "events.jsonl").read_text(encoding="utf-8").splitlines()
    expected_inputs = [json.loads(line) for line in original_lines if line.strip()
                       and json.loads(line).get("event") in {"input_admission", "input_release_transition"}]
    if inputs != expected_inputs:
        errors.append("derived_input_rows_do_not_match_source_stream")
    admissions = [row for row in inputs if row.get("event") == "input_admission"]
    releases = [row for row in inputs if row.get("event") == "input_release_transition"]
    if len(samples) != 761 or len(events) != 1 or len(admissions) != 19 or len(releases) != 19:
        errors.append("raw_row_count_mismatch")

    def ident(row):
        return tuple(row.get(key) for key in ("owner_id", "intent_token", "id", "step", "key"))

    downs = {ident(row): row for row in admissions}
    ups = {ident(row): row for row in releases}
    if len(downs) != len(admissions) or len(ups) != len(releases) or set(downs) != set(ups):
        errors.append("admission_release_identity_join_mismatch")

    batch_groups = defaultdict(list)
    baseline_groups = defaultdict(list)
    intervals = []
    for identity, release in ups.items():
        down = downs.get(identity, {})
        batch = release.get("release_batch_identifier")
        step = release.get("release_batch_step")
        batch_groups[(identity[0], identity[1], identity[2], batch, step)].append(release)
        baseline_groups[(identity[0], identity[1], identity[2], batch)].append(release)
        receipt = release.get("owner_thread_keyup_receipt", {})
        if release.get("physical_verification_authoritative") is not False or receipt.get("physical_verification_authoritative") is not False:
            errors.append("physical_authority_promoted")
        if release.get("release_batch_complete") is not True or release.get("owner_thread_keyup_verified_after_batch") is not True:
            errors.append("release_batch_not_complete")
        if batch != identity[2] or step != identity[3]:
            errors.append("release_batch_identity_mismatch")
        sync_ns = receipt.get("owner_sync_returned_ns")
        intervals.append({
            "intent_token": identity[1],
            "key": identity[4],
            "start": down.get("admitted_ns", -1),
            "end": sync_ns if type(sync_ns) is int else -1,
            "release_verified": bool(
                receipt.get("server_sync_completed") is True
                and receipt.get("physical_verification_authoritative") is False
                and type(sync_ns) is int
            ),
        })

    malformed_batches = []
    for key, rows in batch_groups.items():
        sizes = {row.get("release_batch_size") for row in rows}
        positions = [row.get("release_batch_position") for row in rows]
        expected = next(iter(sizes)) if len(sizes) == 1 else None
        if expected is None or len(rows) != expected or set(positions) != set(range(expected)):
            malformed_batches.append(key)
    if malformed_batches:
        errors.append("step_scoped_release_batch_incomplete")

    # Independently reconstruct the adapter's former grouping defect: the
    # program-level id is reused across sequential size-one batches.
    baseline_false_holds = []
    for key, rows in baseline_groups.items():
        sizes = {row.get("release_batch_size") for row in rows}
        positions = [row.get("release_batch_position") for row in rows]
        expected = next(iter(sizes)) if len(sizes) == 1 else None
        if expected is None or len(rows) != expected or set(positions) != set(range(expected)):
            baseline_false_holds.append(key)

    sample_times = [row.get("payload", {}).get("sample_ns") for row in samples]
    if any(type(value) is not int for value in sample_times) or sample_times != sorted(sample_times):
        errors.append("scorer_sample_time_order_mismatch")
    event = events[0] if events else {}
    upper = event.get("observed_ns")
    earlier = [value for value in sample_times if type(value) is int and type(upper) is int and value < upper]
    lower = max(earlier) if earlier else None
    event_sequence_in_samples = type(upper) is int and upper in sample_times
    if lower is None or not event_sequence_in_samples or event.get("polarity") != "positive" or event.get("useful") is not True:
        errors.append("positive_event_sample_bracket_mismatch")

    possible_tokens = sorted({
        row["intent_token"] for row in intervals
        if type(lower) is int and type(upper) is int
        and row["start"] <= upper and (not row["release_verified"] or row["end"] > lower)
    })
    covers = []
    for token in possible_tokens:
        usable = sorted((row["start"], row["end"]) for row in intervals
                        if row["intent_token"] == token and row["release_verified"]
                        and row["end"] > lower and row["start"] <= upper)
        cursor = lower
        for start, end in usable:
            if start > cursor:
                break
            cursor = max(cursor, end)
            if cursor >= upper:
                covers.append(token)
                break
    result = load_json(HERE / "out/RESULT.json")
    baseline = result.get("baseline", {})
    candidate = result.get("candidate", {})
    attrs = candidate.get("attributions", [])
    attribution = attrs[0] if len(attrs) == 1 else {}
    if baseline.get("trace_integrity") != "HOLD_INCOMPLETE_RELEASE_BATCH" or not baseline_false_holds:
        errors.append("baseline_batch_hold_not_reproduced")
    if candidate.get("trace_integrity") != "SOURCE_ROWS_JOINED" or candidate.get("counts", {}).get("integrity_flags"):
        errors.append("candidate_source_join_not_clean")
    if possible_tokens != ["41a11010ac2d4543bfb8d4f2b4bb8f83"] or covers != possible_tokens:
        errors.append("independent_temporal_coverage_mismatch")
    if attribution.get("status") != "TEMPORALLY_UNIQUE" or attribution.get("intent_token") != (covers[0] if covers else None):
        errors.append("candidate_temporal_association_mismatch")
    if attribution.get("detection_interval_ns") != [lower, upper] or attribution.get("causal_attribution") != "NOT_ESTABLISHED":
        errors.append("candidate_scope_fields_mismatch")

    return {
        "audit": "PASS_SCOPED_VISUAL03_TEMPORAL_ASSOCIATION" if not errors else "FAIL_VISUAL03_AUDIT",
        "errors": errors,
        "counts": {"samples": len(samples), "events": len(events), "admissions": len(admissions), "release_transitions": len(releases), "step_scoped_batches": len(batch_groups)},
        "baseline_false_incomplete_batch_groups": len(baseline_false_holds),
        "detection_interval_ns": [lower, upper],
        "possible_intent_tokens": possible_tokens,
        "full_bracket_covering_tokens": sorted(covers),
        "candidate_status": attribution.get("status"),
        "causal_attribution": attribution.get("causal_attribution"),
        "release_basis": "Nested owner-thread XSync receipt only; physical_verification_authoritative=false.",
        "scope": "Temporal association only. Event onset and causal input effect are not established; no physical key-up timing, threat recovery, or new live qualification.",
    }


if __name__ == "__main__":
    import sys
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if not result["errors"] else 1)
