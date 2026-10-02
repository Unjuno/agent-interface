"""Independent raw-only audit; does not import the candidate or ledger."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"
RAW = HERE / "results" / "t0-01" / "raw.json"
OUT = HERE / "results" / "t0-01" / "audit.json"
ALLOCATION = "MAP01-REPEATED-KEY-PULSE-OCCUPANCY-59-T0-20261001-01"
MAIN = "f54e7665f099e78d11cff9ca28e812782aac33d1"
SOURCE_COMMIT = "3983343f6773f118b92652c5e7f72a34b9eda7a2"


def oracle(events):
    if not isinstance(events, list) or len(events) != 3:
        return None, "event_count"
    keyed = [row for row in events if isinstance(row, dict) and row.get("kind") == "key_interval"]
    empty = [row for row in events if isinstance(row, dict) and row.get("kind") == "verified_empty"]
    if len(keyed) != 2 or len(empty) != 1:
        return None, "row_kinds"
    action, epoch = keyed[0].get("action_id"), keyed[0].get("epoch")
    if action != "act-repeat-1" or type(epoch) is not int or epoch != 9:
        return None, "identity"
    pulses = []
    for row in keyed:
        if (row.get("action_id") != action or type(row.get("epoch")) is not int
                or row.get("epoch") != epoch or row.get("key") != "W"
                or row.get("source") != "input-owner-v11"):
            return None, "pulse_identity"
        pulse_id = row.get("pulse_id")
        if not isinstance(pulse_id, str) or not pulse_id or any(p["pulse_id"] == pulse_id for p in pulses):
            return None, "pulse_id"
        names = ("press_request_ns", "press_sync_ns", "down_sample_ns",
                 "release_request_ns", "release_sync_ns", "up_sample_ns")
        values = [row.get(name) for name in names]
        if any(type(value) is not int or value < 0 for value in values):
            return None, "timestamp_type"
        p_req, p_sync, d_sample, r_req, r_sync, u_sample = values
        if not (p_req <= p_sync <= d_sample < r_req <= r_sync <= u_sample):
            return None, "timestamp_order"
        pulses.append({"pulse_id": pulse_id, "action_id": action, "epoch": epoch,
                       "key": "W", "lower_ns": r_req - p_sync,
                       "upper_ns": r_sync - p_req,
                       "press_request_ns": p_req, "up_sample_ns": u_sample})
    if pulses[0]["up_sample_ns"] >= pulses[1]["press_request_ns"]:
        return None, "pulses_not_sequential"
    terminal = empty[0]
    if (terminal.get("action_id") != action or type(terminal.get("epoch")) is not int
            or terminal.get("epoch") != epoch or terminal.get("source") != "xquerykeymap"
            or terminal.get("keys_down") != [] or type(terminal.get("timestamp_ns")) is not int
            or any(p["up_sample_ns"] > terminal["timestamp_ns"] for p in pulses)):
        return None, "terminal"
    return pulses, None


def main():
    fixture_bytes, raw_bytes = FIXTURE.read_bytes(), RAW.read_bytes()
    fixture, raw = json.loads(fixture_bytes.decode("utf-8")), json.loads(raw_bytes.decode("utf-8"))
    expected, error = oracle(fixture.get("events"))
    candidate = raw.get("candidate_result")
    checks = {
        "allocation": raw.get("allocation_id") == ALLOCATION,
        "main_identity": raw.get("main_sha") == MAIN,
        "candidate_source_identity": raw.get("candidate_source_pr") == 6094 and raw.get("candidate_source_commit") == SOURCE_COMMIT,
        "candidate_once_no_retry": type(raw.get("candidate_invocations")) is int and raw["candidate_invocations"] == 1 and raw.get("retries") == 0,
        "fixture_hash": raw.get("fixture_sha256") == hashlib.sha256(fixture_bytes).hexdigest(),
        "independent_oracle_two_pulses": error is None and len(expected or []) == 2 and all(
            (pulse["lower_ns"], pulse["upper_ns"]) == (20, 40) for pulse in expected or []),
        "candidate_fail_closed_duplicate_key": isinstance(candidate, dict)
            and candidate.get("status") == "UNKNOWN" and candidate.get("intervals") == []
            and "duplicate_or_invalid_key" in candidate.get("reasons", []),
    }
    report = {
        "schema": "map01-repeated-key-pulse-occupancy-audit-v1",
        "status": "PASS_REPRESENTATION_BOUNDARY_SCOPED" if all(checks.values()) else "FAIL_AUDIT",
        "checks": checks,
        "oracle_error": error,
        "oracle_occurrence_bounds": expected,
        "candidate_result": candidate,
        "interpretation": "existing per-key identity cannot encode repeated occurrences; UNKNOWN is fail-closed, not a false duration estimate",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "auditor_imports_candidate": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, sort_keys=True, indent=2) + "\n"
    OUT.write_text(encoded, encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
