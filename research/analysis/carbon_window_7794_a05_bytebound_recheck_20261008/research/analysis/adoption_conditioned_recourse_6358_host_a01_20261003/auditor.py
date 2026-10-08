"""Independent event-ledger auditor; intentionally does not import candidate.py."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ALLOCATION = "ADOPTION-CONDITIONED-RECOURSE-6358-T0-MAC-HOST-20261003-01"
POLICIES = {"generic_retry", "witness_only", "public_warning_stagger", "recipient_specific_routing", "wording_placebo", "no_advice", "abandon_eligible_control"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _route_options(case: dict, offer: dict, policy: str) -> list[str]:
    if case["topology"] == "disjoint_by_offer":
        return [offer["resource"]]
    if policy in {"generic_retry", "witness_only", "public_warning_stagger", "wording_placebo", "abandon_eligible_control"}:
        return ["shared"]
    return list(offer["allowed_resources"])


def _expected_block(case: dict, offer: dict, policy: str):
    if policy == "no_advice":
        return "NO_ADVICE", "CONSERVATIVE_TYPED_STOP"
    if not offer["adopted"]:
        return "NOT_ADOPTED", "UNRESOLVED_NOT_ADOPTED"
    if offer["adoption_tick"] > case["advice_expires"]:
        return "EXPIRED", "STALE_ADVICE"
    if offer["effect_state"] == "UNKNOWN" or not offer["idempotent"]:
        return "BLOCKED_UNCERTAIN_EFFECT", "UNKNOWN_NO_RETRY"
    return None


def _audit_policy(case: dict, policy: str, result: dict) -> list[str]:
    errors = []
    if result.get("policy") != policy:
        return [f"{policy}: policy label mismatch"]
    frozen = {o["id"]: o for o in case["offers"]}
    rows = result.get("offers")
    if not isinstance(rows, list):
        return [f"{policy}: missing offer ledger"]
    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    if len(ids) != len(set(ids)) or set(ids) != set(frozen):
        errors.append(f"{policy}: duplicate, missing, or extra offered-stop IDs")
    by_id = {r.get("id"): r for r in rows if isinstance(r, dict)}
    scheduled: dict[str, list[tuple[int, int, str]]] = {r: [] for r in case["resources"]}
    for offer_id, offer in frozen.items():
        row = by_id.get(offer_id)
        if row is None:
            continue
        attempts = row.get("attempts")
        if not isinstance(attempts, list):
            errors.append(f"{policy}/{offer_id}: attempts not a list")
            continue
        blocked = _expected_block(case, offer, policy)
        if blocked:
            if (row.get("advice_status"), row.get("outcome")) != blocked or attempts or row.get("resolved") or row.get("resource") is not None:
                errors.append(f"{policy}/{offer_id}: blocked/no-advice stop was altered or executed")
            continue
        censor_key = "shared" if case["topology"] != "disjoint_by_offer" else offer["resource"]
        if policy == "abandon_eligible_control" and case["topology"] != "disjoint_by_offer" and len(scheduled.get(censor_key, [])) >= 2:
            if attempts or row.get("resource") is not None or row.get("resolved") or row.get("outcome") != "UNRESOLVED_ELIGIBLE_SUPPRESSED":
                errors.append(f"{policy}/{offer_id}: suppression not retained as unresolved")
            continue
        if not attempts:
            if row.get("advice_status") != "NO_FEASIBLE_ROUTE" or row.get("outcome") != "NO_FEASIBLE_RECOURSE" or row.get("resolved"):
                errors.append(f"{policy}/{offer_id}: eligible offer lacks attempt or typed no-route outcome")
            continue
        resource = row.get("resource")
        if resource not in _route_options(case, offer, policy) or resource not in offer["allowed_resources"]:
            errors.append(f"{policy}/{offer_id}: resource route is forbidden or inconsistent with the assigned arm")
        if len(attempts) != 2:
            errors.append(f"{policy}/{offer_id}: recovery must have exactly two serial receipts")
            continue
        unit = case["resources"].get(resource, {}).get("step_duration")
        first, second = attempts
        start = first.get("start_tick")
        finish = second.get("end_tick")
        if unit is None or not all(isinstance(x, int) for x in (start, finish)):
            errors.append(f"{policy}/{offer_id}: malformed clock or unknown resource")
            continue
        if (first.get("number"), second.get("number")) != (1, 2) or first.get("receipt") != "NOT_APPLIED_VERIFIED" or second.get("receipt") != "APPLIED_VERIFIED":
            errors.append(f"{policy}/{offer_id}: receipt sequence does not establish safe verified effect")
        key = f"idem:{offer_id}"
        if first.get("idempotency_key") != key or second.get("idempotency_key") != key:
            errors.append(f"{policy}/{offer_id}: idempotency key is not frozen per offer")
        if first.get("end_tick") != start + unit or second.get("start_tick") != start + unit or finish != start + 2 * unit:
            errors.append(f"{policy}/{offer_id}: serial service duration is invalid")
        earliest = offer["adoption_tick"]
        if policy == "public_warning_stagger":
            ordinal = sorted(case["offers"], key=lambda o: (o["adoption_tick"], o["id"])).index(offer)
            earliest += case["stagger_ticks"][ordinal]
        if start < earliest or row.get("advice_status") != "ADOPTED_VALID":
            errors.append(f"{policy}/{offer_id}: service precedes valid/adopted scheduled advice")
        if finish <= case["deadline"]:
            if row.get("outcome") != "RESOLVED_VERIFIED" or row.get("resolved") is not True:
                errors.append(f"{policy}/{offer_id}: timely completion not counted as resolved")
        elif row.get("outcome") != "DEADLINE_MISS" or row.get("resolved") is not False:
            errors.append(f"{policy}/{offer_id}: late completion misclassified")
        scheduled[resource].append((start, finish, offer_id))
        if policy == "wording_placebo" and row.get("advice_variant") != offer["placebo_wording"]:
            errors.append(f"{policy}/{offer_id}: wording placebo token differs from frozen wording")
        if policy == "public_warning_stagger" and row.get("advice_variant") != "COMMON_CAPACITY_WARNING":
            errors.append(f"{policy}/{offer_id}: public warning arm has wrong advisory label")
        if policy == "recipient_specific_routing" and row.get("advice_variant") != "SOURCE_BOUND_ROUTE":
            errors.append(f"{policy}/{offer_id}: recipient-specific route lacks source-bound label")

    for resource, jobs in scheduled.items():
        cap = case["resources"][resource]["capacity"]
        events = []
        for start, finish, offer_id in jobs:
            events.extend(((start, 1, offer_id), (finish, -1, offer_id)))
        live = 0
        for _, delta, _ in sorted(events, key=lambda e: (e[0], e[1])):
            live += delta
            if live > cap:
                errors.append(f"{policy}/{resource}: concurrent service exceeds capacity")
                break
    counts = {}
    for row in rows:
        counts[row.get("outcome")] = counts.get(row.get("outcome"), 0) + 1
    metrics = result.get("metrics", {})
    resolved = sum(row.get("resolved") is True for row in rows)
    if metrics.get("offered") != len(frozen) or metrics.get("resolved_verified") != resolved or metrics.get("all_offer_resolution_rate") != resolved / len(frozen):
        errors.append(f"{policy}: denominator/resolution score does not reconstruct")
    expected_advice_budget = 0 if policy == "no_advice" else len(frozen)
    if any(row.get("advice_issued") is not (policy != "no_advice") for row in rows) or metrics.get("advice_issued") != expected_advice_budget:
        errors.append(f"{policy}: per-offer advice budget differs from the frozen arm")
    if metrics.get("outcomes") != counts:
        errors.append(f"{policy}: outcome counts do not reconstruct")
    expected_deadlines = counts.get("DEADLINE_MISS", 0)
    if metrics.get("deadline_misses") != expected_deadlines:
        errors.append(f"{policy}: deadline misses omitted")
    expected_classes: dict[str, dict[str, int]] = {}
    for row in rows:
        summary = expected_classes.setdefault(row["class"], {"offered": 0, "resolved": 0, "deadline_misses": 0})
        summary["offered"] += 1
        summary["resolved"] += int(row.get("resolved") is True)
        summary["deadline_misses"] += int(row.get("outcome") == "DEADLINE_MISS")
    if metrics.get("recipient_classes") != expected_classes:
        errors.append(f"{policy}: recipient disparity classes do not reconstruct")
    return errors


def audit(cases: dict, cases_sha256: str, candidate: dict) -> dict:
    errors = []
    if candidate.get("schema") != "adoption-conditioned-recourse-raw-v2" or candidate.get("allocation") != ALLOCATION or candidate.get("cases_sha256") != cases_sha256:
        errors.append("candidate schema/allocation/frozen-fixture digest mismatch")
    if candidate.get("policies") != cases["policies"]:
        errors.append("candidate policy inventory differs from frozen definition")
    expected_ids = [c["id"] for c in cases["cases"]]
    observed = candidate.get("cases", [])
    if [c.get("case_id") for c in observed] != expected_ids:
        errors.append("candidate case inventory/order differs from frozen fixture")
    by_case = {row.get("case_id"): row.get("policies", {}) for row in observed}
    for case in cases["cases"]:
        actual = by_case.get(case["id"], {})
        if set(actual) != POLICIES:
            errors.append(f"{case['id']}: assigned policy inventory mismatch")
        for policy in sorted(POLICIES & set(actual)):
            errors.extend(f"{case['id']}: {e}" for e in _audit_policy(case, policy, actual[policy]))

    def n(case_id: str, policy: str) -> int:
        return by_case.get(case_id, {}).get(policy, {}).get("metrics", {}).get("resolved_verified", -1)
    if [n("shared-high-adoption", p) for p in ("generic_retry", "witness_only", "public_warning_stagger", "recipient_specific_routing", "wording_placebo")] != [2, 2, 2, 4, 2]:
        errors.append("primary contrast or wording-only placebo does not match frozen expected counts")
    primary = by_case.get("shared-high-adoption", {})
    for policy in POLICIES:
        if primary.get(policy, {}).get("metrics", {}).get("offered") != 4:
            errors.append(f"primary/{policy}: all four offers must remain in denominator")
    place_rows = primary.get("wording_placebo", {}).get("offers", [])
    generic_rows = primary.get("generic_retry", {}).get("offers", [])
    if [(r.get("resource"), r.get("outcome")) for r in place_rows] != [(r.get("resource"), r.get("outcome")) for r in generic_rows]:
        errors.append("wording placebo changed resource choice or outcome")
    routed = {r["id"]: r for r in primary.get("recipient_specific_routing", {}).get("offers", [])}
    if routed.get("h0", {}).get("resource") != "disjoint" or routed.get("h2", {}).get("resource") != "disjoint":
        errors.append("primary recipient-specific policy failed to diversify eligible flexible cohort")
    if n("shared-high-adoption", "abandon_eligible_control") != 2 or primary.get("abandon_eligible_control", {}).get("metrics", {}).get("eligible_suppressed") != 2:
        errors.append("censoring control failed to retain its two suppressed offers")
    if n("shared-low-adoption", "recipient_specific_routing") != 2 or n("disjoint-resource-null", "recipient_specific_routing") != 4:
        errors.append("low-adoption or disjoint-resource null control failed")
    if n("no-feasible-fallback", "recipient_specific_routing") != 1 or by_case.get("no-feasible-fallback", {}).get("recipient_specific_routing", {}).get("metrics", {}).get("no_feasible_recourse") != 3:
        errors.append("no-feasible-fallback control did not retain explicit no-route outcomes")
    if n("forbidden-alternative", "recipient_specific_routing") != 3 or by_case.get("forbidden-alternative", {}).get("recipient_specific_routing", {}).get("metrics", {}).get("unsafe_or_forbidden_advice") != 0:
        errors.append("forbidden alternative should route only the authorized flexible offer and never execute a forbidden route")
    if n("slow-alternative", "recipient_specific_routing") != 2:
        errors.append("slow alternative case should reject deadline-infeasible slow route")
    for case_id, expected in (("expired-advice", "STALE_ADVICE"), ("uncertain-delivery", "UNKNOWN_NO_RETRY")):
        rows = by_case.get(case_id, {}).get("recipient_specific_routing", {}).get("offers", [])
        if len(rows) != 1 or rows[0].get("outcome") != expected or rows[0].get("attempts"):
            errors.append(f"{case_id}: stale/uncertain advice must remain a no-work stop")
    return {"schema": "adoption-conditioned-recourse-audit-v2", "allocation": ALLOCATION,
            "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_RAW_AUDIT", "cases_checked": len(expected_ids),
            "policies_checked": len(expected_ids) * len(POLICIES), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    raw = audit(cases, _sha(args.cases), candidate)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": raw["status"], "errors": len(raw["errors"]), "sha256": _sha(args.out)}))
    return 0 if raw["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
