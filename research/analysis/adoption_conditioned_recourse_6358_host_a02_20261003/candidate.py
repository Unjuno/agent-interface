"""Deterministic synthetic cohort scheduler for Issue #6358; no external effects."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ALLOCATION = "ADOPTION-CONDITIONED-RECOURSE-6358-T0-MAC-HOST-20261003-02"
POLICIES = ("generic_retry", "witness_only", "public_warning_stagger", "recipient_specific_routing", "wording_placebo", "no_advice", "abandon_eligible_control")


def read_cases(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _service_slots(resources: dict) -> dict[str, list[int]]:
    return {name: [0] * spec["capacity"] for name, spec in resources.items()}


def _reserve(case: dict, slots: dict[str, list[int]], resource: str, tick: int) -> tuple[int, int]:
    index = min(range(len(slots[resource])), key=lambda i: (slots[resource][i], i))
    start = max(slots[resource][index], tick)
    end = start + 2 * case["resources"][resource]["step_duration"]
    slots[resource][index] = end
    return start, end


def _summary(policy: str, rows: list[dict], case: dict) -> dict:
    outcomes: dict[str, int] = {}
    classes: dict[str, dict[str, int]] = {}
    for row in rows:
        outcomes[row["outcome"]] = outcomes.get(row["outcome"], 0) + 1
        cohort = classes.setdefault(row["class"], {"offered": 0, "resolved": 0, "deadline_misses": 0})
        cohort["offered"] += 1
        cohort["resolved"] += int(row["resolved"])
        cohort["deadline_misses"] += int(row["outcome"] == "DEADLINE_MISS")
    total = len(rows)
    return {
        "policy": policy,
        "offers": rows,
        "metrics": {
            "offered": total,
            "advice_issued": sum(row["advice_issued"] for row in rows),
            "resolved_verified": sum(row["resolved"] for row in rows),
            "all_offer_resolution_rate": sum(row["resolved"] for row in rows) / total if total else 0.0,
            "attempted_offers": sum(bool(row["attempts"]) for row in rows),
            "deadline_misses": outcomes.get("DEADLINE_MISS", 0),
            "queue_occupancy_peak": max((sum(1 for row in rows if row["resource"] == name and row["attempts"]) for name in case["resources"]), default=0),
            "unsafe_or_forbidden_advice": sum(row["advice_status"] in ("FORBIDDEN_ROUTE_REJECTED", "UNSAFE_ADVICE_BLOCKED") for row in rows),
            "no_feasible_recourse": outcomes.get("NO_FEASIBLE_RECOURSE", 0),
            "stale_advice": outcomes.get("STALE_ADVICE", 0),
            "unknown_no_retry": outcomes.get("UNKNOWN_NO_RETRY", 0),
            "unresolved_not_adopted": outcomes.get("UNRESOLVED_NOT_ADOPTED", 0),
            "eligible_suppressed": outcomes.get("UNRESOLVED_ELIGIBLE_SUPPRESSED", 0),
            "recipient_classes": classes,
            "outcomes": outcomes,
        },
    }


def _run_policy(case: dict, policy: str) -> dict:
    slots = _service_slots(case["resources"])
    rows = [{"id": offer["id"], "class": offer["class"], "advice_issued": policy != "no_advice", "advice_status": "OFFERED", "advice_variant": None,
             "resource": None, "attempts": [], "outcome": None, "resolved": False} for offer in case["offers"]]
    row_by_id = {row["id"]: row for row in rows}
    offers = {offer["id"]: offer for offer in case["offers"]}

    if policy == "no_advice":
        for row in rows:
            row.update(advice_status="NO_ADVICE", outcome="CONSERVATIVE_TYPED_STOP")
        return _summary(policy, rows, case)

    ordered = sorted(case["offers"], key=lambda o: (o["adoption_tick"], o["id"]))
    served = 0
    for ordinal, offer in enumerate(ordered):
        row = row_by_id[offer["id"]]
        if policy == "wording_placebo":
            row["advice_variant"] = offer["placebo_wording"]
        if not offer["adopted"]:
            row.update(advice_status="NOT_ADOPTED", outcome="UNRESOLVED_NOT_ADOPTED")
            continue
        if offer["adoption_tick"] > case["advice_expires"]:
            row.update(advice_status="EXPIRED", outcome="STALE_ADVICE")
            continue
        if offer["effect_state"] == "UNKNOWN" or not offer["idempotent"]:
            row.update(advice_status="BLOCKED_UNCERTAIN_EFFECT", outcome="UNKNOWN_NO_RETRY")
            continue
        if policy == "abandon_eligible_control" and served >= 2 and case["topology"] != "disjoint_by_offer":
            row.update(advice_status="SUPPRESSED_BY_ABANDONMENT_CONTROL", outcome="UNRESOLVED_ELIGIBLE_SUPPRESSED")
            continue

        route_options = [offer["resource"]] if case["topology"] == "disjoint_by_offer" else list(offer["allowed_resources"])
        if policy in ("generic_retry", "witness_only", "public_warning_stagger", "wording_placebo", "abandon_eligible_control"):
            route_options = [offer["resource"]] if case["topology"] == "disjoint_by_offer" else ["shared"]
        if policy == "public_warning_stagger":
            tick = offer["adoption_tick"] + case["stagger_ticks"][ordinal]
        else:
            tick = offer["adoption_tick"]

        feasible = []
        for resource in route_options:
            if resource not in offer["allowed_resources"]:
                continue
            spec = case["resources"][resource]
            earliest = max(min(slots[resource]), tick)
            finish = earliest + 2 * spec["step_duration"]
            if finish <= case["deadline"]:
                feasible.append((finish, resource))
        if not feasible:
            row.update(advice_status="NO_FEASIBLE_ROUTE", outcome="NO_FEASIBLE_RECOURSE")
            continue

        _, resource = min(feasible, key=lambda item: (item[0], item[1]))
        start, finish = _reserve(case, slots, resource, tick)
        duration = case["resources"][resource]["step_duration"]
        key = f"idem:{offer['id']}"
        row.update(resource=resource, advice_status="ADOPTED_VALID")
        if policy == "public_warning_stagger":
            row["advice_variant"] = "COMMON_CAPACITY_WARNING"
        elif policy == "recipient_specific_routing":
            row["advice_variant"] = "SOURCE_BOUND_ROUTE"
        row["attempts"] = [
            {"number": 1, "start_tick": start, "end_tick": start + duration, "receipt": "NOT_APPLIED_VERIFIED", "idempotency_key": key},
            {"number": 2, "start_tick": start + duration, "end_tick": finish, "receipt": "APPLIED_VERIFIED", "idempotency_key": key},
        ]
        if finish <= case["deadline"]:
            row.update(outcome="RESOLVED_VERIFIED", resolved=True)
        else:
            row.update(outcome="DEADLINE_MISS", resolved=False)
        served += 1
    return _summary(policy, rows, case)


def simulate(cases: dict, cases_sha256: str) -> dict:
    return {"schema": "adoption-conditioned-recourse-raw-v2", "allocation": ALLOCATION, "cases_sha256": cases_sha256,
            "policies": list(POLICIES), "cases": [{"case_id": case["id"], "policies": {policy: _run_policy(case, policy) for policy in POLICIES}} for case in cases["cases"]]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cases, digest = read_cases(args.cases)
    raw = json.dumps(simulate(cases, digest), sort_keys=True, indent=2) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(raw, encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "cases": len(cases["cases"]), "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
