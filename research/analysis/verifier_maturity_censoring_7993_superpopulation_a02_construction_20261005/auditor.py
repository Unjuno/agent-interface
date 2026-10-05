"""Raw-only auditor independently joins candidate and oracle row streams."""
import hashlib
import json
import math


def oracle_digest(oracle_input):
    canonical = json.dumps(oracle_input, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def audit(candidate_input, oracle_input, output, expected_oracle_sha256):
    errors = []
    if oracle_digest(oracle_input) != expected_oracle_sha256:
        errors.append("oracle_hash_mismatch")
    crows = candidate_input.get("rows", [])
    orows = oracle_input.get("rows", [])
    ckeys = [(r.get("cohort"), r.get("row")) for r in crows]
    okeys = [(r.get("cohort"), r.get("row")) for r in orows]
    if len(set(ckeys)) != len(ckeys) or len(set(okeys)) != len(okeys):
        errors.append("duplicate_assignment")
    if set(ckeys) != set(okeys):
        errors.append("assignment_denominator_mismatch")
    c_by_key = {(r.get("cohort"), r.get("row")): r for r in crows}
    o_by_key = {(r.get("cohort"), r.get("row")): r for r in orows}
    n_cohorts = candidate_input.get("cohorts", 0)
    n = candidate_input.get("n_per_cohort", 0)
    if len(crows) != n_cohorts * n:
        errors.append("candidate_denominator_wrong")
    for key in set(ckeys) & set(okeys):
        c, o = c_by_key[key], o_by_key[key]
        if c.get("x") != o.get("x") or c.get("pi") != o.get("pi"):
            errors.append("stratum_or_propensity_mismatch")
        if c.get("observed") != o.get("observed"):
            errors.append("followup_assignment_mismatch")
        if c.get("observed") and c.get("label") != o.get("y"):
            errors.append("observed_label_mismatch")
        if not c.get("observed") and c.get("label") is not None:
            errors.append("hidden_label_leaked")
    if output.get("status") == "ASSUMPTION_CONDITIONAL" and not errors:
        cohort_cc, cohort_ht = [], []
        for cohort in range(n_cohorts):
            rs = [c_by_key[(cohort, i)] for i in range(n)]
            os = [o_by_key[(cohort, i)] for i in range(n)]
            seen = sum(r["observed"] for r in rs)
            if not seen:
                errors.append("empty_observed_cohort")
                continue
            cohort_cc.append(sum(o["y"] for o in os if o["observed"]) / seen)
            cohort_ht.append(sum(o["y"] / r["pi"] for r, o in zip(rs, os) if o["observed"]) / n)
        if len(cohort_cc) != n_cohorts or len(output.get("cohort_cc", [])) != n_cohorts:
            errors.append("checkpoint_count_mismatch")
        elif any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-12)
                 for a, b in zip(cohort_cc, output["cohort_cc"])):
            errors.append("complete_case_reconstruction_mismatch")
        elif any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-12)
                 for a, b in zip(cohort_ht, output.get("cohort_ht", []))):
            errors.append("ht_reconstruction_mismatch")
        elif not math.isclose(sum(cohort_ht) / n_cohorts, output.get("ht_mean", float("nan")),
                              rel_tol=0, abs_tol=1e-12):
            errors.append("ht_aggregate_mismatch")
    return {"ok": not errors, "errors": errors, "assigned": len(crows),
            "cohorts_reconstructed": n_cohorts if not errors else 0}
