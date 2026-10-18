#!/usr/bin/env python3
"""Finite cache-delivery protocol model for Issue #5865; Python stdlib only."""
import argparse
import json
from pathlib import Path

POLICIES = ("no_reuse", "naive_sliding_untyped", "origin_bound_typed")
KEY_FIELDS = ("target_id", "surface_id", "scope", "predicate_version", "epoch")


def record_from(seed, query, ttl, policy, *, at=None, result=None, evaluation_id=None):
    evaluated = seed["time"] if at is None else at
    status = seed["result"] if result is None else result
    return {
        "record_type": "SCOPED_NEGATIVE_EVIDENCE" if policy == "origin_bound_typed" else "UNTYPED_NEGATIVE",
        "query": dict(query),
        "result": status,
        "evaluation_id": seed["evaluation_id"] if evaluation_id is None else evaluation_id,
        "origin_evaluated_at": evaluated,
        "origin_expiry": evaluated + ttl,
        "expires_at": evaluated + ttl,
        "writer_coverage": seed["writer_coverage"],
        "coherent": seed["coherent"],
        "clock_mapping": seed["clock_mapping"],
        "source_id": seed["source_id"],
    }


def typed_valid(record, query, now):
    return (
        record.get("record_type") == "SCOPED_NEGATIVE_EVIDENCE"
        and record.get("result") == "NO_MATCH_WITHIN_CERTIFIED_SCOPE"
        and record.get("writer_coverage") is True
        and record.get("coherent") is True
        and record.get("clock_mapping") == "known"
        and all(record.get("query", {}).get(k) == query.get(k) for k in KEY_FIELDS)
        and now < record.get("origin_expiry", -1)
    )


def storage_bytes(cache, failures):
    stored = {"semantic": cache, "route_failures": failures}
    return len(json.dumps(stored, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def run_case(case_id, case, base_query, ttl, policy):
    cache = {}
    failures = {}
    events = []
    producer_attempts = 0
    route_attempts = 0
    route_failures_seen = 0
    cache_reuses = 0
    expired_origin_reuses = 0
    query = dict(base_query)
    inserted_at = None

    def emit(action, *, event_type, time, status=None, reason=None, record=None, route=None, attempt=False, extra=None):
        nonlocal producer_attempts, route_attempts, route_failures_seen, cache_reuses, expired_origin_reuses
        if attempt:
            producer_attempts += 1
        row = {
            "case": case_id, "policy": policy, "sequence": len(events), "event": event_type,
            "time": time, "status": status, "reason": reason,
            "producer_attempts_total": producer_attempts,
            "route_attempts_total": route_attempts,
            "route_failures_total": route_failures_seen,
            "cache_reuses_total": cache_reuses,
            "expired_origin_reuses_total": expired_origin_reuses,
            "cache_entries": len(cache), "failure_entries": len(failures),
            "retained_entries": len(cache) + len(failures), "retained_bytes": storage_bytes(cache, failures),
            "cache_snapshot": cache, "failure_snapshot": failures,
            "authority_granted": False,
        }
        for field in ("request_id", "from", "to", "at", "route"):
            if action.get(field) is not None:
                row[field] = action[field]
        if record:
            row.update({"evaluation_id": record.get("evaluation_id"), "origin_evaluated_at": record.get("origin_evaluated_at"),
                        "origin_expiry": record.get("origin_expiry"), "record_type": record.get("record_type")})
        if route is not None:
            row["route"] = route
        if extra:
            row.update(extra)
        events.append(row)

    seed = dict(case.get("seed_overrides", {}))
    seed = {**json.loads(json.dumps(case.get("seed_record", {}))), **seed}
    if case.get("seed"):
        seed = {**case["seed_record"], **case.get("seed_overrides", {})}
        producer_attempts += 1
        rec = record_from(seed, query, ttl, policy)
        if policy == "naive_sliding_untyped":
            cache["A"] = rec
        elif policy == "origin_bound_typed" and rec["result"] == "NO_MATCH_WITHIN_CERTIFIED_SCOPE" and rec["writer_coverage"] and rec["coherent"] and rec["clock_mapping"] == "known":
            cache["A"] = rec
        emit({}, event_type="source_evaluation", time=seed["time"], status=seed["result"], record=rec,
             reason="seed_evaluation", extra={"source_id": seed["source_id"], "request_id": seed.get("request_id")})

    for action in case["actions"]:
        kind, now = action["type"], action["time"]
        if kind == "copy":
            rec = cache.get(action["from"])
            if policy == "no_reuse" or rec is None:
                emit(action, event_type="forward", time=now, reason="no_cache_record")
                continue
            moved = dict(rec)
            if policy == "naive_sliding_untyped":
                moved["expires_at"] = now + ttl
            cache[action["to"]] = moved
            emit(action, event_type="forward", time=now, status="FORWARDED", record=moved,
                 reason="receipt_copy_does_not_re_evaluate_source")
        elif kind == "invalidate":
            removed = 0
            if policy == "origin_bound_typed":
                for key in list(cache):
                    if cache[key].get("query", {}).get("target_id") == action["target_id"]:
                        cache.pop(key)
                        removed += 1
            emit(action, event_type="invalidation", time=now, status="INVALIDATED" if removed else "NO_TYPED_ENTRY",
                 reason="target_membership_change", extra={"records_removed": removed})
        elif kind == "insert_target":
            inserted_at = now
            emit(action, event_type="target_inserted", time=now, status="ENVIRONMENT_CHANGED", reason="not_a_source_evaluation")
        elif kind == "evict":
            existed = cache.pop(action["at"], None) is not None
            emit(action, event_type="eviction", time=now, status="EVICTED" if existed else "ALREADY_ABSENT", reason="capacity_or_policy_eviction")
        elif kind == "copy_failure":
            failure = failures.get(f"A:{action['route']}")
            if policy == "naive_sliding_untyped":
                failure = cache.get("A")
                if failure is not None:
                    forwarded = dict(failure)
                    forwarded["expires_at"] = now + ttl
                    cache[action["to"]] = forwarded
            elif policy == "origin_bound_typed" and failure is not None:
                failures[f"{action['to']}:{action['route']}"] = dict(failure)
            emit(action, event_type="failure_forward", time=now, status="FORWARDED" if failure else "NO_RECORD",
                 reason="copy_is_not_a_new_attributable_probe", extra={"route": action["route"], "retry_after": failure.get("retry_after") if failure else None})
        elif kind == "fresh_evaluation":
            producer_attempts += 1
            refreshed_seed = {**seed, "time": now, "evaluation_id": f"eval-{now}", "result": action["result"]}
            rec = record_from(refreshed_seed, query, ttl, policy, at=now, result=action["result"], evaluation_id=refreshed_seed["evaluation_id"])
            if policy == "naive_sliding_untyped":
                cache[action["at"]] = rec
            elif policy == "origin_bound_typed" and rec["writer_coverage"] and rec["coherent"] and rec["clock_mapping"] == "known":
                cache[action["at"]] = rec
            emit(action, event_type="source_evaluation", time=now, status=action["result"], record=rec, reason="new_producer_evaluation")
        elif kind == "lookup":
            request = dict(query)
            request.update(action["query"])
            rec = cache.get(action["at"])
            valid = False
            if policy == "naive_sliding_untyped" and rec is not None:
                valid = request.get("target_id") == rec.get("query", {}).get("target_id") and now <= rec.get("expires_at", -1)
            elif policy == "origin_bound_typed" and rec is not None:
                valid = typed_valid(rec, request, now)
            if policy != "no_reuse" and valid:
                cache_reuses += 1
                expired = now >= rec["origin_expiry"]
                if expired:
                    expired_origin_reuses += 1
                emit(action, event_type="lookup", time=now, status=rec["result"], record=rec,
                     reason="cache_hit", extra={"request": request, "source_age": now - rec["origin_evaluated_at"], "expired_origin_reuse": expired})
                continue
            if action["provider_available"]:
                producer_attempts += 1
                answer = action["provider_result"]
                fresh = {**seed, "time": now, "evaluation_id": f"eval-{now}-{len(events)}", "result": answer}
                new_record = record_from(fresh, request, ttl, policy, at=now, result=answer, evaluation_id=fresh["evaluation_id"])
                if answer == "NO_MATCH_WITHIN_CERTIFIED_SCOPE" and policy == "naive_sliding_untyped":
                    cache[action["at"]] = new_record
                elif answer == "NO_MATCH_WITHIN_CERTIFIED_SCOPE" and policy == "origin_bound_typed" and new_record["writer_coverage"] and new_record["coherent"] and new_record["clock_mapping"] == "known":
                    cache[action["at"]] = new_record
                elif answer == "MATCH_FOUND":
                    cache.pop(action["at"], None)
                emit(action, event_type="lookup", time=now, status=answer, record=new_record,
                     reason="fresh_source_evaluation", attempt=False, extra={"request": request, "source_age": 0, "expired_origin_reuse": False,
                     "recovery_delay": now - inserted_at if answer == "MATCH_FOUND" and inserted_at is not None else None})
            else:
                reason = "CLOCK_MAPPING_UNKNOWN" if rec and rec.get("clock_mapping") != "known" else "NO_ELIGIBLE_RECORD_OR_PRODUCER"
                emit(action, event_type="lookup", time=now, status="UNKNOWN", record=rec, reason=reason,
                     extra={"request": request, "source_age": None, "expired_origin_reuse": False})
        elif kind == "route_failure":
            route_attempts += 1
            route_failures_seen += 1
            failure = {"record_type": "OBSERVATION_ROUTE_FAILURE", "route": action["route"], "failure_class": action["failure_class"],
                       "retry_after": action["retry_after"], "retained_until": action["retry_after"] + ttl,
                       "query": {**query, **action["query"]}}
            if policy == "origin_bound_typed":
                failures[f"A:{action['route']}"] = failure
            elif policy == "naive_sliding_untyped":
                cache["A"] = {"record_type": "UNTYPED_NEGATIVE", "query": dict(query), "result": "NO_MATCH_WITHIN_CERTIFIED_SCOPE",
                               "evaluation_id": "failure-miscast", "origin_evaluated_at": now, "origin_expiry": now + ttl, "expires_at": now + ttl}
            emit(action, event_type="route_failure", time=now, status="DEPENDENCY_UNAVAILABLE", reason=action["failure_class"], route=action["route"], extra={"record_type": failure["record_type"] if policy == "origin_bound_typed" else "UNTYPED_NEGATIVE" if policy == "naive_sliding_untyped" else None, "retry_after": action["retry_after"]})
        elif kind == "route_probe":
            request = {**query, **action["query"]}
            tier = action.get("at", "A")
            if policy == "origin_bound_typed":
                for failure_key in list(failures):
                    if now >= failures[failure_key]["retained_until"]:
                        failures.pop(failure_key)
            rec = cache.get(tier)
            if policy == "naive_sliding_untyped" and rec and rec.get("query", {}).get("target_id") == request.get("target_id") and now <= rec.get("expires_at", -1):
                cache_reuses += 1
                emit(action, event_type="route_probe", time=now, status=rec["result"], record=rec, reason="untyped_failure_suppressed_all_routes", extra={"attempted_routes": [], "healthy_route_suppressed": "B"})
                continue
            attempted, answer = [], "UNKNOWN_DEPENDENCY_UNAVAILABLE"
            for route_row in action["routes"]:
                route = route_row["route"]
                active_failure = failures.get(f"{tier}:{route}")
                if policy == "origin_bound_typed" and active_failure and now < active_failure["retry_after"]:
                    continue
                attempted.append(route)
                route_attempts += 1
                if route_row["outcome"] == "TIMEOUT":
                    route_failures_seen += 1
                    if policy == "origin_bound_typed":
                        failures[f"{tier}:{route}"] = {"record_type": "OBSERVATION_ROUTE_FAILURE", "route": route, "failure_class": "TIMEOUT", "retry_after": now + 5, "retained_until": now + 5 + ttl, "query": request}
                    elif policy == "naive_sliding_untyped":
                        cache["A"] = {"record_type": "UNTYPED_NEGATIVE", "query": dict(query), "result": "NO_MATCH_WITHIN_CERTIFIED_SCOPE", "evaluation_id": "failure-miscast", "origin_evaluated_at": now, "origin_expiry": now + ttl, "expires_at": now + ttl}
                    continue
                answer = route_row["outcome"]
                break
            emit(action, event_type="route_probe", time=now, status=answer, reason="route_scoped_failure_does_not_hide_healthy_route", extra={"attempted_routes": attempted, "healthy_route_suppressed": None})
        else:
            raise ValueError(f"unknown action {kind}")

    return {
        "case": case_id, "policy": policy, "events": events,
        "summary": {
            "producer_attempts": producer_attempts, "route_attempts": route_attempts,
            "route_failures": route_failures_seen, "cache_reuses": cache_reuses,
            "expired_origin_reuses": expired_origin_reuses, "cache_entries": len(cache),
            "failure_entries": len(failures), "retained_entries": len(cache) + len(failures),
            "retained_bytes": storage_bytes(cache, failures),
            "unknown_results": sum(row["status"] == "UNKNOWN" or row["status"] == "UNKNOWN_DEPENDENCY_UNAVAILABLE" for row in events),
            "offered_requests": len({row.get("request_id") for row in events if row.get("request_id")}),
            "request_ids": sorted({row.get("request_id") for row in events if row.get("request_id")}),
            "false_freshness_rows": expired_origin_reuses, "authority_granted": False,
        },
    }


def run(data):
    result = {"study": data["study"], "policies": list(POLICIES), "cases": {}}
    for case_id, case in data["cases"].items():
        seed = {**data["seed"], **case.get("seed_overrides", {})}
        case_with_seed = {**case, "seed_record": seed}
        result["cases"][case_id] = {policy: run_case(case_id, case_with_seed, data["query"], data["ttl"], policy) for policy in POLICIES}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("output path already exists; refusing overwrite")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = run(data)
    args.out.mkdir(parents=True)
    rows = []
    for case_id, by_policy in result["cases"].items():
        for policy in POLICIES:
            row = by_policy[policy]
            rows.extend(row["events"])
    with (args.out / "events.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    (args.out / "results.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
