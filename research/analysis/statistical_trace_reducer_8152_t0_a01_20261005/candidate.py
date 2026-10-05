#!/usr/bin/env python3
"""Frozen candidate for the #8152 synthetic statistical reducer study."""
import hashlib
import json
import math
import sys


TARGET = "TARGET:LEASE_TIMEOUT:EXIT42"
COMPETING = "COMPETING:BAD_ROUTE:EXIT42"
NO_FAILURE = "NO_FAILURE"
INVALID = "INVALID_AUTH_OR_RELEASE"
EDGES = (("AUTH", "CORE_A"), ("SETUP", "CORE_A"), ("CORE_A", "CORE_B"), ("AUTH", "RELEASE"))


def run(trace, seed, lane):
    s = set(trace)
    if not {"AUTH", "SETUP", "RELEASE"} <= s:
        return INVALID
    if "CORE_A" not in s:
        return COMPETING if "DECOY" in s else NO_FAILURE
    if "CORE_B" not in s:
        # A rare same-fingerprint transient is deliberately possible after deleting a causal event.
        p = 0.05
    else:
        p = 0.70 + (0.10 if "NOISE_1" not in s else 0.0) + (0.10 if "NOISE_2" not in s else 0.0)
    payload = (lane + "|" + seed + "|" + ",".join(sorted(s))).encode()
    u = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / 2**64
    return TARGET if u < p else NO_FAILURE


def tail_ge(n, k, p):
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))


def tail_le(n, k, p):
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(0, k+1))


def cp_lower(k, n, alpha):
    if k == 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(64):
        mid = (lo + hi) / 2
        if tail_ge(n, k, mid) < alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def cp_upper(k, n, alpha):
    if k == n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(64):
        mid = (lo + hi) / 2
        if tail_le(n, k, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def ci(k, n, alpha):
    return [cp_lower(k, n, alpha), cp_upper(k, n, alpha)]


def eval_rows(trace, seeds, lane):
    rows = [{"seed": seed, "fingerprint": run(trace, seed, lane)} for seed in seeds]
    return rows, sum(row["fingerprint"] == TARGET for row in rows)


def safe(trace):
    s = set(trace)
    return {"AUTH", "SETUP", "RELEASE"} <= s and all(b not in s or a in s for a, b in EDGES)


def reduce(trace0, protocol, method):
    trace = list(trace0)
    seeds = protocol["search_seeds"]
    baseline_seeds = seeds[:1] if method == "A_SINGLE" else seeds
    baseline_rows, baseline_k = eval_rows(trace, baseline_seeds, method + ":baseline")
    baseline_n = len(baseline_seeds)
    decisions = []
    for event in protocol["candidate_removal_order"]:
        if event not in trace:
            continue
        proposed = list(trace)
        proposed.remove(event)
        if event == "CORE_A" and "CORE_B" in proposed:
            proposed.remove("CORE_B")
        if not safe(proposed):
            decisions.append({"event": event, "status": "REJECT_UNSAFE", "rows": []})
            continue
        cand_seeds = seeds
        lane = method + ":candidate:" + event
        if method == "A_SINGLE":
            used = cand_seeds[:1]
            rows, k = eval_rows(proposed, used, lane)
            accept = rows[0]["fingerprint"] == TARGET
            status = "ACCEPT" if accept else "REJECT"
            decisions.append({"event": event, "status": status, "rows": rows, "n": 1, "target_count": k})
        elif method == "B_FIXED":
            rows, k = eval_rows(proposed, cand_seeds, lane)
            alpha = protocol["familywise_alpha"] / (2 * len(protocol["candidate_removal_order"]))
            lower = cp_lower(k, len(rows), alpha) - cp_upper(baseline_k, baseline_n, alpha)
            accept = lower >= -protocol["noninferiority_margin"]
            decisions.append({"event": event, "status": "ACCEPT" if accept else "REJECT", "rows": rows, "n": len(rows), "target_count": k, "lower_difference": lower})
        else:
            status, rows, k, used_n = "UNRESOLVED", [], 0, 0
            looks = len(protocol["sequential_batches"])
            alpha = protocol["familywise_alpha"] / (2 * len(protocol["candidate_removal_order"]) * looks)
            for n in protocol["sequential_batches"]:
                used = cand_seeds[:n]
                rows, k = eval_rows(proposed, used, lane)
                lower = cp_lower(k, n, alpha) - cp_upper(baseline_k, baseline_n, alpha)
                upper = cp_upper(k, n, alpha) - cp_lower(baseline_k, baseline_n, alpha)
                used_n = n
                if lower >= -protocol["noninferiority_margin"]:
                    status = "ACCEPT"
                    break
                if upper < -protocol["noninferiority_margin"]:
                    status = "REJECT"
                    break
            decisions.append({"event": event, "status": status, "rows": rows, "n": used_n, "target_count": k})
        if decisions[-1]["status"] == "ACCEPT":
            trace = proposed
    return {"method": method, "final_trace": trace, "baseline_rows": baseline_rows, "baseline_target_count": baseline_k, "decisions": decisions,
            "query_count": baseline_n + sum(d.get("n", 0) for d in decisions)}


def main(protocol_path, output_path):
    with open(protocol_path, encoding="utf-8") as f:
        protocol = json.load(f)
    results = [reduce(protocol["base_trace"], protocol, m) for m in ("A_SINGLE", "B_FIXED", "C_SEQUENTIAL")]
    confirm = []
    seeds = protocol["confirmation_seeds"]
    alpha = protocol["familywise_alpha"] / 6
    for item in results:
        base_rows, base_k = eval_rows(protocol["base_trace"], seeds, item["method"] + ":heldout:baseline")
        cand_rows, cand_k = eval_rows(item["final_trace"], seeds, item["method"] + ":heldout:candidate")
        diff_lower = cp_lower(cand_k, len(seeds), alpha) - cp_upper(base_k, len(seeds), alpha)
        confirm.append({"method": item["method"], "baseline_rows": base_rows, "candidate_rows": cand_rows,
                        "baseline_target_count": base_k, "candidate_target_count": cand_k, "lower_difference": diff_lower,
                        "noninferior": diff_lower >= -protocol["noninferiority_margin"], "independent_seed_namespace": True})
    out = {"schema": "8152-a01-raw-v1", "allocation": protocol["allocation"], "results": results, "confirmation": confirm}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
