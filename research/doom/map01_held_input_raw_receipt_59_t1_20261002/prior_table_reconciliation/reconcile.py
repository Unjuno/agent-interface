"""Audit-only reconciliation of retained #6198 outputs to the #6175 prior table."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


TABLE_SCHEMA = "map01-held-input-audited-table-transcription-v1"
TABLE_ALLOCATION = "MAP01-HELD-INPUT-FULLTRACE-59-T0-20261002-01"
TABLE_GIT_BLOB = "b84cddc6d884e10e8a5e9baf202210923c558c57"
TABLE_SHA256 = "2aab450e687cce4b912a83d548b9ab76165ed1826110e7506468efe2891ef7df"
EXPECTED_CANDIDATE_SHA256 = {
    "v38": "55771151887660b4a264d9e788410e12e2e6e45ca4f4c9d96db1a5f93e85e5f1",
    "v39": "49a47182f6d6f3fdb944224882be5716a0452b2cc88beee51b482ef915be5fc0",
}
EXPECTED_ROW_COUNTS = {"v38": 11, "v39": 27}
AGGREGATE_FIELDS = {
    "completed_hold_count": "completed_holds",
    "interrupted_verified_count": "verified_interrupted_holds",
    "requested_total_ms": "requested_total_ms",
    "owner_commanded_hold_total_lower_ms": "owner_commanded_hold_total_lower_ms",
    "owner_commanded_hold_total_upper_ms": "owner_commanded_hold_total_upper_ms",
    "overshoot_total_lower_ms": "overshoot_total_lower_ms",
    "overshoot_total_upper_ms": "overshoot_total_upper_ms",
    "median_overshoot_lower_ms": "median_overshoot_lower_ms",
    "median_overshoot_upper_ms": "median_overshoot_upper_ms",
}
TOLERANCE = 1e-9


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _rows_by_identity(rows: list[dict], id_field: str, errors: list[str], label: str) -> dict[tuple, dict]:
    indexed = {}
    for row in rows:
        key = (row.get(id_field), row.get("step"))
        if key in indexed:
            errors.append(f"{label}:duplicate_row:{key!r}")
        indexed[key] = row
    return indexed


def _finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def reconcile(v38: dict, v39: dict, prior: dict, expected_counts: dict[str, int] | None = None) -> dict:
    errors: list[str] = []
    row_counts = EXPECTED_ROW_COUNTS if expected_counts is None else expected_counts
    expected_total = sum(row_counts.values())
    if prior.get("schema") != TABLE_SCHEMA:
        errors.append("prior_table_schema_mismatch")
    if prior.get("allocation_id") != TABLE_ALLOCATION:
        errors.append("prior_table_allocation_mismatch")
    prior_rows = prior.get("completed_holds", [])
    if len(prior_rows) != expected_total:
        errors.append("prior_table_row_count_mismatch")
    prior_index = {}
    for row in prior_rows:
        key = (row.get("trace"), row.get("decision_id"), row.get("step"))
        if key in prior_index:
            errors.append(f"prior_table:duplicate_row:{key!r}")
        prior_index[key] = row

    candidates = {"v38": v38, "v39": v39}
    candidate_rows_checked = 0
    aggregate_fields_checked = 0
    expected_prior_keys = set()
    for trace, candidate in candidates.items():
        rows = candidate.get("completed_holds", [])
        if len(rows) != row_counts[trace]:
            errors.append(f"{trace}:candidate_row_count_mismatch")
        candidate_index = _rows_by_identity(rows, "id", errors, trace)
        expected_prior_keys.update((trace, key[0], key[1]) for key in candidate_index)
        trace_prior = {
            (row.get("decision_id"), row.get("step")): row
            for row in prior_rows
            if row.get("trace") == trace
        }
        if set(candidate_index) != set(trace_prior):
            errors.append(f"{trace}:row_identity_set_mismatch")
        for key, candidate_row in candidate_index.items():
            table_row = trace_prior.get(key)
            if table_row is None:
                continue
            candidate_rows_checked += 1
            for field, candidate_field in (
                ("lower_ms", "owner_commanded_hold_lower_ms"),
                ("upper_ms", "owner_commanded_hold_upper_ms"),
                ("interval_width_ms", "bound_width_ms"),
            ):
                actual_value = candidate_row.get(candidate_field)
                table_value = table_row.get(field)
                if not _finite_number(actual_value) or not _finite_number(table_value) or round(float(actual_value), 3) != table_value:
                    errors.append(f"{trace}:{key!r}:{field}:display_precision_mismatch")
            if candidate_row.get("requested_ms") != table_row.get("requested_ms"):
                errors.append(f"{trace}:{key!r}:requested_ms_mismatch")

        prior_summaries = prior.get("reported_exact_precision_summaries", {})
        expected_summary = prior_summaries.get(trace)
        actual_summary = candidate.get("summary", {})
        if not isinstance(expected_summary, dict):
            errors.append(f"{trace}:prior_summary_missing")
            continue
        for candidate_field, table_field in AGGREGATE_FIELDS.items():
            actual = actual_summary.get(candidate_field)
            expected = expected_summary.get(table_field)
            aggregate_fields_checked += 1
            if not _finite_number(actual) or not _finite_number(expected):
                errors.append(f"{trace}:{candidate_field}:aggregate_missing_or_non_numeric")
            elif not math.isfinite(float(actual)) or not math.isfinite(float(expected)) or abs(float(actual) - float(expected)) > TOLERANCE:
                errors.append(f"{trace}:{candidate_field}:aggregate_tolerance_exceeded")
        requested = actual_summary.get("requested_total_ms")
        if _finite_number(requested) and requested:
            for fraction_field, total_field in (
                ("overshoot_fraction_lower", "overshoot_total_lower_ms"),
                ("overshoot_fraction_upper", "overshoot_total_upper_ms"),
            ):
                fraction = actual_summary.get(fraction_field)
                total = expected_summary.get(total_field)
                if not _finite_number(fraction) or not _finite_number(total) or abs(float(fraction) - float(total) / float(requested)) > TOLERANCE:
                    errors.append(f"{trace}:{fraction_field}:derived_fraction_mismatch")

    if expected_prior_keys != set(prior_index):
        errors.append("candidate_and_prior_complete_identity_sets_differ")

    interruptions_38 = v38.get("interrupted_holds", [])
    interruptions_39 = v39.get("interrupted_holds", [])
    table_interruption = prior.get("interrupted_hold")
    interruption_match = False
    if len(interruptions_38) != 0 or len(interruptions_39) != 1 or not isinstance(table_interruption, dict):
        errors.append("interrupted_hold_count_mismatch")
    else:
        actual = interruptions_39[0]
        interruption_match = (
            actual.get("id") == table_interruption.get("decision_id")
            and actual.get("step") == table_interruption.get("step")
            and actual.get("requested_ms") == table_interruption.get("requested_ms")
            and actual.get("keys") == table_interruption.get("keys")
            and actual.get("full_keyset_ack_ns") == table_interruption.get("full_keyset_ack_ns")
            and actual.get("empty_verified_ns") == table_interruption.get("empty_verified_ns")
            and _finite_number(actual.get("ack_to_empty_verified_ms"))
            and _finite_number(table_interruption.get("ack_to_empty_verified_ms"))
            and abs(float(actual["ack_to_empty_verified_ms"]) - float(table_interruption["ack_to_empty_verified_ms"])) <= TOLERANCE
            and _finite_number(actual.get("empty_verified_ns"))
            and _finite_number(actual.get("full_keyset_ack_ns"))
            and abs((actual["empty_verified_ns"] - actual["full_keyset_ack_ns"]) / 1_000_000 - actual["ack_to_empty_verified_ms"]) <= TOLERANCE
            and table_interruption.get("trace") == "v39"
            and table_interruption.get("classification") == "interrupted_empty_verified"
            and table_interruption.get("excluded_from_completed_hold_totals") is True
        )
        if not interruption_match:
            errors.append("interrupted_hold_receipt_mismatch")

    return {
        "schema": "map01-held-input-prior-table-reconciliation-v1",
        "disposition": "PASS_PRIOR_TABLE_RECONCILED" if not errors else "FAIL_PRIOR_TABLE_RECONCILIATION",
        "expected_completed_rows": expected_total,
        "completed_rows_matched": candidate_rows_checked,
        "aggregate_fields_checked": aggregate_fields_checked,
        "interrupted_receipt_match": interruption_match,
        "rounding_rule": "candidate row fields rounded to 0.001 ms and compared exactly to the published prior table",
        "aggregate_tolerance_ms": TOLERANCE,
        "errors": errors,
    }


def _read_json(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    return json.loads(data.decode("utf-8")), data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parents[1]
    here = Path(__file__).resolve().parent
    inputs = {
        "v38": package / "candidate_v38.json",
        "v39": package / "candidate_v39.json",
        "prior_table": here / "AUDITED_INTERVALS.json",
    }
    raw = {}
    input_hashes = {}
    errors = []
    for name, path in inputs.items():
        try:
            raw[name], data = _read_json(path)
            input_hashes[name] = hashlib.sha256(data).hexdigest()
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{name}:input_read_error:{type(exc).__name__}")
    if not errors:
        for name, expected in EXPECTED_CANDIDATE_SHA256.items():
            if input_hashes.get(name) != expected:
                errors.append(f"{name}:sha256_mismatch")
        table_bytes = inputs["prior_table"].read_bytes()
        if input_hashes.get("prior_table") != TABLE_SHA256 or _git_blob_sha1(table_bytes) != TABLE_GIT_BLOB:
            errors.append("prior_table:immutable_identity_mismatch")
    if errors:
        result = {
            "schema": "map01-held-input-prior-table-reconciliation-v1",
            "disposition": "STOP_INPUT_IDENTITY_MISMATCH",
            "input_sha256": input_hashes,
            "errors": errors,
        }
    else:
        result = reconcile(raw["v38"], raw["v39"], raw["prior_table"])
        result["input_sha256"] = input_hashes
        result["prior_table_git_blob_sha1"] = TABLE_GIT_BLOB
    output = Path(args.output)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "disposition": result["disposition"], "errors": result.get("errors", [])}))
    return 0 if result["disposition"] == "PASS_PRIOR_TABLE_RECONCILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
