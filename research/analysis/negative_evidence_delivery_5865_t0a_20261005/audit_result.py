#!/usr/bin/env python3
"""Independent specification audit for the Issue #5865 T0a raw event stream."""
import argparse
import copy
import json
from pathlib import Path

POLICIES = ("no_reuse", "naive_sliding_untyped", "origin_bound_typed")
NO = "NO_MATCH_WITHIN_CERTIFIED_SCOPE"
MATCH = "MATCH_FOUND"
UNKNOWN = "UNKNOWN"

# Expected request-level outcomes are derived from the frozen scenario truth,
# not by importing or calling the candidate policy implementation.
EXPECTED = {
    "forward_cycle": {"no_reuse": ([NO, NO], ["fresh_source_evaluation"] * 2, 3),
                      "naive_sliding_untyped": ([NO, NO], ["cache_hit"] * 2, 1),
                      "origin_bound_typed": ([NO, NO], ["cache_hit", "fresh_source_evaluation"], 2)},
    "exact_expiry_boundary": {"no_reuse": ([NO, NO], ["fresh_source_evaluation"] * 2, 3),
                              "naive_sliding_untyped": ([NO, NO], ["cache_hit"] * 2, 1),
                              "origin_bound_typed": ([NO, NO], ["cache_hit", "fresh_source_evaluation"], 2)},
    "predicate_changed_target_present": {"no_reuse": ([MATCH], ["fresh_source_evaluation"], 2),
                                         "naive_sliding_untyped": ([NO], ["cache_hit"], 1),
                                         "origin_bound_typed": ([MATCH], ["fresh_source_evaluation"], 2)},
    "insertion_with_invalidation": {"no_reuse": ([MATCH], ["fresh_source_evaluation"], 2),
                                    "naive_sliding_untyped": ([NO], ["cache_hit"], 1),
                                    "origin_bound_typed": ([MATCH], ["fresh_source_evaluation"], 2)},
    "missing_writer_coverage": {"no_reuse": ([UNKNOWN], ["NO_ELIGIBLE_RECORD_OR_PRODUCER"], 1),
                                "naive_sliding_untyped": ([NO], ["cache_hit"], 1),
                                "origin_bound_typed": ([UNKNOWN], ["NO_ELIGIBLE_RECORD_OR_PRODUCER"], 1)},
    "unknown_clock_offset": {"no_reuse": ([UNKNOWN], ["NO_ELIGIBLE_RECORD_OR_PRODUCER"], 1),
                             "naive_sliding_untyped": ([NO], ["cache_hit"], 1),
                             "origin_bound_typed": ([UNKNOWN], ["NO_ELIGIBLE_RECORD_OR_PRODUCER"], 1)},
    "timeout_target_present_healthy_route": {"no_reuse": ([MATCH], ["route_scoped_failure_does_not_hide_healthy_route"], 0),
                                             "naive_sliding_untyped": ([NO], ["untyped_failure_suppressed_all_routes"], 0),
                                             "origin_bound_typed": ([MATCH], ["route_scoped_failure_does_not_hide_healthy_route"], 0)},
    "failure_cooldown_copy": {"no_reuse": ([MATCH, MATCH], ["route_scoped_failure_does_not_hide_healthy_route"] * 2, 0),
                              "naive_sliding_untyped": ([NO, MATCH], ["untyped_failure_suppressed_all_routes", "route_scoped_failure_does_not_hide_healthy_route"], 0),
                              "origin_bound_typed": ([MATCH, MATCH], ["route_scoped_failure_does_not_hide_healthy_route"] * 2, 0)},
    "evicted_entry": {"no_reuse": ([UNKNOWN], ["NO_ELIGIBLE_RECORD_OR_PRODUCER"], 1),
                      "naive_sliding_untyped": ([UNKNOWN], ["NO_ELIGIBLE_RECORD_OR_PRODUCER"], 1),
                      "origin_bound_typed": ([UNKNOWN], ["NO_ELIGIBLE_RECORD_OR_PRODUCER"], 1)},
    "fresh_source_reevaluation": {"no_reuse": ([NO, NO], ["fresh_source_evaluation"] * 2, 4),
                                  "naive_sliding_untyped": ([NO, NO], ["cache_hit"] * 2, 2),
                                  "origin_bound_typed": ([NO, NO], ["cache_hit", "fresh_source_evaluation"], 3)},
}


def canonical(rows):
    return [json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows]


def core_audit(data, truth, results, raw_rows):
    errors = []
    cases = set(data["cases"])
    if set(results.get("cases", {})) != cases:
        errors.append("case set mismatch")
    serialized = []
    result_lookup = {}
    for case_id, policies in results.get("cases", {}).items():
        if set(policies) != set(POLICIES):
            errors.append(f"{case_id}: policy set mismatch")
        for policy, result in policies.items():
            result_lookup[(case_id, policy)] = result
            serialized.extend(result.get("events", []))
    if sorted(canonical(serialized)) != sorted(canonical(raw_rows)):
        errors.append("raw JSONL differs from the saved per-case event projection")
    if len(canonical(raw_rows)) != len(set(canonical(raw_rows))):
        # Identical events can legitimately exist at distinct sequence numbers;
        # only reject duplicate complete records when sequence identity repeats.
        keys = [(r.get("case"), r.get("policy"), r.get("sequence")) for r in raw_rows]
        if len(keys) != len(set(keys)):
            errors.append("duplicate case/policy/event sequence")

    false_negatives = {policy: [] for policy in POLICIES}
    unsupported_negative_claims = {policy: [] for policy in POLICIES}
    for case_id, policy_table in EXPECTED.items():
        for policy, (statuses, reasons, expected_calls) in policy_table.items():
            item = result_lookup.get((case_id, policy))
            if item is None:
                errors.append(f"missing result {case_id}/{policy}")
                continue
            lookups = [row for row in item.get("events", []) if row.get("event") in ("lookup", "route_probe")]
            if [row.get("status") for row in lookups] != statuses:
                errors.append(f"{case_id}/{policy}: request outcomes differ from frozen truth")
            if [row.get("reason") for row in lookups] != reasons:
                errors.append(f"{case_id}/{policy}: source/reuse reasons differ")
            summary = item.get("summary", {})
            if summary.get("producer_attempts") != expected_calls:
                errors.append(f"{case_id}/{policy}: producer attempt count mismatch")
            if summary.get("authority_granted") is not False or any(row.get("authority_granted") is not False for row in item.get("events", [])):
                errors.append(f"{case_id}/{policy}: authority was emitted")
            if policy == "no_reuse" and (summary.get("cache_reuses") != 0 or any(row.get("retained_entries") != 0 for row in item.get("events", []))):
                errors.append(f"{case_id}: no-reuse baseline retained or reused a record")
            truth_row = truth["truth"][case_id]
            target_present = truth_row.get("target_present", truth_row.get("target_present_at_5", False))
            if case_id == "insertion_with_invalidation":
                target_present = True
            for row in lookups:
                if row.get("status") == "NO_MATCH_WITHIN_CERTIFIED_SCOPE" and target_present:
                    false_negatives[policy].append(case_id)
                if row.get("status") == "NO_MATCH_WITHIN_CERTIFIED_SCOPE" and case_id in ("missing_writer_coverage", "unknown_clock_offset"):
                    unsupported_negative_claims[policy].append(case_id)
            if summary.get("unknown_results") != sum(row.get("status") in (UNKNOWN, "UNKNOWN_DEPENDENCY_UNAVAILABLE") for row in item.get("events", [])):
                errors.append(f"{case_id}/{policy}: unknown count mismatch")
            actual_producers = sum(row.get("event") == "source_evaluation" or (row.get("event") == "lookup" and row.get("reason") == "fresh_source_evaluation") for row in item.get("events", []))
            if actual_producers != expected_calls:
                errors.append(f"{case_id}/{policy}: raw source evaluation receipts mismatch")
            case_spec = data["cases"][case_id]
            expected_request_ids = {action["request_id"] for action in case_spec["actions"] if action.get("request_id")}
            if case_spec.get("seed"):
                expected_request_ids.add(data["seed"]["request_id"])
            observed_request_ids = {row["request_id"] for row in item.get("events", []) if row.get("request_id")}
            if observed_request_ids != expected_request_ids or summary.get("request_ids") != sorted(expected_request_ids) or summary.get("offered_requests") != len(expected_request_ids):
                errors.append(f"{case_id}/{policy}: offered-request identity ledger mismatch")
            actual_route_attempts = sum(row.get("event") == "route_failure" for row in item.get("events", []))
            actual_route_attempts += sum(len(row.get("attempted_routes", [])) for row in item.get("events", []) if row.get("event") == "route_probe")
            if summary.get("route_attempts") != actual_route_attempts:
                errors.append(f"{case_id}/{policy}: route attempt ledger mismatch")
            actual_expired_reuses = sum(row.get("expired_origin_reuse") is True for row in item.get("events", []))
            if summary.get("expired_origin_reuses") != actual_expired_reuses or summary.get("false_freshness_rows") != actual_expired_reuses:
                errors.append(f"{case_id}/{policy}: expired-origin summary mismatch")
            for row in item.get("events", []):
                if policy == "origin_bound_typed" and row.get("reason") == "cache_hit" and row.get("origin_expiry") is not None and row.get("time", 0) >= row["origin_expiry"]:
                    errors.append(f"{case_id}: typed evidence reused at or after original expiry")
                if row.get("cache_entries") != len(row.get("cache_snapshot", {})):
                    errors.append(f"{case_id}/{policy}: cache entry count differs from snapshot")
                if row.get("failure_entries") != len(row.get("failure_snapshot", {})):
                    errors.append(f"{case_id}/{policy}: failure entry count differs from snapshot")
                expected_bytes = len(json.dumps({"semantic": row.get("cache_snapshot", {}), "route_failures": row.get("failure_snapshot", {})}, sort_keys=True, separators=(",", ":")).encode("utf-8"))
                if row.get("retained_entries") != row.get("cache_entries", 0) + row.get("failure_entries", 0) or row.get("retained_bytes") != expected_bytes:
                    errors.append(f"{case_id}/{policy}: retained entry/byte ledger mismatch")
                if row.get("event") == "route_probe" and policy == "origin_bound_typed" and case_id == "timeout_target_present_healthy_route":
                    if "B" not in row.get("attempted_routes", []):
                        errors.append("typed route failure hid independent healthy route B")
                if row.get("event") == "failure_forward" and policy == "origin_bound_typed" and case_id == "failure_cooldown_copy":
                    failure = row.get("failure_snapshot", {}).get("B:A", {})
                    if row.get("retry_after") != 5 or failure.get("retry_after") != 5 or failure.get("retained_until") != 15:
                        errors.append("typed forwarding renewed original failure cooldown")
                if row.get("event") == "forward" and policy == "origin_bound_typed":
                    forwarded = row.get("cache_snapshot", {}).get(row.get("to", ""), {})
                    if forwarded and forwarded.get("expires_at") != forwarded.get("origin_expiry"):
                        errors.append(f"{case_id}: typed evidence forwarding extended its deadline")
                if row.get("event") == "route_probe" and policy == "origin_bound_typed" and case_id == "failure_cooldown_copy":
                    if "A" not in row.get("attempted_routes", []):
                        errors.append("typed failure cooldown remained after retry eligibility")
                    if row.get("time") == 16 and row.get("failure_snapshot"):
                        errors.append("typed failure record outlived its bounded retention")
                if row.get("event") == "lookup" and policy == "origin_bound_typed" and row.get("reason") == "cache_hit":
                    record = next(iter(row.get("cache_snapshot", {}).values()), {})
                    request = row.get("request", {})
                    if any(record.get("query", {}).get(key) != request.get(key) for key in ("target_id", "surface_id", "scope", "predicate_version", "epoch")):
                        errors.append(f"{case_id}: typed cache hit crossed a query-key boundary")

    if false_negatives["origin_bound_typed"]:
        errors.append("typed policy has false-negative outcomes")
    if unsupported_negative_claims["origin_bound_typed"]:
        errors.append("typed policy certified incomplete/clock-unknown evidence")
    if false_negatives["no_reuse"]:
        errors.append("no-reuse baseline has false-negative outcomes")
    if not false_negatives["naive_sliding_untyped"]:
        errors.append("planted unsafe control did not expose a target-present false negative")
    if not unsupported_negative_claims["naive_sliding_untyped"]:
        errors.append("planted unsafe control did not expose incomplete-provenance claims")
    cycle_typed = result_lookup.get(("forward_cycle", "origin_bound_typed"), {}).get("summary", {})
    cycle_plain = result_lookup.get(("forward_cycle", "no_reuse"), {}).get("summary", {})
    if not (cycle_typed.get("cache_reuses", 0) > 0 and cycle_typed.get("producer_attempts", 99) < cycle_plain.get("producer_attempts", 0)):
        errors.append("valid repeated-query reuse did not reduce producer attempts")

    return errors, false_negatives, unsupported_negative_claims


def audit(data, truth, results, raw_rows):
    errors, false_negatives, unsupported = core_audit(data, truth, results, raw_rows)
    controls = {}

    def mutation_rejected(changed_results, changed_raw):
        return bool(core_audit(data, truth, changed_results, changed_raw)[0])

    changed_results = copy.deepcopy(results)
    changed_raw = copy.deepcopy(raw_rows)
    for collection in (changed_results["cases"]["forward_cycle"]["origin_bound_typed"]["events"], changed_raw):
        row = next(row for row in collection if row.get("case") == "forward_cycle" and row.get("policy") == "origin_bound_typed" and row.get("event") == "lookup" and row.get("time") == 16)
        row.update({"status": NO, "reason": "cache_hit", "origin_evaluated_at": 0, "origin_expiry": 10, "expired_origin_reuse": True})
    controls["expired_forward_reuse_rejected"] = mutation_rejected(changed_results, changed_raw)

    changed_results = copy.deepcopy(results)
    changed_raw = copy.deepcopy(raw_rows)
    for collection in (changed_results["cases"]["predicate_changed_target_present"]["origin_bound_typed"]["events"], changed_raw):
        row = next(row for row in collection if row.get("case") == "predicate_changed_target_present" and row.get("policy") == "origin_bound_typed" and row.get("event") == "lookup")
        row.update({"status": NO, "reason": "cache_hit", "request": {"target_id": "save-button", "surface_id": "window-4", "scope": "panel-main", "predicate_version": 2, "epoch": 7}})
    controls["predicate_scope_mismatch_rejected"] = mutation_rejected(changed_results, changed_raw)

    changed_results = copy.deepcopy(results)
    changed_raw = copy.deepcopy(raw_rows)
    for collection in (changed_results["cases"]["timeout_target_present_healthy_route"]["origin_bound_typed"]["events"], changed_raw):
        row = next(row for row in collection if row.get("case") == "timeout_target_present_healthy_route" and row.get("policy") == "origin_bound_typed" and row.get("event") == "route_probe")
        row.update({"status": NO, "attempted_routes": [], "healthy_route_suppressed": "B"})
    controls["healthy_route_suppression_rejected"] = mutation_rejected(changed_results, changed_raw)

    changed_results = copy.deepcopy(results)
    changed_raw = copy.deepcopy(raw_rows)
    for collection in (changed_results["cases"]["failure_cooldown_copy"]["origin_bound_typed"]["events"], changed_raw):
        row = next(row for row in collection if row.get("case") == "failure_cooldown_copy" and row.get("policy") == "origin_bound_typed" and row.get("event") == "failure_forward")
        row["retry_after"] = 9
        row["failure_snapshot"]["A"]["retry_after"] = 9
    controls["failure_forward_does_not_renew_cooldown"] = mutation_rejected(changed_results, changed_raw)

    changed_results = copy.deepcopy(results)
    changed_raw = copy.deepcopy(raw_rows)
    duplicate = copy.deepcopy(next(row for row in changed_raw if row.get("case") == "forward_cycle" and row.get("policy") == "origin_bound_typed"))
    changed_raw.append(duplicate)
    changed_results["cases"]["forward_cycle"]["origin_bound_typed"]["events"].append(copy.deepcopy(duplicate))
    controls["duplicate_raw_event_rejected"] = mutation_rejected(changed_results, changed_raw)

    changed_results = copy.deepcopy(results)
    changed_raw = copy.deepcopy(raw_rows)
    target = next(row for row in changed_results["cases"]["fresh_source_reevaluation"]["origin_bound_typed"]["events"] if row.get("event") == "source_evaluation" and row.get("time") == 5)
    changed_results["cases"]["fresh_source_reevaluation"]["origin_bound_typed"]["events"].remove(target)
    changed_raw.remove(next(row for row in changed_raw if row.get("case") == "fresh_source_reevaluation" and row.get("policy") == "origin_bound_typed" and row.get("event") == "source_evaluation" and row.get("time") == 5))
    controls["omitted_producer_receipt_rejected"] = mutation_rejected(changed_results, changed_raw)

    return {"errors": errors, "false_negatives": false_negatives, "unsupported_negative_claims": unsupported, "mutation_controls": controls}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    truth = json.loads(args.truth.read_text(encoding="utf-8"))
    results = json.loads(args.results.read_text(encoding="utf-8"))
    raw_rows = [json.loads(line) for line in args.events.read_text(encoding="utf-8").splitlines() if line]
    checked = audit(data, truth, results, raw_rows)
    controls_pass = all(checked["mutation_controls"].values())
    report = {"status": "PASS_AUDIT" if not checked["errors"] and controls_pass else "FAIL_AUDIT", "raw_event_rows": len(raw_rows), "case_policy_rows": len(results.get("cases", {})) * len(POLICIES), **checked}
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS_AUDIT" else 1)


if __name__ == "__main__":
    main()
