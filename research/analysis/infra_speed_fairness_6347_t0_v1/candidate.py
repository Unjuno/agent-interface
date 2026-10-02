"""Deterministic synthetic scheduler candidate for Issue #6347 T0."""
import json
import sys
from pathlib import Path


POLICIES = ("frfs", "arrival_fifo", "batch_rotate")
PRINCIPALS = ("A", "B")
WINDOW = 5


def _intent_rows(case, origins, delays, sends=None, kind="normal", swap=False):
    sends = sends or {p: 0 for p in PRINCIPALS}
    result = []
    for principal in PRINCIPALS:
        source = delays[principal]
        transport = source.get("transport", 0)
        compute = source.get("compute", 0)
        if swap:
            source = delays["B" if principal == "A" else "A"]
            transport = source.get("transport", 0)
            compute = source.get("compute", 0)
        origin = origins[principal]
        result.append({
            "id": f"{case}-{principal}", "principal": principal,
            "origin": origin, "arrival": origin + sends.get(principal, 0) + transport,
            "ready": origin + sends.get(principal, 0) + transport + compute,
            "grant": "active", "evidence_expiry": 10000,
            "revoke_at": None, "deadline": 10000, "completion_cost": 1,
            "resource": "focus", "eligible": True, "kind": kind,
        })
    return result


def _one(case, intents, policy, pointer, rights="equal", kind="normal"):
    if rights != "equal":
        return {"winner": None, "status": "HOLD_NO_TIE_RIGHTS", "admission": None,
                "completion": None, "reason": "no declared decision right", "pointer_after": pointer}
    batch = policy == "batch_rotate" and kind not in ("critical", "short_deadline", "disjoint")
    if kind == "short_deadline":
        batch = False
    ordered = sorted(intents, key=lambda x: (x["ready"], x["id"]))
    if not ordered:
        return {"winner": None, "status": "REFUSE", "admission": None,
                "completion": None, "reason": "no eligible intents", "pointer_after": pointer}
    if batch:
        admission = ordered[0]["ready"] + WINDOW
        available = [x for x in ordered if x["ready"] <= admission]
        if available:
            rank = {p: (0 if p == pointer else 1) for p in PRINCIPALS}
            selected = sorted(available, key=lambda x: (rank[x["principal"]], x["id"]))[0]
        else:
            selected = ordered[0]
    elif policy == "arrival_fifo":
        selected = sorted(intents, key=lambda x: (x["arrival"], x["id"]))[0]
        admission = selected["ready"]
    else:
        selected = ordered[0]
        admission = selected["ready"]

    if selected["kind"] == "critical":
        admission = selected["ready"]
    if selected.get("revoke_at") is not None and admission >= selected["revoke_at"]:
        return {"winner": None, "status": "REFUSE_REVOKED", "admission": admission,
                "completion": None, "reason": "grant revoked before admission", "pointer_after": pointer}
    if admission >= selected["evidence_expiry"]:
        return {"winner": None, "status": "REFUSE_STALE", "admission": admission,
                "completion": None, "reason": "evidence expired before admission", "pointer_after": pointer}
    completion = admission + selected["completion_cost"]
    if completion >= selected["deadline"]:
        return {"winner": None, "status": "REFUSE_DEADLINE", "admission": admission,
                "completion": completion, "reason": "completion not strictly before deadline", "pointer_after": pointer}
    if kind == "disjoint":
        admitted = []
        for intent in intents:
            at = intent["ready"]
            if intent["grant"] == "active" and at < intent["evidence_expiry"] and at + intent["completion_cost"] < intent["deadline"]:
                admitted.append(intent["principal"])
        return {"winner": admitted, "status": "ADMITTED_DISJOINT", "admission": admission,
                "completion": completion, "reason": "independent resources", "pointer_after": pointer}
    after = ("B" if selected["principal"] == "A" else "A") if batch else pointer
    return {"winner": selected["principal"], "status": "ADMITTED", "admission": admission,
            "completion": completion, "reason": "eligible at admission", "pointer_after": after}


def _run_sequence(items, swapped, policy):
    pointer = "A"
    rows = []
    for item in items:
        origins = item["origin"]
        delays = {p: {"transport": 0, "compute": item["delay"][p]} for p in PRINCIPALS}
        intents = _intent_rows(item["id"], origins, delays, swap=swapped)
        row = _one(item["id"], intents, policy, pointer)
        row.update({"case": item["id"], "policy": policy,
                    "arm": "delay_swapped" if swapped else "baseline",
                    "phase": "heldout"})
        pointer = row["pointer_after"]
        rows.append(row)
    return rows


def run(fixture):
    rows = []
    for item in fixture["paired_delay_swap"]:
        for swapped in (False, True):
            intents = _intent_rows(item["id"], {p: item["origin"] for p in PRINCIPALS},
                                  {p: {"transport": item["transport"][p], "compute": item["compute"][p]} for p in PRINCIPALS},
                                  swap=swapped)
            for intent in intents:
                intent["deadline"] = item["deadline"]
                intent["completion_cost"] = item["completion_cost"][intent["principal"]]
                intent["evidence_expiry"] = item["evidence_expiry"][intent["principal"]]
            for policy in POLICIES:
                row = _one(item["id"], intents, policy, "A")
                row.update({"case": item["id"], "policy": policy,
                            "arm": "delay_swapped" if swapped else "baseline", "phase": "paired"})
                rows.append(row)
    for policy in POLICIES:
        for swapped in (False, True):
            rows.extend(_run_sequence(fixture["heldout_opportunities"], swapped, policy))

    for item in fixture["boundary_controls"]:
        origins = item["origin"]
        delays = {p: {"transport": 0, "compute": item.get("delay", {}).get(p, 0)} for p in PRINCIPALS}
        sends = item.get("send_offset", {})
        reps = item.get("repetitions", 1)
        for repeat in range(reps):
            for policy in POLICIES:
                intents = _intent_rows(f"{item['id']}-{repeat}", origins, delays, sends=sends)
                row = _one(item["id"], intents, policy, "A" if repeat % 2 == 0 else "B")
                row.update({"case": item["id"], "repeat": repeat, "policy": policy,
                            "arm": "baseline", "phase": "boundary"})
                rows.append(row)

    for item in fixture["safety_controls"]:
        kind = item["kind"]
        origins = item["origin"]
        delays = {p: {"transport": 0, "compute": item["delay"][p]} for p in PRINCIPALS}
        intents = _intent_rows(item["id"], origins, delays, kind=kind)
        if kind == "critical":
            for intent in intents:
                intent["kind"] = "critical"
        if kind == "short_deadline":
            for intent in intents:
                intent["deadline"] = item["deadline_after_origin"]
        if kind == "revoked":
            for intent in intents:
                if intent["principal"] == item["revoked_principal"]:
                    intent["revoke_at"] = item["revoke_at"]
        if kind == "expired":
            for intent in intents:
                if intent["principal"] == item["expired_principal"]:
                    intent["evidence_expiry"] = item["evidence_expiry_at"]
        rights = "none" if kind == "no_rights" else "equal"
        for policy in POLICIES:
            row = _one(item["id"], intents, policy, "A", rights=rights, kind=kind)
            row.update({"case": item["id"], "policy": policy, "arm": "baseline",
                        "phase": "safety", "kind": kind})
            rows.append(row)

    pairs = {}
    for row in rows:
        if row["phase"] in ("paired", "heldout"):
            pairs.setdefault((row["case"], row["policy"]), {})[row["arm"]] = row["winner"]
    sensitivity = {policy: {"changed": sum(v.get("baseline") != v.get("delay_swapped") for (case, pol), v in pairs.items() if pol == policy),
                            "pairs": sum(pol == policy for (_, pol) in pairs)} for policy in POLICIES}
    return {"schema": "infra-speed-fairness-6347-raw-v1", "window": WINDOW,
            "fixture_id": fixture["schema"], "rows": rows, "delay_swap_sensitivity": sensitivity}


if __name__ == "__main__":
    print(json.dumps(run(json.loads(Path(sys.argv[1]).read_text())), sort_keys=True, separators=(",", ":")))
