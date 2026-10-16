#!/usr/bin/env python3
"""Independent, read-only reconstruction of retained A03 ammo soft transitions."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: reaudit_soft_transitions.py PACKAGE_ROOT OUTPUT_JSON")
    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    checksum_file = root / "SHA256SUMS.txt"
    package_checks = []
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        actual = sha256(root / relative)
        package_checks.append({"path": relative, "expected": expected, "actual": actual, "match": expected == actual})
    if not package_checks or not all(row["match"] for row in package_checks):
        raise AssertionError("original A03 package checksum verification failed")

    report_path = root / "input" / "report.json"
    events_path = root / "input" / "events.jsonl"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    typed = {}
    for event in events:
        if event.get("event") == "typed_observation":
            sequence = event.get("sequence")
            if type(sequence) is not int or sequence in typed:
                raise AssertionError("typed observation sequence invalid or duplicated")
            typed[sequence] = event

    reconstructed = []
    per_decision = []
    for decision_index, decision in enumerate(report["decisions"]):
        expected_count = decision.get("cover_validity_soft_events", 0)
        if type(expected_count) is not int or expected_count < 0:
            raise AssertionError("decision soft-event count is not a nonnegative integer")
        if expected_count == 0:
            continue
        admission = decision["cover_validity_admission"]
        source = admission["source_ammo_signal"]
        source_sequence = source["sequence"]
        invalidation = decision["policy_invalidation"]
        end_sequence = invalidation["sequence"]
        maximum_age_ms = admission["effective"]["max_source_age_ms"]
        hard_minimum = 1
        last_value = source["value"]
        decision_rows = []

        for sequence in range(source_sequence + 1, end_sequence + 1):
            event = typed.get(sequence)
            if event is None:
                raise AssertionError(f"missing typed observation at sequence {sequence}")
            signal = event["signals"]["ammo"]
            if signal.get("status") != "observed" or signal.get("signal_id") != "ammo":
                raise AssertionError(f"unexpected ammo signal at sequence {sequence}")
            if canonical(signal.get("binding")) != canonical(source.get("binding")):
                raise AssertionError(f"binding changed at sequence {sequence}")
            if type(signal.get("sequence")) is not int or signal["sequence"] != sequence:
                raise AssertionError(f"signal sequence mismatch at {sequence}")
            if type(signal.get("capture_ns")) is not int or signal["capture_ns"] <= source["capture_ns"]:
                raise AssertionError(f"capture clock did not advance at sequence {sequence}")
            age_ms = (signal["capture_ns"] - source["capture_ns"]) / 1_000_000
            if age_ms > maximum_age_ms:
                break
            value = signal.get("value")
            if type(value) is not int or not 0 <= value <= 1_000_000:
                raise AssertionError(f"invalid ammo value at sequence {sequence}")
            if value < hard_minimum:
                break
            if value != source["value"] and value != last_value:
                row = {
                    "decision_index": decision_index,
                    "iteration": decision["iteration"],
                    "sequence": sequence,
                    "signal_id": "ammo",
                    "source_value": source["value"],
                    "current_value": value,
                    "source_age_ms": age_ms,
                }
                decision_rows.append(row)
                last_value = value
            elif value == source["value"]:
                last_value = value

        if len(decision_rows) != expected_count:
            raise AssertionError(
                f"decision {decision_index}: reconstructed {len(decision_rows)} transitions, "
                f"report records {expected_count}"
            )
        reconstructed.extend(decision_rows)
        per_decision.append({
            "decision_index": decision_index,
            "iteration": decision["iteration"],
            "reported_count": expected_count,
            "reconstructed_count": len(decision_rows),
            "sequences": [row["sequence"] for row in decision_rows],
        })

    reported_total = report["cover_validity_soft_events"]
    if type(reported_total) is not int or len(reconstructed) != reported_total:
        raise AssertionError("reconstructed total does not equal report cumulative count")
    selected = sorted(
        decision["cover_validity_latest_soft_event"]["sequence"]
        for decision in report["decisions"]
        if decision.get("cover_validity_latest_soft_event")
    )
    reconstructed_sequences = [row["sequence"] for row in reconstructed]
    result = {
        "schema": "wslc-typed-policy-replay-a03-soft-transition-supplement-v1",
        "disposition": "PASS_RAW_SOFT_TRANSITION_RECONSTRUCTION_SCOPED",
        "method": "manual raw-only transition reconstruction; imports neither candidate nor guard implementation",
        "original_wslc_allocation_rerun": False,
        "original_candidate_or_audit_modified": False,
        "package_manifest_entries_verified": len(package_checks),
        "package_manifest_all_match": all(row["match"] for row in package_checks),
        "report_sha256": sha256(report_path),
        "events_sha256": sha256(events_path),
        "reported_cumulative_soft_count": reported_total,
        "reconstructed_soft_transition_count": len(reconstructed),
        "selected_latest_soft_sequences": selected,
        "complete_reconstructed_soft_sequences": reconstructed_sequences,
        "previously_unselected_soft_sequences": sorted(set(reconstructed_sequences) - set(selected)),
        "per_decision": per_decision,
        "soft_transitions": reconstructed,
        "scope_limit": (
            "Reconstructs retained ammo value transitions under the frozen source signal, binding, "
            "hard minimum, age limit, and raw typed sequence. Does not add a WSLc result, production "
            "wiring, live invalidation, task effect, recovery, survival, or product claim."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "disposition", "package_manifest_entries_verified", "reported_cumulative_soft_count",
        "reconstructed_soft_transition_count", "selected_latest_soft_sequences",
        "complete_reconstructed_soft_sequences", "previously_unselected_soft_sequences",
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
