#!/usr/bin/env python3
"""Separate reconstruction implementation; does not import candidate code."""
import json, random, statistics, sys


def data(seed, n, salt):
    rng = random.Random(seed * 1009 + salt); rows = []
    for i in range(n):
        truth, stratum = rng.randrange(2), rng.randrange(4)
        rows.append({"id": f"{salt}:{i}", "stratum": stratum, "truth": truth,
                     "baseline": truth if i % 2 == 0 else 1-truth})
    return rows


def correct(rows, exact_ids, covered_strata):
    n = 0
    for item in rows:
        predicted = item["truth"] if item["id"] in exact_ids or item["stratum"] in covered_strata else item["baseline"]
        n += int(predicted == item["truth"])
    return n


def audit(raw):
    errors, gaps, fresh_scores = [], {"FULL": [], "CONTROLLED": []}, {"FULL": [], "CONTROLLED": []}
    if raw.get("schema") != "issue8072-finite-a02-v1" or len(raw.get("arms", [])) != 200: errors.append("shape")
    for run in raw.get("arms", []):
        seed, arm = run.get("seed"), run.get("arm")
        dev, fresh = data(seed, 16, 1), data(seed, 128, 2)
        if arm not in gaps or len(run.get("queries", [])) != 8: errors.append(f"arm:{seed}"); continue
        ids, groups = set(), set()
        for i, q in enumerate(run["queries"]):
            if arm == "FULL":
                target = next((r["id"] for r in dev if correct([r], ids, groups) == 0), None)
                expected = {"kind": "PATCH_ID", "target": target}
            else: expected = {"kind": "TRANSFER_STRATUM", "target": i % 4}
            before = correct(dev, ids, groups); ni, ng = set(ids), set(groups)
            if expected["kind"] == "PATCH_ID" and expected["target"] is not None: ni.add(expected["target"])
            if expected["kind"] == "TRANSFER_STRATUM": ng.add(expected["target"])
            after = correct(dev, ni, ng); failure = i == 6
            expected_feedback = ({"utility_rows": after-before} if arm == "FULL" else
                                 {"accepted_threshold": after-before >= 2})
            accepted = not failure and (after > before if arm == "FULL" else after-before >= 2)
            fields = (q.get("proposal") == expected and q.get("before") == before and
                      q.get("proposed") == after and q.get("hard_failure") == failure and
                      q.get("exact_safety_disclosed") is True and q.get("veto") == failure and
                      q.get("feedback") == expected_feedback and q.get("accepted") == accepted and
                      q.get("fresh_read") is False)
            if not fields: errors.append(f"query:{seed}:{arm}:{i}")
            if accepted: ids, groups = ni, ng
        dc, fc = correct(dev, ids, groups), correct(fresh, ids, groups)
        if (run.get("dev_correct"), run.get("fresh_correct"), run.get("locked_before_fresh"),
            run.get("post_lock_raw_disclosed")) != (dc, fc, True, True): errors.append(f"result:{seed}:{arm}")
        gaps[arm].append(dc/len(dev)-fc/len(fresh)); fresh_scores[arm].append(fc/len(fresh))
    med = {k: statistics.median(v) for k,v in gaps.items()}; means = {k: sum(v)/len(v) for k,v in fresh_scores.items()}
    decision = "PASS_METHOD_SCOPED" if (not errors and med["CONTROLLED"] < med["FULL"] and means["CONTROLLED"] >= means["FULL"]-.05) else "FAIL_METHOD"
    return {"decision": decision, "errors": errors, "median_optimism": med, "mean_fresh_utility": means,
            "seed_count": len(gaps["FULL"]), "scope": "authored synthetic finite mechanism only"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f: raw = json.load(f)
    json.dump(audit(raw), sys.stdout, sort_keys=True, indent=2); print()
