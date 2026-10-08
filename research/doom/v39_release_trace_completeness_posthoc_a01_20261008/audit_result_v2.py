"""Full-field independent verifier for the retained V39 result (no rerun)."""
import hashlib
import json
import argparse
from pathlib import Path

try:
    from .run_audit import FREEZE, load_inputs
except ImportError:
    from run_audit import FREEZE, load_inputs

HERE = Path(__file__).resolve().parent


def reconstruct(events, owner_events, report, prior_audit):
    """Reconstruct every result claim directly from frozen source rows."""
    def indexed(event_name):
        rows = [row for row in events if row.get("event") == event_name]
        ids = [row.get("id") for row in rows]
        if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"invalid or duplicate {event_name} IDs")
        return {row["id"]: row for row in rows}

    accepted = indexed("accepted")
    terminals = indexed("terminal")
    cancels = indexed("cancel_requested")
    releases = [r for r in events if r.get("event") in
                ("input_released", "input_release_unverified")]
    release_ids = [r.get("id") for r in releases]
    if any(not isinstance(i, str) or not i for i in release_ids) or len(release_ids) != len(set(release_ids)):
        raise ValueError("invalid or duplicate release IDs")
    early = {r["id"]: r for r in releases if r["event"] == "input_released"}
    unverified = {r["id"]: r for r in releases if r["event"] == "input_release_unverified"}
    if set(early) & set(unverified) or set(release_ids) - set(terminals):
        raise ValueError("release identity inconsistency")
    if set(accepted) != set(terminals):
        raise ValueError("accepted/terminal ID sets differ")
    held = {r["id"] for r in events if r.get("event") == "keys_held"}
    all_rows, active_rows = [], []
    for ident, cancel in cancels.items():
        term = terminals.get(ident)
        if term is None:
            raise ValueError(f"cancel lacks terminal: {ident}")
        rel = term.get("release", {})
        if term.get("status") != "cancelled" or rel.get("verified") is not True or rel.get("keys_down") != [] or rel.get("buttons_down") != []:
            raise ValueError(f"terminal release invalid: {ident}")
        cause = (term.get("interruption") or {}).get("record")
        active = ident in held
        row = {"id": ident, "prior_keys_held_event": active,
               "interruption_owner_release": cause is not None,
               "input_release_event": ident in early,
               "input_release_unverified_event": ident in unverified,
               "cancel_requested_ns": cancel.get("requested_ns"),
               "terminal_ns": term.get("terminal_ns"),
               "terminal_owner_verified_ns": rel.get("verified_ns")}
        if cause is not None:
            when = cause.get("verified_ns")
            if (cause.get("event") != "owner_release" or cause.get("verified") is not True or
                    cause.get("keys_down") != [] or cause.get("buttons_down") != [] or
                    not cancel.get("requested_ns") <= when <= term.get("terminal_ns")):
                raise ValueError(f"interruption receipt invalid: {ident}")
            row["cause_owner_verified_ns"] = when
            row["cancel_to_owner_verified_ms"] = (when - cancel["requested_ns"]) / 1e6
            row["owner_verified_to_terminal_ms"] = (term["terminal_ns"] - when) / 1e6
            if ident in early:
                er = early[ident]
                if er.get("owner_release") != cause or er.get("grants_input_authority") is not False:
                    raise ValueError(f"early release mismatch: {ident}")
                row["owner_verified_to_release_event_ms"] = (er["published_ns"] - when) / 1e6
            if active:
                active_rows.append(row)
        all_rows.append(row)
    if len(cancels) != 7 or prior_audit.get("formal_pass") is not True:
        raise ValueError("frozen allocation/prior audit expectation mismatch")
    if report.get("score", {}).get("episode_finished") is not False:
        raise ValueError("unexpected task outcome")
    event_types = {r.get("event") for r in events}
    latencies = [r["cancel_to_owner_verified_ms"] for r in active_rows]
    numerator = sum(r["input_release_event"] for r in active_rows)
    return {
        "schema": "map01-v39-release-trace-completeness-result-v2",
        "status": "PASS_TRACE_RECONCILIATION_WITH_EARLY_EVENT_GAP",
        "main_commit": FREEZE["frozen_main"],
        "allocation_id": FREEZE["allocation_id"],
        "prior_audit_formal_pass": prior_audit["formal_pass"],
        "accepted_terminal_ids_match": True,
        "cancel_requests": len(cancels),
        "cancelled_terminals_with_empty_verified_release": len(all_rows),
        "cancellations_with_prior_keys_held": sum(r["prior_keys_held_event"] for r in all_rows),
        "active_interruption_owner_receipts": len(active_rows),
        "active_interruption_receipts_with_input_released_event": numerator,
        "active_interruption_coverage": {"numerator": numerator, "denominator": len(active_rows)},
        "active_interruption_rows": active_rows,
        "all_cancellation_rows": all_rows,
        "aggregate_cancel_to_owner_verified_ms": {"min": min(latencies), "max": max(latencies)},
        "input_release_event_rows": len(early),
        "input_release_unverified_event_rows": len(unverified),
        "per_key_release_measurement_events": len(event_types.intersection(
            {"input_release_measurement", "input_release_transition"})),
        "owner_release_has_per_key_timestamps": any(any(
            key in item for key in ("per_key", "key_release_ns", "keyup_ns")) for item in owner_events),
        "independent_useful_feedback_timestamp": False,
        "task_outcome": {key: report["score"].get(key) for key in
                         ("kill_count", "death_count", "map_exit", "episode_finished")},
        "decision": "Aggregate owner/terminal release reconciles for all cancellations. Early input_released coverage is 1/3 for prior-key-held interrupted programs; two cover interruptions appear only in terminal receipts. This is telemetry coverage evidence, not a failed release. Per-key up time, useful application feedback, and task completion remain unmeasured.",
    }


def validate(result, events, owner_events, report, prior_audit, freeze=FREEZE):
    if freeze != FREEZE:
        raise ValueError("freeze does not match versioned verifier source")
    expected = reconstruct(events, owner_events, report, prior_audit)
    if result != expected:
        mismatches = sorted(k for k in set(result) | set(expected) if result.get(k) != expected.get(k))
        raise ValueError("result differs from canonical raw reconstruction: " + ", ".join(mismatches))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=HERE / "RESULT.json")
    parser.add_argument("--output", type=Path, default=HERE / "AUDIT_V2.json")
    args = parser.parse_args()
    result_path = args.result if args.result.is_absolute() else HERE / args.result
    output = args.output if args.output.is_absolute() else HERE / args.output
    result = json.loads(result_path.read_text(encoding="utf-8"))
    events, owner, report, prior = load_inputs()
    validate(result, events, owner, report, prior)
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    audit = {"schema": "map01-v39-release-trace-completeness-audit-v3",
             "status": "PASS_FULL_FIELD_RAW_RECONSTRUCTION",
             "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
             "source_commit": FREEZE["frozen_main"],
             "checks": {"every_result_field_reconstructed": True,
                        "all_cancellation_rows_reconstructed": True,
                        "provenance_reconstructed_from_freeze": True}}
    output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
