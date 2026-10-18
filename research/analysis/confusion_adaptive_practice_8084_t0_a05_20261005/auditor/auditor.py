#!/usr/bin/env python3
"""Independent raw-only reconstruction using a separate scorer implementation."""
import copy
import json
import random


def _audit(observations, truth, raw):
    errors = []
    observation_rows = observations.get("rows", [])
    raw_rows = raw.get("rows", [])
    obs = {r["row_id"]: r for r in observation_rows}
    got = {r.get("row_id"): r for r in raw_rows}
    expected_total = len(truth["strata"]) * len(truth["sample_sizes"]) * truth["replicates"]
    if raw.get("schema") != "issue8084-a05-candidate-v1" or len(observation_rows) != expected_total or len(raw_rows) != expected_total or len(obs) != expected_total or len(got) != expected_total or set(obs) != set(got):
        errors.append("row_manifest")
    summary = {}
    ordered = observations.get("rows", [])
    expected_rows = []
    for si, stratum in enumerate(truth["strata"]):
        for ni, n in enumerate(truth["sample_sizes"]):
            for rep in range(truth["replicates"]):
                key = 828405 + si * 100000 + n * 1000 + rep
                counts = []
                for pair, probability in enumerate(stratum["rates"]):
                    rng = random.Random(key * 10 + pair)
                    counts.append(sum(1 for _ in range(n) if rng.random() < probability))
                expected_rows.append({"row_id": f"r{len(expected_rows):04d}", "n": n, "successes": counts})
    if ordered != expected_rows:
        errors.append("independent_generation_reconstruction")
    for si, stratum in enumerate(truth["strata"]):
        summary[stratum["id"]] = {}
        for n in truth["sample_sizes"]:
            subset = [r for r in observations["rows"] if r["row_id"] in got and r["n"] == n and
                      int(r["row_id"][1:]) // (truth["replicates"] * len(truth["sample_sizes"])) == si]
            # Independently map rows to the authored stratum/sample block by frozen row order.
            eligible_count = false_count = miss_count = top_correct = top_total = 0
            for o in subset:
                observed = got.get(o["row_id"], {})
                if len(o["successes"]) != 3 or any(type(x) is not int or x < 0 or x > n for x in o["successes"]):
                    errors.append("count_bounds:" + o["row_id"]); continue
                rates = [x / n for x in o["successes"]]
                top_i = max(range(3), key=lambda i: (rates[i], -i))
                gate = max(rates) - min(rates) >= truth["minimum_span"] and max(rates) >= truth["minimum_peak"]
                expected = {"row_id": o["row_id"], "eligible": gate,
                            "top_pair": truth["pair_order"][top_i], "rates": rates}
                if observed != expected:
                    errors.append("reconstruct:" + o["row_id"])
                # Truth status is recovered from the contiguous block identity, not candidate output.
                stratum_index = int(o["row_id"][1:]) // (truth["replicates"] * len(truth["sample_sizes"]))
                latent = truth["strata"][stratum_index]
                if o["n"] == n:
                    eligible_count += int(gate)
                    if not latent["eligible"]: false_count += int(gate)
                    if latent["eligible"]: miss_count += int(not gate)
                    if gate and latent["eligible"]:
                        top_total += 1
                        top_correct += int(truth["pair_order"][top_i] == truth["pair_order"][latent["expected_top_pair"]])
            summary[stratum["id"]][str(n)] = {"replicates": len(subset), "eligible": eligible_count,
                "activation_rate": eligible_count / max(1, len(subset)),
                "false_activation_rate": false_count / max(1, len(subset)) if not stratum["eligible"] else None,
                "miss_rate": miss_count / max(1, len(subset)) if stratum["eligible"] else None,
                "top_pair_accuracy_when_eligible": top_correct / max(1, top_total), "top_pair_denominator": top_total}
    rates_by = {s["id"]: s for s in truth["strata"]}
    strong_ids = (truth["strata"][0]["id"], truth["strata"][1]["id"])
    null_ids = (truth["strata"][2]["id"], truth["strata"][3]["id"])
    support = True
    for n in (20, 100):
        for sid in strong_ids:
            support &= summary[sid][str(n)]["activation_rate"] >= 0.80
            support &= summary[sid][str(n)]["top_pair_accuracy_when_eligible"] >= 0.90
        for sid in null_ids:
            support &= summary[sid][str(n)]["false_activation_rate"] <= 0.05
    return {"decision": "METHOD_PASS_SCOPED" if not errors else "HOLD_METHOD_GATE",
            "diagnostic_screen": "SUPPORTS_N_GE_20_FOR_CLEAR_STRATA" if support else "DOES_NOT_SUPPORT_CURRENT_GATE_AS_RELIABLE_AT_N_GE_20",
            "errors": errors, "rows": len(got), "summary": summary,
            "scope": "finite authored stationary-binomial diagnostics only; no participant or GUI inference"}


def audit(observations, truth, raw):
    result = _audit(observations, truth, raw)
    mutations = []
    mutations_to_try = [
        ("flipped_gate", lambda d, r: r["rows"][0].__setitem__("eligible", not r["rows"][0]["eligible"])),
        ("altered_count", lambda d, r: d["rows"][0]["successes"].__setitem__(0, (d["rows"][0]["successes"][0] + 1) % (d["rows"][0]["n"] + 1))),
        ("altered_pair", lambda d, r: r["rows"][0].__setitem__("top_pair", "ZZ")),
        ("duplicate_row", lambda d, r: r["rows"].append(copy.deepcopy(r["rows"][0]))),
        ("altered_denominator", lambda d, r: d["rows"][0].__setitem__("n", d["rows"][0]["n"] + 1)),
    ]
    for name, mutate in mutations_to_try:
        d, r = copy.deepcopy(observations), copy.deepcopy(raw)
        mutate(d, r)
        detected = bool(_audit(d, truth, r)["errors"])
        mutations.append({"mutation": name, "rejected": detected})
    if not all(x["rejected"] for x in mutations):
        result["errors"].append("mutation_survived")
        result["decision"] = "HOLD_METHOD_GATE"
    result["mutation_controls"] = mutations
    return result


if __name__ == "__main__":
    with open("observed_counts.json", encoding="utf-8") as f: observations = json.load(f)
    with open("SCORING.json", encoding="utf-8") as f: truth = json.load(f)
    with open("candidate.raw.json", encoding="utf-8") as f: raw = json.load(f)
    print(json.dumps(audit(observations, truth, raw), sort_keys=True, separators=(",", ":")))
