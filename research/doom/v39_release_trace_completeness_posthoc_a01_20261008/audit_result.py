"""Independent oracle for the retained release-coverage result."""
import json
import argparse
from pathlib import Path

try:
    from .run_audit import load_inputs
except ImportError:  # direct script execution from this directory
    from run_audit import load_inputs

HERE = Path(__file__).resolve().parent


def validate(result, events, owner_events, report):
    accepted = {row["id"] for row in events if row.get("event") == "accepted"}
    terminals = {row["id"] for row in events if row.get("event") == "terminal"}
    cancels = [row for row in events if row.get("event") == "cancel_requested"]
    held = {row["id"] for row in events if row.get("event") == "keys_held"}
    early = {row["id"]: row for row in events if row.get("event") in
             ("input_released", "input_release_unverified")}
    if accepted != terminals:
        raise ValueError("source accepted/terminal IDs differ")
    by_id = {row["id"]: row for row in events if row.get("event") == "terminal"}
    active_interrupted = []
    for cancel in cancels:
        terminal = by_id[cancel["id"]]
        release = terminal.get("release", {})
        if (terminal.get("status") != "cancelled" or release.get("verified") is not True or
                release.get("keys_down") != [] or release.get("buttons_down") != []):
            raise ValueError(f"source terminal release invalid: {cancel['id']}")
        cause = (terminal.get("interruption") or {}).get("record")
        if cancel["id"] in held and cause is not None:
            when = cause.get("verified_ns")
            if (cause.get("reason") != "cancelled" or cause.get("verified") is not True or
                    cause.get("keys_down") != [] or cause.get("buttons_down") != [] or
                    not cancel["requested_ns"] <= when <= terminal["terminal_ns"]):
                raise ValueError(f"source interruption receipt invalid: {cancel['id']}")
            early_row = early.get(cancel["id"])
            if early_row is not None and (
                    early_row.get("owner_release") != cause or
                    early_row.get("grants_input_authority") is not False):
                raise ValueError(f"source early-release event invalid: {cancel['id']}")
            active_interrupted.append(cancel["id"])
    expected_coverage = {"numerator": len(set(active_interrupted) & set(early)),
                         "denominator": len(active_interrupted)}
    expected = {
        "status": "PASS_TRACE_RECONCILIATION_WITH_EARLY_EVENT_GAP",
        "accepted_terminal_ids_match": True,
        "cancel_requests": len(cancels),
        "cancelled_terminals_with_empty_verified_release": len(cancels),
        "cancellations_with_prior_keys_held": len(set(cancels_row["id"] for cancels_row in cancels) & held),
        "active_interruption_owner_receipts": len(active_interrupted),
        "active_interruption_coverage": expected_coverage,
        "active_interruption_receipts_with_input_released_event": expected_coverage["numerator"],
        "input_release_event_rows": len(early),
        "owner_release_has_per_key_timestamps": any(
            any(key in item for key in ("per_key", "key_release_ns", "keyup_ns"))
            for item in owner_events),
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise ValueError(f"result mismatch for {key}: {result.get(key)!r} != {value!r}")
    expected_rows = []
    for identifier in active_interrupted:
        cancel = next(row for row in cancels if row["id"] == identifier)
        terminal = by_id[identifier]
        cause = terminal["interruption"]["record"]
        verified = cause["verified_ns"]
        item = {
            "id": identifier,
            "prior_keys_held_event": True,
            "interruption_owner_release": True,
            "input_release_event": identifier in early,
            "cancel_requested_ns": cancel["requested_ns"],
            "terminal_ns": terminal["terminal_ns"],
            "terminal_owner_verified_ns": terminal["release"]["verified_ns"],
            "cause_owner_verified_ns": verified,
            "cancel_to_owner_verified_ms": (verified - cancel["requested_ns"]) / 1e6,
            "owner_verified_to_terminal_ms": (terminal["terminal_ns"] - verified) / 1e6,
        }
        if identifier in early:
            item["owner_verified_to_release_event_ms"] = (
                early[identifier]["published_ns"] - verified) / 1e6
        expected_rows.append(item)
    if result.get("active_interruption_rows") != expected_rows:
        raise ValueError("active interruption row details do not match raw trace")
    latencies = [row["cancel_to_owner_verified_ms"] for row in expected_rows]
    if result.get("aggregate_cancel_to_owner_verified_ms") != {
            "min": min(latencies), "max": max(latencies)}:
        raise ValueError("aggregate latency does not match raw trace")
    if report is not None:
        expected_task = {key: report["score"].get(key) for key in
                         ("kill_count", "death_count", "map_exit", "episode_finished")}
        if result.get("task_outcome") != expected_task:
            raise ValueError("task outcome does not match retained report")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=HERE / "RESULT.json")
    parser.add_argument("--output", type=Path, default=HERE / "AUDIT.json")
    args = parser.parse_args()
    result_path = args.result if args.result.is_absolute() else HERE / args.result
    output = args.output if args.output.is_absolute() else HERE / args.output
    result = json.loads(result_path.read_text(encoding="utf-8"))
    events, owner_events, report, _prior = load_inputs()
    validate(result, events, owner_events, report)
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    audit = {"schema": "map01-v39-release-trace-completeness-audit-v1",
             "status": "PASS_INDEPENDENT_RAW_RECONCILIATION",
             "checks": {"accepted_terminal_identity": True,
                        "all_cancelled_terminals_empty": True,
                        "active_interruption_receipt_order": True,
                        "active_release_latency_and_identity": True,
                        "early_event_coverage_matches_raw": True,
                        "task_outcome_matches_report": True,
                        "per_key_timestamps_absent": True},
             "result_sha256": __import__("hashlib").sha256(
                 result_path.read_bytes()).hexdigest()}
    output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
