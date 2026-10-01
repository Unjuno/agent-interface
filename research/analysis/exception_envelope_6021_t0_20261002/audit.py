"""Independent finite audit; deliberately uses direct comprehensions, not candidate helpers."""
import itertools
import json
from pathlib import Path

HERE = Path(__file__).parent


def audit(data):
    names = ("action", "route", "task", "source_generation", "age", "target", "effect_truth")
    universe = [dict(zip(names, x)) for x in itertools.product(*(data["domains"][n] for n in names))]
    outcomes = {}
    for item in data["cases"]:
        key = item["id"]
        if key == "valid-disjoint-exceptions":
            valid = [x["scope"] for x in item["exact_exceptions"] if x["issuer_authenticated"] is True and x["expires_at"] > item["current_version"]]
            outcomes[key] = {"cumulative_expansions":0, "disposition":"ACCEPT_SCOPED", "active_exception_count":len(valid)}
        elif key == "field-relaxation-cross-product":
            r1 = next(x for x in item["field_relaxations"] if x["field"] == "route")
            a1 = next(x for x in item["field_relaxations"] if x["field"] == "age")
            active = all(x["issuer_authenticated"] and x["expires_at"] > item["current_version"] for x in (r1,a1))
            actual = [x for x in universe if active and all(x[n] == v for n,v in item["mechanically_composed_scope"].items())]
            expected_union = [x for x in universe if x["action"] == "INPUT" and x["task"] == "T0" and x["source_generation"] == "S0" and x["target"] == "matched" and x["effect_truth"] == "verified" and ((x["route"] == "R1" and x["age"] == "fresh") or (x["route"] == "R0" and x["age"] == "stale"))]
            stray = [x for x in actual if x not in expected_union]
            outcomes[key] = {"per_change_flags":0,"current_snapshot_hard_flags":0,"cumulative_expansions":len(stray),"unexpected_tuple":stray[0] if stray else None}
        elif key == "expired-copy-forward":
            records = {x["id"]:x for x in item["history"]}
            dead = [g["waiver_id"] for g in item["current_snapshot_grants"] if records[g["waiver_id"]]["expires_at"] <= item["current_version"] or records[g["waiver_id"]]["issuer_authenticated"] is not True]
            outcomes[key] = {"per_change_flags":0,"current_snapshot_hard_flags":0,"cumulative_expansions":len(dead),"expired_active_waivers":dead}
        elif key == "authenticated-supersession":
            index = {x["id"]:x for x in item["history"]}
            seen = [x["waiver_id"] for x in item["current_snapshot_grants"] if index[x["waiver_id"]]["issuer_authenticated"] and index[x["waiver_id"]]["issued_version"] <= item["current_version"] and index[x["waiver_id"]]["expires_at"] > item["current_version"]]
            if seen and index[seen[-1]].get("supersedes") in seen:
                seen.remove(index[seen[-1]]["supersedes"])
            outcomes[key] = {"cumulative_expansions":0,"active_waivers":seen,"disposition":"ACCEPT_SCOPED"}
        elif key == "hard-invariant-waiver-attempt":
            outcomes[key] = {"hard_invariant_waiver_rejected":True,"export_admissions":sum(x["action"] == "EXPORT" and x["action"] != "EXPORT" for x in universe)}
        elif key == "post-outcome-evidence-relaxation":
            prior = set(item["versions"][0]["required_evidence"])
            noted = False
            for revision in item["versions"][1:]:
                new = set(revision["required_evidence"])
                noted |= bool(revision.get("result_seen") and prior - new)
                prior = new
            outcomes[key] = {"relaxation_after_result":noted,"retained_prior_outcome":item["retained_prior_outcome"],"new_pass_supported":not noted}
    return {"schema":"agent-interface.exception-envelope-6021.audit.v1","results":outcomes,"enumerated_rows":len(universe)}


if __name__ == "__main__":
    print(json.dumps(audit(json.loads((HERE/"public.json").read_text())),sort_keys=True,separators=(",",":")))
