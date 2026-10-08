"""Independent raw-derived check for the retained per-key ledger A01 output."""

import argparse
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def rows_for_key_interval(raw):
    rows = raw.get("events")
    if not isinstance(rows, list):
        raise ValueError("raw events must be a list")
    intervals = [
        row for row in rows
        if isinstance(row, dict) and row.get("kind") == "key_interval"
    ]
    if not intervals:
        raise ValueError("raw fixture has no key intervals")
    return intervals


def derive_interval(row):
    names = (
        "press_request_ns", "press_sync_ns", "down_sample_ns",
        "release_request_ns", "release_sync_ns", "up_sample_ns",
    )
    values = [row.get(name) for name in names]
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("raw interval has an invalid timestamp")
    p_req, p_sync, down, r_req, r_sync, up = values
    if not (p_req <= p_sync <= down < r_req <= r_sync <= up):
        raise ValueError("raw interval timestamps are not ordered")
    if row.get("source") != "input-owner-v11":
        raise ValueError("raw interval source is not trusted")
    action_id, epoch, key = row.get("action_id"), row.get("epoch"), row.get("key")
    if not isinstance(action_id, str) or not action_id or type(epoch) is not int:
        raise ValueError("raw interval identity is invalid")
    if not isinstance(key, str) or not key:
        raise ValueError("raw interval key is invalid")
    return {
        "action_id": action_id,
        "epoch": epoch,
        "key": key,
        "lower_ns": r_req - p_sync,
        "upper_ns": r_sync - p_req,
    }


def expected_result(rows, expected_keys, empty):
    try:
        actual = [derive_interval(row) for row in rows]
    except (TypeError, ValueError):
        return {"status": "UNKNOWN", "intervals": []}
    keys = [row["key"] for row in actual]
    if len(set(keys)) != len(keys) or set(keys) != set(expected_keys):
        return {"status": "UNKNOWN", "intervals": []}
    if (not isinstance(empty, dict)
            or empty.get("kind") != "verified_empty"
            or empty.get("source") != "xquerykeymap"
            or empty.get("keys_down") != []
            or type(empty.get("timestamp_ns")) is not int
            or empty["timestamp_ns"] < 0
            or any(row["action_id"] != empty.get("action_id")
                   or row["epoch"] != empty.get("epoch")
                   or row["up_sample_ns"] > empty["timestamp_ns"]
                   for row in rows)):
        return {"status": "UNKNOWN", "intervals": []}
    return {
        "status": "BOUNDED",
        "intervals": sorted(actual, key=lambda row: row["key"]),
    }


def audit(raw_path, output_path):
    raw_bytes = Path(raw_path).read_bytes()
    output_bytes = Path(output_path).read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"))
    output = json.loads(output_bytes.decode("utf-8"))
    intervals = rows_for_key_interval(raw)
    event_rows = raw["events"]
    empty_rows = [
        row for row in event_rows
        if isinstance(row, dict) and row.get("kind") == "verified_empty"
    ]
    unknown_rows = [
        row for row in event_rows
        if not isinstance(row, dict)
        or row.get("kind") not in ("key_interval", "verified_empty")
    ]
    empty = empty_rows[0] if len(empty_rows) == 1 else None
    original_keys = sorted(row.get("key") for row in intervals)
    omitted_rows = [row for row in intervals if row.get("key") != "SPACE"]
    omitted_keys = sorted(row.get("key") for row in omitted_rows)
    cases = output.get("cases", {})

    expected = {
        "complete_correct_inventory": expected_result(intervals, original_keys, empty),
        "omitted_correct_inventory": expected_result(omitted_rows, original_keys, empty),
        "omitted_underdeclared_inventory": expected_result(omitted_rows, ["W"], empty),
        "complete_underdeclared_inventory": expected_result(intervals, ["W"], empty),
    }
    exact_cases = {
        name: {
            "status": cases.get(name, {}).get("status"),
            "intervals": cases.get(name, {}).get("intervals"),
        }
        for name in expected
    }
    checks = {
        "raw_fixture_contains_two_distinct_keys": original_keys == ["SPACE", "W"],
        "mutated_observation_contains_only_w": omitted_keys == ["W"],
        "raw_stream_contains_one_verified_empty_and_no_unknown_rows": (
            len(empty_rows) == 1 and not unknown_rows
        ),
        "candidate_case_names_match_frozen_scenarios": set(cases) == set(expected),
        "all_candidate_interval_rows_match_raw_derived_bounds": (
            canonical(exact_cases) == canonical(expected)
        ),
        "complete_default_control_is_bounded": expected["complete_correct_inventory"]["status"] == "BOUNDED",
        "omission_with_correct_inventory_is_unknown": expected["omitted_correct_inventory"]["status"] == "UNKNOWN",
        "omission_with_underdeclared_inventory_is_bounded": expected["omitted_underdeclared_inventory"]["status"] == "BOUNDED",
        "complete_with_underdeclared_inventory_is_unknown": expected["complete_underdeclared_inventory"]["status"] == "UNKNOWN",
    }
    report = {
        "allocation": "MAP01-PERKEY-LEDGER-A01-AUDIT-RECHECK-20261005",
        "status": "PASS_RAW_DERIVED_AUDIT" if all(checks.values()) else "FAIL_AUDIT",
        "checks": checks,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_output_sha256": hashlib.sha256(output_bytes).hexdigest(),
        "expected_cases_raw_derived": expected,
        "imports_candidate_or_ledger": False,
        "scope": "independent raw timestamp arithmetic and exact candidate case reconstruction; synthetic fixture only",
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--candidate-output", type=Path, required=True)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()
    report = audit(args.raw, args.candidate_output)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report_out:
        args.report_out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["status"] == "PASS_RAW_DERIVED_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
