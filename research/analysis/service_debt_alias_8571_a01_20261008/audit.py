"""Independent raw-only replay for the service-debt alias finite trace."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ALLOCATION_ID = "SERVICE-DEBT-ALIAS-8571-A01"
RAW_SCHEMA = "service-debt-alias-candidate-raw-v1"
AUDIT_SCHEMA = "service-debt-alias-independent-audit-v1"


def _cases(fixture: dict) -> list[dict]:
    """Reconstruct inputs independently of candidate.expand_cases."""
    result = []
    for item in fixture["alias_partitions"]:
        source = fixture["base_requests"]
        requests = []
        trust = {"B": "B"}
        seen = []
        for block_number, indices in enumerate(item["blocks"]):
            caller = f"A_alias_{block_number}"
            trust[caller] = "A"
            for index in indices:
                seen.append(index)
        if sorted(seen) != list(range(4)) or len(seen) != len(set(seen)):
            raise ValueError("invalid frozen alias partition")
        block_for = {index: number for number, block in enumerate(item["blocks"]) for index in block}
        for request in source:
            copied = dict(request)
            if copied["id"].startswith("A"):
                number = int(copied["id"][1:])
                copied["caller_id"] = f"A_alias_{block_for[number]}"
            requests.append(copied)
        result.append({
            "id": item["id"], "requests": requests,
            "trusted_parents": trust,
            "parent_claims": dict(item.get("parent_claims", {})),
            "release_times": [],
        })
    result.extend(dict(entry) for entry in fixture["extra_cases"])
    return result


def _canonical_partition(blocks: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(sorted(block)) for block in blocks))


def _all_partitions_four() -> set[tuple[tuple[int, ...], ...]]:
    partitions: set[tuple[tuple[int, ...], ...]] = set()
    def place(index: int, blocks: list[list[int]]) -> None:
        if index == 4:
            partitions.add(_canonical_partition(blocks))
            return
        for block_index in range(len(blocks)):
            blocks[block_index].append(index)
            place(index + 1, blocks)
            blocks[block_index].pop()
        blocks.append([index])
        place(index + 1, blocks)
        blocks.pop()
    place(0, [])
    return partitions


def _reason(request: dict, case: dict, moment: int) -> str | None:
    if request["caller_id"] not in case["trusted_parents"]:
        return "UNTRUSTED_CALLER"
    if request["authority_current"] is not True:
        return "NO_CURRENT_AUTHORITY"
    if request["fresh"] is not True:
        return "STALE_EVIDENCE"
    if request["joint_grant"] is not True:
        return "MISSING_JOINT_GRANT"
    if request["conflict_free"] is not True:
        return "CONFLICT"
    if request["revoked_at"] is not None and request["revoked_at"] <= moment:
        return "REVOKED"
    return None


def _debt_group(request: dict, policy: str, trusted: dict) -> str:
    return request["caller_id"] if policy == "presented_service_debt" else trusted[request["caller_id"]]


def _reference_row(case: dict, policy: str, horizon: int) -> dict:
    """Use event validation and a separate group-first tie resolver."""
    requests = {request["id"]: dict(request) for request in case["requests"]}
    not_pending = set()
    exclusions = []
    for key, request in requests.items():
        why = _reason(request, case, 0)
        if why:
            not_pending.add(key)
            exclusions.append({"request_id": key, "reason": why})
    exclusions.sort(key=lambda value: value["request_id"])

    claims = []
    for caller, proposed in sorted(case["parent_claims"].items()):
        established = case["trusted_parents"].get(caller)
        claims.append({
            "caller_id": caller,
            "claimed_parent": proposed,
            "trusted_parent": established,
            "decision": "ACCEPTED" if proposed == established else "REJECTED_FALSE_PARENT_LINK",
        })

    remaining = set(requests) - not_pending
    debt: dict[str, int] = {}
    attempts = []
    releases = []
    cursor = 0
    tick = 0
    events = sorted(case["release_times"])
    stop = "EMPTY_QUEUE"

    while True:
        if tick >= horizon:
            stop = "HORIZON"
            break
        due = [value for value in events if value not in releases and value <= tick]
        if due:
            releases.extend(sorted(due))
            stop = "MANDATORY_RELEASE"
            break
        next_event = next((value for value in events if value not in releases), None)

        ready = []
        for key in remaining:
            request = requests[key]
            if request["arrival"] > tick or _reason(request, case, tick):
                continue
            if tick + request["service"] > request["deadline"]:
                continue
            if next_event is not None and tick + request["service"] > next_event:
                continue
            ready.append(request)

        if not ready:
            next_arrival = [requests[key]["arrival"] for key in remaining
                            if requests[key]["arrival"] > tick]
            milestones = next_arrival + ([next_event] if next_event is not None else [])
            if milestones and min(milestones) <= horizon:
                tick = min(milestones)
                if next_event is not None and tick == next_event:
                    releases.append(next_event)
                    stop = "MANDATORY_RELEASE"
                    break
                continue
            stop = "NO_ELIGIBLE_WORK" if not remaining else "EMPTY_QUEUE"
            break

        if policy == "fifo":
            selected = sorted(ready, key=lambda value: (
                value["arrival"], value["ordinal"], value["id"]))[0]
        else:
            groups = sorted({_debt_group(value, policy, case["trusted_parents"]) for value in ready})
            smallest = min(debt.get(group, 0) for group in groups)
            candidates = {group for group in groups if debt.get(group, 0) == smallest}
            rotated = groups[cursor % len(groups):] + groups[:cursor % len(groups)]
            winner = next(group for group in rotated if group in candidates)
            selected = min((value for value in ready
                            if _debt_group(value, policy, case["trusted_parents"]) == winner),
                           key=lambda value: (value["arrival"], value["ordinal"], value["id"]))

        start = tick
        finish = start + selected["service"]
        if finish > horizon:
            stop = "HORIZON"
            break
        if next_event is not None and finish > next_event:
            releases.append(next_event)
            stop = "MANDATORY_RELEASE"
            break
        attempts.append({
            "request_id": selected["id"], "caller_id": selected["caller_id"],
            "start": start, "end": finish, "service": selected["service"],
        })
        remaining.remove(selected["id"])
        if policy != "fifo":
            key = _debt_group(selected, policy, case["trusted_parents"])
            debt[key] = debt.get(key, 0) + selected["service"]
            cursor += 1
        tick = finish

    return {
        "case_id": case["id"], "policy": policy,
        "attempts": attempts, "excluded": exclusions,
        "parent_claims": claims, "release_events": releases,
        "termination": stop,
    }


def _eligible_principals(case: dict, oracle: dict) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for request in case["requests"]:
        principal = oracle["request_truth"][request["id"]]["principal"]
        if _reason(request, case, 0) is None:
            result.setdefault(principal, set()).add(request["id"])
    return result


def _metrics(case: dict, row: dict, oracle: dict, horizon: int) -> dict:
    requests = {request["id"]: request for request in case["requests"]}
    eligible = _eligible_principals(case, oracle)
    principals = sorted(set(eligible) | {
        oracle["request_truth"][item["request_id"]]["principal"]
        for item in row["excluded"]
    })
    units = {principal: 0 for principal in principals}
    dispatch_count = {principal: 0 for principal in principals}
    useful = {principal: 0 for principal in principals}
    first_start: dict[str, int] = {}
    pending = {p: set(ids) for p, ids in eligible.items()}
    run_bypass = {p: 0 for p in eligible}
    peak_bypass = {p: 0 for p in eligible}

    for attempt in row["attempts"]:
        identity = oracle["request_truth"][attempt["request_id"]]
        principal = identity["principal"]
        for other in eligible:
            if other == principal:
                run_bypass[other] = 0
            elif pending.get(other):
                run_bypass[other] += 1
                peak_bypass[other] = max(peak_bypass[other], run_bypass[other])
        units[principal] = units.get(principal, 0) + attempt["service"]
        dispatch_count[principal] = dispatch_count.get(principal, 0) + 1
        first_start.setdefault(principal, attempt["start"])
        pending.get(principal, set()).discard(attempt["request_id"])
        request = requests[attempt["request_id"]]
        if identity["verified_useful"] is True and attempt["end"] <= request["deadline"]:
            useful[principal] = useful.get(principal, 0) + 1

    first_wait = {}
    censored_wait = {}
    for principal, request_ids in eligible.items():
        first_arrival = min(requests[key]["arrival"] for key in request_ids)
        first_wait[principal] = (first_start[principal] - first_arrival
                                 if principal in first_start else None)
        censored_wait[principal] = (None if principal in first_start else
                                    max(0, horizon - first_arrival))
    return {
        "eligible_request_count": {principal: len(ids) for principal, ids in eligible.items()},
        "dispatch_count": units_to_json(dispatch_count),
        "service_units": units_to_json(units),
        "first_dispatch_wait": first_wait,
        "right_censored_wait_at_horizon": censored_wait,
        "max_consecutive_bypasses": peak_bypass,
        "verified_useful_on_time_completions": units_to_json(useful),
    }


def units_to_json(value: dict[str, int]) -> dict[str, int]:
    return {key: value[key] for key in sorted(value)}


def _study_decision(metrics: dict[str, dict], partitions: list[dict]) -> tuple[str, dict]:
    indexed = {(key.split("|", 1)[0], key.split("|", 1)[1]): value
               for key, value in metrics.items()}
    base_id = partitions[0]["id"]
    base_presented = indexed[(base_id, "presented_service_debt")]["service_units"]
    base_trusted = indexed[(base_id, "trusted_parent_service_debt")]["service_units"]
    alias_advantages = []
    trust_replays = []
    for partition in partitions:
        present = indexed[(partition["id"], "presented_service_debt")]["service_units"]
        trusted = indexed[(partition["id"], "trusted_parent_service_debt")]["service_units"]
        if len(partition["blocks"]) > 1:
            alias_advantages.append({
                "partition": partition["id"],
                "A_presented_units": present.get("A", 0),
                "A_one_identity_units": base_presented.get("A", 0),
                "advantage_observed": present.get("A", 0) > base_presented.get("A", 0),
            })
        trust_replays.append({
            "partition": partition["id"],
            "matches_one_identity_service_units": trusted == base_trusted,
        })
    # The preregistered claim is existential over the complete fixed partition
    # set: one unchanged-demand representation may expose an advantage; null
    # partitions remain in the report and are not discarded.
    conditions = any(item["advantage_observed"] for item in alias_advantages)
    conditions = conditions and all(item["matches_one_identity_service_units"] for item in trust_replays)
    summary = {
        "alias_partition_count": len(partitions),
        "nontrivial_alias_partitions": len(alias_advantages),
        "alias_advantages": alias_advantages,
        "trusted_parent_replays": trust_replays,
        "one_identity_presented_debt_service_units": base_presented,
        "one_identity_trusted_debt_service_units": base_trusted,
    }
    return ("PASS_METHOD_SCOPED" if conditions else "FAIL_NO_ALIAS_ADVANTAGE_IN_FIXTURE"), summary


def audit(fixture: dict, oracle: dict, raw: dict) -> dict:
    errors = []
    if set(raw) != {"schema", "allocation_id", "base_revision", "rows"}:
        errors.append("RAW_TOP_LEVEL_SHAPE_MISMATCH")
    if raw.get("schema") != RAW_SCHEMA:
        errors.append("RAW_SCHEMA_MISMATCH")
    if raw.get("allocation_id") != fixture.get("allocation_id"):
        errors.append("ALLOCATION_ID_MISMATCH")
    if raw.get("base_revision") != fixture.get("base_revision"):
        errors.append("BASE_REVISION_MISMATCH")
    observed_partitions = [_canonical_partition(item["blocks"]) for item in fixture["alias_partitions"]]
    if len(observed_partitions) != 15 or set(observed_partitions) != _all_partitions_four():
        errors.append("PARTITION_ENUMERATION_INCOMPLETE")
    cases = _cases(fixture)
    for case in cases:
        for request in case["requests"]:
            expected_parent = oracle["request_truth"][request["id"]]["principal"]
            if case["trusted_parents"].get(request["caller_id"]) != expected_parent:
                errors.append(f"TRUSTED_PARENT_ORACLE_MISMATCH:{case['id']}:{request['id']}")
    expected_keys = [(case["id"], policy) for case in cases for policy in fixture["policies"]]
    actual_rows = raw.get("rows")
    if type(actual_rows) is not list or len(actual_rows) != len(expected_keys):
        errors.append("ROW_COUNT_MISMATCH")
        actual_rows = actual_rows if type(actual_rows) is list else []
    by_key = {}
    for row in actual_rows:
        key = (row.get("case_id"), row.get("policy")) if type(row) is dict else (None, None)
        if key in by_key:
            errors.append("DUPLICATE_ROW_KEY")
        by_key[key] = row

    metrics = {}
    case_by_id = {case["id"]: case for case in cases}
    for case_id, policy in expected_keys:
        key = (case_id, policy)
        row = by_key.get(key)
        if row is None:
            errors.append(f"MISSING_ROW:{case_id}:{policy}")
            continue
        expected = _reference_row(case_by_id[case_id], policy, fixture["horizon"])
        if row != expected:
            errors.append(f"RAW_REPLAY_MISMATCH:{case_id}:{policy}")
            continue
        for attempt in row["attempts"]:
            if attempt["request_id"] not in oracle["request_truth"]:
                errors.append(f"ORACLE_MISSING_REQUEST:{attempt['request_id']}")
        metric_key = f"{case_id}|{policy}"
        metrics[metric_key] = _metrics(case_by_id[case_id], row, oracle, fixture["horizon"])

    expected_order = expected_keys
    actual_order = [(row.get("case_id"), row.get("policy")) for row in actual_rows if type(row) is dict]
    if actual_order != expected_order:
        errors.append("ROW_ORDER_MISMATCH")

    decision, alias_summary = _study_decision(metrics, fixture["alias_partitions"]) if not errors else ("FAIL_METHOD", {})
    if not errors:
        base_trusted_order = [attempt["request_id"] for attempt in
                              by_key[(fixture["alias_partitions"][0]["id"], "trusted_parent_service_debt")]["attempts"]]
        for partition in fixture["alias_partitions"]:
            current_order = [attempt["request_id"] for attempt in
                             by_key[(partition["id"], "trusted_parent_service_debt")]["attempts"]]
            if current_order != base_trusted_order:
                errors.append(f"TRUSTED_PARENT_TRACE_CHANGED:{partition['id']}")
        if "honest_three_principals|trusted_parent_service_debt" in metrics:
            distinct = metrics["honest_three_principals|trusted_parent_service_debt"]["service_units"]
            if distinct != {"A": 1, "B": 1, "C": 1}:
                errors.append("DISTINCT_PRINCIPAL_CONTROL_FAILED")
        if "revoked_principal|trusted_parent_service_debt" in metrics:
            revoked = metrics["revoked_principal|trusted_parent_service_debt"]["service_units"]
            if revoked.get("A", 0) != 0 or revoked.get("B", 0) != 4:
                errors.append("REVOKED_REQUEST_CONTROL_FAILED")
        if ("missing_joint_grant", "trusted_parent_service_debt") in by_key:
            missing = by_key[("missing_joint_grant", "trusted_parent_service_debt")]
            if "J_A1" not in {item["request_id"] for item in missing["excluded"]}:
                errors.append("JOINT_GRANT_CONTROL_FAILED")
        if ("false_parent_claim", "trusted_parent_service_debt") in by_key:
            false_claim = by_key[("false_parent_claim", "trusted_parent_service_debt")]
            if not any(item["decision"] == "REJECTED_FALSE_PARENT_LINK" for item in false_claim["parent_claims"]):
                errors.append("FALSE_PARENT_LINK_CONTROL_FAILED")
        if ("mandatory_release", "trusted_parent_service_debt") in by_key:
            release = by_key[("mandatory_release", "trusted_parent_service_debt")]
            if release["release_events"] != [2] or any(item["end"] > 2 for item in release["attempts"]):
                errors.append("MANDATORY_RELEASE_CONTROL_FAILED")
        if ("fragmentation_base|trusted_parent_service_debt" in metrics and
                "fragmentation_split|trusted_parent_service_debt" in metrics):
            base_fragment = metrics["fragmentation_base|trusted_parent_service_debt"]["service_units"]
            split_fragment = metrics["fragmentation_split|trusted_parent_service_debt"]["service_units"]
            if base_fragment != split_fragment:
                errors.append("FRAGMENTATION_SERVICE_ALLOCATION_CHANGED")
        if errors:
            decision = "FAIL_METHOD"

    return {
        "schema": AUDIT_SCHEMA,
        "allocation_id": fixture.get("allocation_id"),
        "rows_checked": len(metrics),
        "errors": errors,
        "disposition": decision,
        "alias_summary": alias_summary,
        "metrics": metrics,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        raise SystemExit("usage: audit.py TRACE_FIXTURE OUTCOME_ORACLE CANDIDATE_RAW OUTPUT_JSON")
    fixture_path, oracle_path, raw_path, output_path = map(Path, argv[1:])
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    result = audit(fixture, oracle, raw)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(f"disposition={result['disposition']} rows_checked={result['rows_checked']} errors={len(result['errors'])}")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

