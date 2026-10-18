"""Posthoc audit of retained V39 cancel/release event coverage; no rerun."""
import hashlib
import argparse
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
MAIN = FREEZE["frozen_main"]


def frozen_bytes(path):
    spec = FREEZE["inputs"][path]
    data = subprocess.check_output(["git", "show", f"{MAIN}:{path}"])
    if (len(data) != spec["bytes"] or hashlib.sha256(data).hexdigest() != spec["sha256"] or
            subprocess.check_output(["git", "rev-parse", f"{MAIN}:{path}"], text=True).strip()
            != spec["git_blob"]):
        raise ValueError(f"frozen input identity mismatch: {path}")
    return data


def load_inputs():
    paths = list(FREEZE["inputs"])
    loaded = {path: frozen_bytes(path) for path in paths}
    events_path = next(path for path in paths if path.endswith("events.jsonl"))
    owner_path = next(path for path in paths if path.endswith("owner-events.json"))
    report_path = next(path for path in paths if path.endswith("report.json"))
    audit_path = next(path for path in paths if path.endswith("audit-v2.json"))
    events = [json.loads(line) for line in loaded[events_path].decode().splitlines()]
    owner_events = json.loads(loaded[owner_path])
    report = json.loads(loaded[report_path])
    prior_audit = json.loads(loaded[audit_path])
    return events, owner_events, report, prior_audit


def analyze(events, owner_events, report, prior_audit):
    def unique_id_map(event_name):
        rows = [row for row in events if row.get("event") == event_name]
        identifiers = [row.get("id") for row in rows]
        if (any(not isinstance(identifier, str) or not identifier for identifier in identifiers) or
                len(identifiers) != len(set(identifiers))):
            raise ValueError(f"{event_name} event IDs must be nonempty and unique")
        return {row["id"]: row for row in rows}

    accepted = unique_id_map("accepted")
    terminals = unique_id_map("terminal")
    cancels = [row for row in events if row.get("event") == "cancel_requested"]
    cancel_ids = [row.get("id") for row in cancels]
    if (any(not isinstance(identifier, str) or not identifier for identifier in cancel_ids) or
            len(cancel_ids) != len(set(cancel_ids))):
        raise ValueError("cancel_requested event IDs must be nonempty and unique")
    release_events = [row for row in events
                      if row.get("event") in ("input_released", "input_release_unverified")]
    release_ids = [row.get("id") for row in release_events]
    if (any(not isinstance(identifier, str) or not identifier for identifier in release_ids) or
            len(release_ids) != len(set(release_ids))):
        raise ValueError("release event IDs must be nonempty and unique")
    release_rows = {row["id"]: row for row in release_events
                    if row.get("event") == "input_released"}
    unverified_release_rows = {row["id"]: row for row in release_events
                               if row.get("event") == "input_release_unverified"}
    if set(release_rows) & set(unverified_release_rows):
        raise ValueError("an ID cannot have both verified and unverified release events")
    if set(release_ids) - set(terminals):
        raise ValueError("release event references an ID without a terminal")
    held_ids = {row["id"] for row in events if row.get("event") == "keys_held"}
    interrupted = []
    cancellation_rows = []
    for cancel in cancels:
        identifier = cancel["id"]
        terminal = terminals.get(identifier)
        if terminal is None:
            raise ValueError(f"cancel lacks terminal: {identifier}")
        terminal_release = terminal.get("release", {})
        requested_ns = cancel.get("requested_ns")
        terminal_ns = terminal.get("terminal_ns")
        verified_ns = terminal_release.get("verified_ns")
        if (terminal.get("status") != "cancelled" or terminal_release.get("verified") is not True or
                terminal_release.get("keys_down") != [] or terminal_release.get("buttons_down") != [] or
                type(requested_ns) is not int or type(verified_ns) is not int or
                type(terminal_ns) is not int or not requested_ns <= verified_ns <= terminal_ns):
            raise ValueError(f"cancel terminal is not verified empty: {identifier}")
        cause = (terminal.get("interruption") or {}).get("record")
        active = identifier in held_ids
        early = release_rows.get(identifier)
        row = {
            "id": identifier,
            "prior_keys_held_event": active,
            "interruption_owner_release": cause is not None,
            "input_release_event": early is not None,
            "input_release_unverified_event": identifier in unverified_release_rows,
            "cancel_requested_ns": requested_ns,
            "terminal_ns": terminal_ns,
            "terminal_owner_verified_ns": verified_ns,
        }
        if cause is not None:
            if (cause.get("event") != "owner_release" or cause.get("verified") is not True or
                    cause.get("keys_down") != [] or cause.get("buttons_down") != []):
                raise ValueError(f"interruption receipt is not verified empty: {identifier}")
            verified = cause.get("verified_ns")
            if not (cancel.get("requested_ns") <= verified <= terminal.get("terminal_ns")):
                raise ValueError(f"interruption timestamps out of order: {identifier}")
            row["cause_owner_verified_ns"] = verified
            row["cancel_to_owner_verified_ms"] = (verified - cancel["requested_ns"]) / 1e6
            row["owner_verified_to_terminal_ms"] = (terminal["terminal_ns"] - verified) / 1e6
            if early is not None:
                early_owner = early.get("owner_release", {})
                if early_owner != cause or early.get("grants_input_authority") is not False:
                    raise ValueError(f"early release event does not match owner cause: {identifier}")
                row["owner_verified_to_release_event_ms"] = (
                    early.get("published_ns") - verified) / 1e6
            if active:
                interrupted.append(row)
        cancellation_rows.append(row)

    if set(accepted) != set(terminals):
        raise ValueError("accepted/terminal ID sets differ")
    if len(cancels) != 7 or not prior_audit.get("formal_pass"):
        raise ValueError("unexpected retained allocation cardinality or prior audit status")
    if report.get("score", {}).get("episode_finished") is not False:
        raise ValueError("unexpected retained task outcome")
    event_types = {row.get("event") for row in events}
    return {
        "schema": "map01-v39-release-trace-completeness-result-v2",
        "status": "PASS_TRACE_RECONCILIATION_WITH_EARLY_EVENT_GAP",
        "main_commit": MAIN,
        "allocation_id": FREEZE["allocation_id"],
        "prior_audit_formal_pass": prior_audit["formal_pass"],
        "accepted_terminal_ids_match": True,
        "cancel_requests": len(cancels),
        "cancelled_terminals_with_empty_verified_release": len(cancellation_rows),
        "cancellations_with_prior_keys_held": sum(row["prior_keys_held_event"] for row in cancellation_rows),
        "active_interruption_owner_receipts": len(interrupted),
        "active_interruption_receipts_with_input_released_event": sum(
            row["input_release_event"] for row in interrupted),
        "active_interruption_coverage": {
            "numerator": sum(row["input_release_event"] for row in interrupted),
            "denominator": len(interrupted),
        },
        "active_interruption_rows": interrupted,
        "all_cancellation_rows": cancellation_rows,
        "aggregate_cancel_to_owner_verified_ms": {
            "min": min(row["cancel_to_owner_verified_ms"] for row in interrupted),
            "max": max(row["cancel_to_owner_verified_ms"] for row in interrupted),
        },
        "input_release_event_rows": len(release_rows),
        "input_release_unverified_event_rows": len(unverified_release_rows),
        "per_key_release_measurement_events": len(event_types.intersection(
            {"input_release_measurement", "input_release_transition"})),
        "owner_release_has_per_key_timestamps": any(
            any(key in item for key in ("per_key", "key_release_ns", "keyup_ns"))
            for item in owner_events),
        "independent_useful_feedback_timestamp": False,
        "task_outcome": {
            "kill_count": report["score"].get("kill_count"),
            "death_count": report["score"].get("death_count"),
            "map_exit": report["score"].get("map_exit"),
            "episode_finished": report["score"].get("episode_finished"),
        },
        "decision": "Aggregate owner/terminal release reconciles for all cancellations. Early input_released coverage is 1/3 for prior-key-held interrupted programs; two cover interruptions appear only in terminal receipts. This is telemetry coverage evidence, not a failed release. Per-key up time, useful application feedback, and task completion remain unmeasured.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "RESULT.json")
    args = parser.parse_args()
    events, owner_events, report, prior_audit = load_inputs()
    result = analyze(events, owner_events, report, prior_audit)
    output = args.output if args.output.is_absolute() else HERE / args.output
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
