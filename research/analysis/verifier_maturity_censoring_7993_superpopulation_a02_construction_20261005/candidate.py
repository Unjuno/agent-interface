"""Candidate consumes only checkpoint-visible outcomes and declared design."""


def evaluate(candidate_input):
    contract = candidate_input["contract"]
    rows = candidate_input["rows"]
    if contract.get("known_propensities") is not True or contract.get("conditional_independence") is not True:
        return {"status": "UNKNOWN", "reason": "assumption_contract_missing"}
    strata = set(contract["strata"])
    propensities = {x: {r["pi"] for r in rows if r["x"] == x} for x in strata}
    if any(not propensities[x] or len(propensities[x]) != 1 or
           not 0 < next(iter(propensities[x])) <= 1 for x in strata):
        return {"status": "UNKNOWN", "reason": "positivity_or_propensity_failure"}
    by_cohort = {}
    for row in rows:
        c = row["cohort"]
        acc = by_cohort.setdefault(c, {"n": 0, "observed": 0, "errors": 0, "ht_sum": 0.0})
        acc["n"] += 1
        if row["observed"]:
            if row["label"] not in (0, 1):
                return {"status": "UNKNOWN", "reason": "observed_label_missing_or_invalid"}
            acc["observed"] += 1
            acc["errors"] += row["label"]
            acc["ht_sum"] += row["label"] / row["pi"]
        elif row["label"] is not None:
            return {"status": "UNKNOWN", "reason": "unobserved_label_leak"}
    cc = []
    ht = []
    for c in sorted(by_cohort):
        row = by_cohort[c]
        if row["n"] == 0 or row["observed"] == 0:
            return {"status": "UNKNOWN", "reason": "empty_cohort_or_complete_case"}
        cc.append(row["errors"] / row["observed"])
        ht.append(row["ht_sum"] / row["n"])
    return {"status": "ASSUMPTION_CONDITIONAL", "cohorts": len(by_cohort),
            "complete_case_mean": sum(cc) / len(cc), "ht_mean": sum(ht) / len(ht),
            "cohort_cc": cc, "cohort_ht": ht}
