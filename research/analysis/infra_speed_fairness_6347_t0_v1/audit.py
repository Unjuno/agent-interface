"""Independent reconstruction of retained scheduler raw output; no candidate imports."""
import copy
import json
import sys
from pathlib import Path


AGENTS = ("A", "B")
RULES = ("frfs", "arrival_fifo", "batch_rotate")
DELTA = 5


def _make(case, origins, delays, sends=None, switch=False):
    sends = sends or {}
    agents = []
    for who in AGENTS:
        source = delays[AGENTS[1 - AGENTS.index(who)]] if switch else delays[who]
        arrival = origins[who] + sends.get(who, 0) + source.get("transport", 0)
        ready = arrival + source.get("compute", 0)
        agents.append({
            "id": f"{case}-{who}", "principal": who, "origin": origins[who],
            "arrival": arrival, "ready": ready, "grant": "active",
            "evidence_expiry": 10000, "revoke_at": None, "deadline": 10000,
            "completion_cost": 1, "resource": "focus", "eligible": True, "kind": "normal",
        })
    return agents


def _decision(agents, rule, pointer, rights="equal", kind="normal"):
    if rights != "equal":
        return {"winner": None, "status": "HOLD_NO_TIE_RIGHTS", "admission": None,
                "completion": None, "reason": "no declared decision right", "pointer_after": pointer}
    collects = rule == "batch_rotate" and kind not in {"critical", "short_deadline", "disjoint"}
    if kind == "short_deadline":
        collects = False
    by_ready = sorted(agents, key=lambda a: (a["ready"], a["id"]))
    if collects:
        at = by_ready[0]["ready"] + DELTA
        contenders = [a for a in by_ready if a["ready"] <= at]
        chosen = min(contenders, key=lambda a: (a["principal"] != pointer, a["id"]))
    elif rule == "arrival_fifo":
        chosen = min(agents, key=lambda a: (a["arrival"], a["id"]))
        at = chosen["ready"]
    else:
        chosen = by_ready[0]
        at = chosen["ready"]

    if chosen["kind"] == "critical":
        at = chosen["ready"]
    if chosen["revoke_at"] is not None and at >= chosen["revoke_at"]:
        return {"winner": None, "status": "REFUSE_REVOKED", "admission": at,
                "completion": None, "reason": "grant revoked before admission", "pointer_after": pointer}
    if at >= chosen["evidence_expiry"]:
        return {"winner": None, "status": "REFUSE_STALE", "admission": at,
                "completion": None, "reason": "evidence expired before admission", "pointer_after": pointer}
    done = at + chosen["completion_cost"]
    if done >= chosen["deadline"]:
        return {"winner": None, "status": "REFUSE_DEADLINE", "admission": at,
                "completion": done, "reason": "completion not strictly before deadline", "pointer_after": pointer}
    if kind == "disjoint":
        passed = [a["principal"] for a in agents if a["grant"] == "active"
                  and a["ready"] < a["evidence_expiry"]
                  and a["ready"] + a["completion_cost"] < a["deadline"]]
        return {"winner": passed, "status": "ADMITTED_DISJOINT", "admission": at,
                "completion": done, "reason": "independent resources", "pointer_after": pointer}
    next_pointer = ("B" if chosen["principal"] == "A" else "A") if collects else pointer
    return {"winner": chosen["principal"], "status": "ADMITTED", "admission": at,
            "completion": done, "reason": "eligible at admission", "pointer_after": next_pointer}


def _tag(base, case, rule, arm, phase, **extra):
    base.update({"case": case, "policy": rule, "arm": arm, "phase": phase})
    base.update(extra)
    return base


def reconstruct(fixture):
    expected = []
    for case in fixture["paired_delay_swap"]:
        for switch, arm in ((False, "baseline"), (True, "delay_swapped")):
            sources = {p: {"transport": case["transport"][p], "compute": case["compute"][p]} for p in AGENTS}
            group = _make(case["id"], {p: case["origin"] for p in AGENTS}, sources, switch=switch)
            for agent in group:
                p = agent["principal"]
                agent["deadline"] = case["deadline"]
                agent["completion_cost"] = case["completion_cost"][p]
                agent["evidence_expiry"] = case["evidence_expiry"][p]
            for rule in RULES:
                expected.append(_tag(_decision(group, rule, "A"), case["id"], rule, arm, "paired"))

    for rule in RULES:
        for switch, arm in ((False, "baseline"), (True, "delay_swapped")):
            pointer = "A"
            for case in fixture["heldout_opportunities"]:
                delays = {p: {"transport": 0, "compute": case["delay"][p]} for p in AGENTS}
                agents = _make(case["id"], case["origin"], delays, switch=switch)
                result = _tag(_decision(agents, rule, pointer), case["id"], rule, arm, "heldout")
                pointer = result["pointer_after"]
                expected.append(result)

    for case in fixture["boundary_controls"]:
        repeats = case.get("repetitions", 1)
        delays = {p: {"transport": 0, "compute": case.get("delay", {}).get(p, 0)} for p in AGENTS}
        for n in range(repeats):
            for rule in RULES:
                agents = _make(f"{case['id']}-{n}", case["origin"], delays, case.get("send_offset"))
                result = _decision(agents, rule, "A" if n % 2 == 0 else "B")
                expected.append(_tag(result, case["id"], rule, "baseline", "boundary", repeat=n))

    for case in fixture["safety_controls"]:
        kind = case["kind"]
        delays = {p: {"transport": 0, "compute": case["delay"][p]} for p in AGENTS}
        agents = _make(case["id"], case["origin"], delays)
        for agent in agents:
            agent["kind"] = kind
            if kind == "short_deadline":
                agent["deadline"] = case["deadline_after_origin"]
            if kind == "revoked" and agent["principal"] == case["revoked_principal"]:
                agent["revoke_at"] = case["revoke_at"]
            if kind == "expired" and agent["principal"] == case["expired_principal"]:
                agent["evidence_expiry"] = case["evidence_expiry_at"]
        rights = "none" if kind == "no_rights" else "equal"
        for rule in RULES:
            result = _decision(agents, rule, "A", rights=rights, kind=kind)
            expected.append(_tag(result, case["id"], rule, "baseline", "safety", kind=kind))

    arms = {}
    for row in expected:
        if row["phase"] in ("paired", "heldout"):
            arms.setdefault((row["case"], row["policy"]), {})[row["arm"]] = row["winner"]
    sensitivity = {rule: {"changed": sum(pair.get("baseline") != pair.get("delay_swapped")
                                           for (case, policy), pair in arms.items() if policy == rule),
                          "pairs": sum(policy == rule for (_, policy) in arms)} for rule in RULES}
    return {"schema": "infra-speed-fairness-6347-raw-v1", "window": DELTA,
            "fixture_id": fixture["schema"], "rows": expected,
            "delay_swap_sensitivity": sensitivity}


def audit(fixture, observed):
    expected = reconstruct(fixture)
    structural = observed == expected
    rows = expected["rows"]
    mutations = []
    variants = []
    changed = copy.deepcopy(expected)
    changed["rows"][0]["winner"] = "forged"
    variants.append(changed)
    changed = copy.deepcopy(expected)
    revoked = next(i for i, r in enumerate(changed["rows"]) if r.get("kind") == "revoked" and r["policy"] == "batch_rotate")
    changed["rows"][revoked]["status"] = "ADMITTED"
    variants.append(changed)
    changed = copy.deepcopy(expected)
    no_right = next(i for i, r in enumerate(changed["rows"]) if r.get("kind") == "no_rights")
    changed["rows"][no_right]["winner"] = "A"
    changed["rows"][no_right]["status"] = "ADMITTED"
    variants.append(changed)
    changed = copy.deepcopy(expected)
    changed["delay_swap_sensitivity"]["batch_rotate"]["changed"] += 1
    variants.append(changed)
    for variant in variants:
        mutations.append(observed != variant)
    return {"schema": "infra-speed-fairness-6347-audit-v1", "pass": structural,
            "reconstructed_rows": len(rows), "row_match": structural,
            "mutation_rejections": mutations, "all_mutations_rejected": all(mutations),
            "observed_sensitivity": observed.get("delay_swap_sensitivity"),
            "independent_sensitivity": expected["delay_swap_sensitivity"],
            "scope": "synthetic finite scheduler traces only"}


if __name__ == "__main__":
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = json.loads(Path(sys.argv[2]).read_text())
    print(json.dumps(audit(fixture, raw), sort_keys=True, separators=(",", ":")))
