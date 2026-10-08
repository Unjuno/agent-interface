"""One-shot candidate for finite service-debt representation traces."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ALLOCATION_ID = "SERVICE-DEBT-ALIAS-8571-A01"
BASE_REVISION = "5215aab506f43c8a02470d495b7352b1326a9580"
SCHEMA = "service-debt-alias-candidate-raw-v1"
POLICIES = ("fifo", "presented_service_debt", "trusted_parent_service_debt")


def expand_cases(fixture: dict) -> list[dict]:
    """Instantiate the frozen caller partitions without consulting outcomes."""
    cases = []
    for partition in fixture["alias_partitions"]:
        requests = [dict(request) for request in fixture["base_requests"]]
        trusted = {"B": "B"}
        for block_index, block in enumerate(partition["blocks"]):
            caller = f"A_alias_{block_index}"
            trusted[caller] = "A"
            for request_index in block:
                requests[2 * request_index]["caller_id"] = caller
        cases.append({
            "id": partition["id"], "requests": requests,
            "trusted_parents": trusted,
            "parent_claims": dict(partition.get("parent_claims", {})),
            "release_times": [],
        })
    cases.extend(dict(case) for case in fixture["extra_cases"])
    return cases


def _denial(request: dict, case: dict, now: int) -> str | None:
    caller = request["caller_id"]
    if caller not in case["trusted_parents"]:
        return "UNTRUSTED_CALLER"
    if request["authority_current"] is not True:
        return "NO_CURRENT_AUTHORITY"
    if request["fresh"] is not True:
        return "STALE_EVIDENCE"
    if request["joint_grant"] is not True:
        return "MISSING_JOINT_GRANT"
    if request["conflict_free"] is not True:
        return "CONFLICT"
    revoked_at = request["revoked_at"]
    if revoked_at is not None and revoked_at <= now:
        return "REVOKED"
    return None


def _group(request: dict, policy: str, case: dict) -> str:
    if policy == "presented_service_debt":
        return request["caller_id"]
    if policy == "trusted_parent_service_debt":
        return case["trusted_parents"][request["caller_id"]]
    raise ValueError("FIFO has no debt group")


def _choose(ready: list[dict], policy: str, case: dict,
            debt: dict[str, int], turn: int) -> dict:
    if policy == "fifo":
        return min(ready, key=lambda item: (item["arrival"], item["ordinal"], item["id"]))
    groups = sorted({_group(item, policy, case) for item in ready})
    offset = turn % len(groups)
    rotated = groups[offset:] + groups[:offset]
    rank = {group: index for index, group in enumerate(rotated)}
    return min(ready, key=lambda item: (
        debt.get(_group(item, policy, case), 0),
        rank[_group(item, policy, case)],
        item["arrival"], item["ordinal"], item["id"],
    ))


def simulate(case: dict, policy: str, horizon: int) -> dict:
    if policy not in POLICIES:
        raise ValueError("unknown scheduling policy")
    requests = {item["id"]: dict(item) for item in case["requests"]}
    pending = set(requests)
    excluded = []
    for request_id in sorted(requests):
        reason = _denial(requests[request_id], case, 0)
        if reason is not None:
            excluded.append({"request_id": request_id, "reason": reason})
            pending.remove(request_id)

    claims = []
    for caller, claimed_parent in sorted(case["parent_claims"].items()):
        trusted_parent = case["trusted_parents"].get(caller)
        claims.append({
            "caller_id": caller,
            "claimed_parent": claimed_parent,
            "trusted_parent": trusted_parent,
            "decision": "ACCEPTED" if trusted_parent == claimed_parent else "REJECTED_FALSE_PARENT_LINK",
        })

    debt: dict[str, int] = {}
    attempts = []
    releases = []
    turn = 0
    now = 0
    release_times = sorted(case["release_times"])
    termination = "EMPTY_QUEUE"

    while True:
        if now >= horizon:
            termination = "HORIZON"
            break
        next_release = next((time for time in release_times if time not in releases), None)
        if next_release is not None and next_release <= now:
            releases.append(next_release)
            termination = "MANDATORY_RELEASE"
            break

        ready = [requests[request_id] for request_id in pending
                 if requests[request_id]["arrival"] <= now
                 and _denial(requests[request_id], case, now) is None
                 and now + requests[request_id]["service"] <= requests[request_id]["deadline"]]
        if next_release is not None:
            ready = [item for item in ready if now + item["service"] <= next_release]

        if not ready:
            future_arrivals = [requests[request_id]["arrival"] for request_id in pending
                               if requests[request_id]["arrival"] > now]
            future_events = future_arrivals + ([next_release] if next_release is not None else [])
            if future_events and min(future_events) <= horizon:
                now = min(future_events)
                if next_release is not None and now == next_release:
                    releases.append(next_release)
                    termination = "MANDATORY_RELEASE"
                    break
                continue
            termination = "NO_ELIGIBLE_WORK"
            break

        chosen = _choose(ready, policy, case, debt, turn)
        start = now
        end = start + chosen["service"]
        if end > horizon:
            termination = "HORIZON"
            break
        if next_release is not None and end > next_release:
            releases.append(next_release)
            termination = "MANDATORY_RELEASE"
            break

        attempts.append({
            "request_id": chosen["id"],
            "caller_id": chosen["caller_id"],
            "start": start,
            "end": end,
            "service": chosen["service"],
        })
        pending.remove(chosen["id"])
        if policy != "fifo":
            group = _group(chosen, policy, case)
            debt[group] = debt.get(group, 0) + chosen["service"]
            turn += 1
        now = end

    return {
        "case_id": case["id"],
        "policy": policy,
        "attempts": attempts,
        "excluded": excluded,
        "parent_claims": claims,
        "release_events": releases,
        "termination": termination,
    }


def run(fixture: dict) -> dict:
    if fixture.get("base_revision") != BASE_REVISION:
        raise ValueError("frozen base revision mismatch")
    rows = []
    for case in expand_cases(fixture):
        for policy in fixture["policies"]:
            rows.append(simulate(case, policy, fixture["horizon"]))
    return {
        "schema": SCHEMA,
        "allocation_id": fixture["allocation_id"],
        "base_revision": fixture["base_revision"],
        "rows": rows,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py TRACE_FIXTURE OUTPUT_JSON")
    source_path, output_path = map(Path, argv[1:])
    fixture = json.loads(source_path.read_text(encoding="utf-8"))
    result = run(fixture)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(f"candidate_rows={len(result['rows'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

