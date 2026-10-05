#!/usr/bin/env python3
"""Independent raw-only reconstruction for #8152; does not import candidate.py."""
import hashlib
import json
import math
import sys


TARGET_FP = "TARGET:LEASE_TIMEOUT:EXIT42"
DECOY_FP = "COMPETING:BAD_ROUTE:EXIT42"
NO_FP = "NO_FAILURE"
BAD_FP = "INVALID_AUTH_OR_RELEASE"
REQ = frozenset(("AUTH", "SETUP", "RELEASE"))
REL = (("AUTH", "CORE_A"), ("SETUP", "CORE_A"), ("CORE_A", "CORE_B"), ("AUTH", "RELEASE"))


def classify(events, trial, stream):
    present = frozenset(events)
    if not REQ.issubset(present):
        return BAD_FP
    if "CORE_A" not in present:
        return DECOY_FP if "DECOY" in present else NO_FP
    threshold = 0.05 if "CORE_B" not in present else 0.70 + .10 * ("NOISE_1" not in present) + .10 * ("NOISE_2" not in present)
    msg = (stream + "|" + trial + "|" + ",".join(sorted(present))).encode("utf-8")
    value = int(hashlib.sha256(msg).hexdigest()[:16], 16) / 18446744073709551616
    return TARGET_FP if value < threshold else NO_FP


def binom_prob(n, p, i):
    return math.comb(n, i) * (p ** i) * ((1-p) ** (n-i))


def exact_bounds(k, n, level_tail):
    # Independent implementation: solve the two binomial tail equations by monotone bisection.
    if k == 0:
        low = 0.0
    else:
        a, b = 0.0, 1.0
        for _ in range(70):
            mid = (a+b)/2
            q = sum(binom_prob(n, mid, j) for j in range(k, n+1))
            if q >= level_tail:
                b = mid
            else:
                a = mid
        low = (a+b)/2
    if k == n:
        high = 1.0
    else:
        a, b = 0.0, 1.0
        for _ in range(70):
            mid = (a+b)/2
            q = sum(binom_prob(n, mid, j) for j in range(0, k+1))
            if q >= level_tail:
                a = mid
            else:
                b = mid
        high = (a+b)/2
    return low, high


def rows_for(trace, seeds, namespace):
    return [{"seed": s, "fingerprint": classify(trace, s, namespace)} for s in seeds]


def counts(rows):
    return sum(r.get("fingerprint") == TARGET_FP for r in rows)


def admissible(events):
    e = set(events)
    return REQ <= e and all(right not in e or left in e for left, right in REL)


def reconstruct(proto, strategy):
    method = strategy
    ss = proto["search_seeds"]
    base_ids = ss[:1] if method == "A_SINGLE" else ss
    base_stream = method + ":baseline"
    base_rows = rows_for(proto["base_trace"], base_ids, base_stream)
    base_n = len(base_rows)
    base_k = counts(base_rows)
    current = list(proto["base_trace"])
    decisions = []
    events = proto["candidate_removal_order"]
    for event in events:
        if event not in current:
            continue
        trial_trace = list(current)
        trial_trace.remove(event)
        if event == "CORE_A" and "CORE_B" in trial_trace:
            trial_trace.remove("CORE_B")
        if not admissible(trial_trace):
            decisions.append({"event": event, "status": "REJECT_UNSAFE", "rows": []})
            continue
        stream = method + ":candidate:" + event
        if method == "A_SINGLE":
            measured = rows_for(trial_trace, ss[:1], stream)
            k = counts(measured)
            state = "ACCEPT" if k == 1 else "REJECT"
            row = {"event": event, "status": state, "rows": measured, "n": 1, "target_count": k}
        elif method == "B_FIXED":
            measured = rows_for(trial_trace, ss, stream)
            k = counts(measured)
            alpha = proto["familywise_alpha"] / (2 * len(events))
            lo, _ = exact_bounds(k, len(measured), alpha)
            _, hi0 = exact_bounds(base_k, base_n, alpha)
            delta_low = lo-hi0
            state = "ACCEPT" if delta_low >= -proto["noninferiority_margin"] else "REJECT"
            row = {"event": event, "status": state, "rows": measured, "n": len(measured), "target_count": k, "lower_difference": delta_low}
        else:
            state, measured, k, used = "UNRESOLVED", [], 0, 0
            looks = len(proto["sequential_batches"])
            alpha = proto["familywise_alpha"] / (2 * len(events) * looks)
            for size in proto["sequential_batches"]:
                measured = rows_for(trial_trace, ss[:size], stream)
                k = counts(measured)
                lo, hi = exact_bounds(k, size, alpha)
                blo, bhi = exact_bounds(base_k, base_n, alpha)
                used = size
                if lo-bhi >= -proto["noninferiority_margin"]:
                    state = "ACCEPT"
                    break
                if hi-blo < -proto["noninferiority_margin"]:
                    state = "REJECT"
                    break
            row = {"event": event, "status": state, "rows": measured, "n": used, "target_count": k}
        decisions.append(row)
        if row["status"] == "ACCEPT":
            current = trial_trace
    queries = base_n + sum(d.get("n", 0) for d in decisions)
    return {"method": method, "final_trace": current, "baseline_rows": base_rows, "baseline_target_count": base_k,
            "decisions": decisions, "query_count": queries}


def rejection_checks(proto, raw):
    checks = {}
    original = raw["results"][0]
    forged = json.loads(json.dumps(original))
    forged["final_trace"].remove("AUTH")
    checks["authority_drop"] = not admissible(forged["final_trace"])
    forged2 = json.loads(json.dumps(original))
    forged2["final_trace"].remove("RELEASE")
    checks["release_drop"] = not admissible(forged2["final_trace"])
    checks["same_exit_code_competitor"] = classify(["AUTH", "SETUP", "CORE_B", "DECOY", "RELEASE"], "control", "mutant") == DECOY_FP and DECOY_FP != TARGET_FP
    checks["search_confirmation_overlap"] = not (set(proto["search_seeds"]) & set(proto["confirmation_seeds"]))
    expected_a = reconstruct(proto, "A_SINGLE")
    missing = json.loads(json.dumps(raw["results"][0]))
    missing["baseline_rows"].pop()
    checks["missing_row_rejected"] = missing != expected_a
    zero_imputed = json.loads(json.dumps(raw["results"][0]))
    zero_imputed["baseline_rows"].append({"seed": "missing-as-zero", "fingerprint": None})
    checks["missingness_not_zero_imputed"] = counts(zero_imputed["baseline_rows"]) == counts(original["baseline_rows"])
    return checks


def coverage_grid(n, alpha):
    # Exhaustively checks interval coverage on a declared 0.01 probability grid.
    bounds = [exact_bounds(k, n, alpha) for k in range(n + 1)]
    minimum = 1.0
    for step in range(1, 100):
        p = step / 100
        covered = sum(binom_prob(n, p, k) for k, (lo, hi) in enumerate(bounds) if lo <= p <= hi)
        minimum = min(minimum, covered)
    return minimum


def run(proto_path, raw_path, audit_path):
    with open(proto_path, encoding="utf-8") as f:
        proto = json.load(f)
    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)
    errors = []
    if raw.get("schema") != "8152-a01-raw-v1" or raw.get("allocation") != proto["allocation"]:
        errors.append("raw identity mismatch")
    expected = [reconstruct(proto, name) for name in ("A_SINGLE", "B_FIXED", "C_SEQUENTIAL")]
    if raw.get("results") != expected:
        errors.append("candidate reductions, observations, or query counts differ from independent reconstruction")
    confirm_expected = []
    alpha = proto["familywise_alpha"] / 6
    hs = proto["confirmation_seeds"]
    for result in expected:
        b = rows_for(proto["base_trace"], hs, result["method"] + ":heldout:baseline")
        c = rows_for(result["final_trace"], hs, result["method"] + ":heldout:candidate")
        bk, ck = counts(b), counts(c)
        _, bu = exact_bounds(bk, len(hs), alpha)
        cl, _ = exact_bounds(ck, len(hs), alpha)
        confirm_expected.append({"method": result["method"], "baseline_rows": b, "candidate_rows": c,
                                 "baseline_target_count": bk, "candidate_target_count": ck,
                                 "lower_difference": cl-bu,
                                 "noninferior": cl-bu >= -proto["noninferiority_margin"],
                                 "independent_seed_namespace": True})
    if raw.get("confirmation") != confirm_expected:
        errors.append("held-out confirmation mismatch or seed reuse")
    checks = rejection_checks(proto, raw)
    if not all(checks.values()):
        errors.append("one or more hostile controls not rejected")
    b = next(x for x in expected if x["method"] == "B_FIXED")
    c = next(x for x in expected if x["method"] == "C_SEQUENTIAL")
    saving = b["query_count"] - c["query_count"]
    conf_c = next(x for x in confirm_expected if x["method"] == "C_SEQUENTIAL")
    if not conf_c["noninferior"]:
        errors.append("sequential method missed held-out noninferiority")
    if saving <= 0:
        errors.append("sequential method did not reduce search queries")
    alpha_fixed = proto["familywise_alpha"] / (2 * len(proto["candidate_removal_order"]))
    alpha_seq = proto["familywise_alpha"] / (2 * len(proto["candidate_removal_order"]) * len(proto["sequential_batches"]))
    coverage = {"fixed_min_grid_coverage": coverage_grid(proto["fixed_repetitions"], alpha_fixed),
                "sequential_by_n": {str(n): coverage_grid(n, alpha_seq) for n in proto["sequential_batches"]},
                "grid": "p=0.01..0.99", "sequential_union_bound_alpha_per_candidate": 2 * alpha_seq * len(proto["sequential_batches"])}
    if coverage["fixed_min_grid_coverage"] + 1e-12 < 1 - 2 * alpha_fixed:
        errors.append("fixed interval coverage grid below its exact-tail bound")
    if any(v + 1e-12 < 1 - 2 * alpha_seq for v in coverage["sequential_by_n"].values()):
        errors.append("sequential interval coverage grid below its exact-tail bound")
    out = {"schema": "8152-a01-audit-v1", "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
           "errors": errors, "independent_reconstruction": True, "mutation_checks": checks,
           "fixed_queries": b["query_count"], "sequential_queries": c["query_count"],
           "sequential_query_saving": saving, "sequential_uses_fewer_queries": saving > 0,
           "heldout_noninferiority_by_method": {x["method"]: x["noninferior"] for x in confirm_expected},
           "interval_coverage_grid": coverage,
           "scope": "finite seeded synthetic model only; no live GUI, retained failure, runtime, safety, or general statistical guarantee"}
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(out, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    return out


if __name__ == "__main__":
    result = run(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1)
