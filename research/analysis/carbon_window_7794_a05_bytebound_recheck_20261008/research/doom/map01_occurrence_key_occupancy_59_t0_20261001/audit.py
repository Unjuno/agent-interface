"""Independent raw-only auditor; does not import candidate.py or occurrence_ledger.py."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.json"
RAW = HERE / "results" / "t0-01" / "raw.json"
OUT = HERE / "results" / "t0-01" / "audit.json"
ALLOCATION = "MAP01-OCCURRENCE-KEY-OCCUPANCY-59-T0-20261001-01"
MAIN = "f0139613cb96d5f2d84e803b75961dff549d58c8"
INVALID_REASON = {
    "missing_interval_id": "duplicate_or_invalid_interval_id",
    "duplicate_interval_id": "duplicate_or_invalid_interval_id",
    "ambiguous_same_key_overlap": "same_key_occurrence_order_ambiguous",
    "cross_action_interval": "key_interval_identity_mismatch",
    "nonempty_terminal": "empty_receipt_not_verified",
    "boolean_timestamp": "invalid_timestamp_order_or_type",
    "missing_release_ack": "missing_or_invalid_key_bracket",
}


def reconstruct(events):
    if not isinstance(events, list) or not events:
        return None, "empty_events"
    presses = [e for e in events if isinstance(e, dict) and e.get("kind") == "key_interval"]
    terminals = [e for e in events if isinstance(e, dict) and e.get("kind") == "verified_empty"]
    if len(presses) + len(terminals) != len(events) or len(terminals) != 1 or not presses:
        return None, "event_kinds_or_terminal_count"
    action, epoch = presses[0].get("action_id"), presses[0].get("epoch")
    if not isinstance(action, str) or not action or type(epoch) is not int:
        return None, "action_epoch"
    found_ids, found = set(), []
    for event in presses:
        if event.get("action_id") != action or type(event.get("epoch")) is not int or event["epoch"] != epoch:
            return None, "action_epoch_mismatch"
        ident, key = event.get("interval_id"), event.get("key")
        if not isinstance(ident, str) or not ident or ident in found_ids:
            return None, "interval_identity"
        found_ids.add(ident)
        if not isinstance(key, str) or not key or event.get("source") != "input-owner-v11":
            return None, "key_or_source"
        fields = ("press_request_ns", "press_sync_ns", "down_sample_ns",
                  "release_request_ns", "release_sync_ns", "up_sample_ns")
        values = [event.get(field) for field in fields]
        if any(type(value) is not int or value < 0 for value in values):
            return None, "timestamp_type"
        p0, p1, pd, r0, r1, ru = values
        if not (p0 <= p1 <= pd < r0 <= r1 <= ru):
            return None, "timestamp_order"
        found.append({"action_id": action, "epoch": epoch, "interval_id": ident,
                      "key": key, "lower_ns": r0 - p1, "upper_ns": r1 - p0,
                      "press_request_ns": p0, "up_sample_ns": ru})
    grouped = {}
    for interval in found:
        grouped.setdefault(interval["key"], []).append(interval)
    for occurrences in grouped.values():
        occurrences.sort(key=lambda item: item["press_request_ns"])
        if any(a["up_sample_ns"] >= b["press_request_ns"] for a, b in zip(occurrences, occurrences[1:])):
            return None, "same_key_occurrence_order_ambiguous"
    terminal = terminals[0]
    t = terminal.get("timestamp_ns")
    if (terminal.get("action_id") != action or type(terminal.get("epoch")) is not int
            or terminal["epoch"] != epoch or terminal.get("source") != "xquerykeymap"
            or terminal.get("keys_down") != [] or type(t) is not int
            or any(item["up_sample_ns"] > t for item in found)):
        return None, "terminal_invalid"
    result = [{key: item[key] for key in
               ("action_id", "epoch", "interval_id", "key", "lower_ns", "upper_ns")}
              for item in found]
    return sorted(result, key=lambda item: (item["key"], item["interval_id"])), None


def main():
    case_bytes, raw_bytes = CASES.read_bytes(), RAW.read_bytes()
    bundle, raw = json.loads(case_bytes.decode("utf-8")), json.loads(raw_bytes.decode("utf-8"))
    by_id = {row.get("case_id"): row for row in raw.get("results", [])}
    checks, reconstructions = {}, {}
    valid_ok = invalid_ok = 0
    for case in bundle.get("cases", []):
        case_id = case["case_id"]
        result = by_id.get(case_id, {}).get("candidate_result")
        expected, error = reconstruct(case.get("events"))
        reconstructions[case_id] = {"expected_intervals": expected, "oracle_error": error}
        if case["expected_class"] == "bounded":
            passed = error is None and result == {"status": "BOUNDED", "intervals": expected, "reasons": []}
            valid_ok += int(passed)
        else:
            reason = INVALID_REASON[case_id]
            passed = (error is not None and isinstance(result, dict)
                      and result.get("status") == "UNKNOWN" and result.get("intervals") == []
                      and reason in result.get("reasons", []))
            invalid_ok += int(passed)
        checks[case_id] = passed
    expected_ids = {case["case_id"] for case in bundle.get("cases", [])}
    checks["all_case_ids_exact"] = set(by_id) == expected_ids and len(raw.get("results", [])) == len(expected_ids)
    checks["allocation_and_source_counts"] = (raw.get("allocation_id") == ALLOCATION
        and raw.get("main_sha") == MAIN and raw.get("candidate_invocations") == 1 and raw.get("retries") == 0)
    checks["cases_hash"] = raw.get("cases_sha256") == hashlib.sha256(case_bytes).hexdigest()
    passed = all(checks.values())
    report = {
        "schema": "map01-occurrence-key-occupancy-audit-v1",
        "status": "PASS_METHOD_SCOPED" if passed else "FAIL_AUDIT",
        "checks": checks,
        "valid_cases_passed": valid_ok,
        "valid_cases_total": 4,
        "invalid_cases_rejected": invalid_ok,
        "invalid_cases_total": 7,
        "independent_reconstruction": reconstructions,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "auditor_imports_candidate": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
