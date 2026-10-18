"""Independent raw-only audit; scoring truth stays in this directory."""
import copy
import json
import math
import random

Z95 = 1.959963984540054


def _expected_rows(truth):
    rows = []
    for pi, profile in enumerate(truth["profiles"]):
        for n in truth["sample_sizes"]:
            for ai, arm in enumerate(truth["arms"]):
                for replicate in range(truth["replicates"]):
                    key = 88100000 + pi * 20000000 + n * 100000 + ai * 10000 + replicate
                    counts = []
                    for pair, mean in enumerate(profile["rates"]):
                        rng = random.Random(key * 10 + pair)
                        if arm["concentration"] is None:
                            probability = mean
                        else:
                            k = arm["concentration"]
                            probability = rng.betavariate(mean * k, (1 - mean) * k)
                        counts.append(rng.binomialvariate(n, probability))
                    rows.append({"row_id": f"r{len(rows):06d}", "profile_id": profile["id"],
                                 "n": n, "arm_id": arm["id"], "successes": counts})
    return rows


def _wilson(successes, trials):
    p = successes / trials
    z2 = Z95 * Z95
    denominator = 1 + z2 / trials
    center = (p + z2 / (2 * trials)) / denominator
    half = Z95 * math.sqrt(p * (1 - p) / trials + z2 / (4 * trials * trials)) / denominator
    return [max(0.0, center - half), min(1.0, center + half)]


def _audit(data, truth, raw):
    errors = []
    expected = _expected_rows(truth)
    if data.get("schema") != "issue8084-a10-observations-v1" or data.get("rows") != expected:
        errors.append("independent_observation_reconstruction")
    if data.get("span_grid") != truth["span_grid"] or data.get("peak_grid") != truth["peak_grid"]:
        errors.append("frozen_gate_grid")
    obs_rows = data.get("rows", [])
    raw_rows = raw.get("rows", [])
    if raw.get("schema") != "issue8084-a10-candidate-v1" or len(raw_rows) != len(expected):
        errors.append("raw_schema_or_cardinality")
    expected_raw = []
    for row in expected:
        rates = [x / row["n"] for x in row["successes"]]
        span = max(rates) - min(rates)
        peak = max(rates)
        mask = 0
        bit = 0
        for minimum_span in truth["span_grid"]:
            for minimum_peak in truth["peak_grid"]:
                if span >= minimum_span and peak >= minimum_peak:
                    mask |= 1 << bit
                bit += 1
        expected_raw.append({"row_id": row["row_id"], "gate_mask": mask})
    if raw_rows != expected_raw:
        errors.append("independent_candidate_reconstruction")

    gate_count = len(truth["span_grid"]) * len(truth["peak_grid"])
    activated_by = {arm["id"]: {profile["id"]: {str(n): [0] * gate_count
                                                for n in truth["sample_sizes"]}
                                for profile in truth["profiles"]}
                    for arm in truth["arms"]}
    for row, rawrow in zip(expected, expected_raw):
        mask = rawrow["gate_mask"]
        counts = activated_by[row["arm_id"]][row["profile_id"]][str(row["n"])]
        for bit in range(gate_count):
            counts[bit] += (mask >> bit) & 1
    per_profile = {}
    qualified = []
    for bit in range(gate_count):
        gate = {"span": truth["span_grid"][bit // len(truth["peak_grid"])],
                "peak": truth["peak_grid"][bit % len(truth["peak_grid"])], "arms": {}}
        for arm in truth["arms"]:
            all_pass = True
            gate["arms"][arm["id"]] = {"concentration": arm["concentration"], "profiles": {}}
            for profile in truth["profiles"]:
                gate["arms"][arm["id"]]["profiles"][profile["id"]] = {}
                for n in truth["sample_sizes"]:
                    activated = activated_by[arm["id"]][profile["id"]][str(n)][bit]
                    interval = _wilson(activated, truth["replicates"])
                    gate["arms"][arm["id"]]["profiles"][profile["id"]][str(n)] = {
                        "activated": activated, "replicates": truth["replicates"],
                        "activation_rate": activated / truth["replicates"], "wilson_95": interval}
                    if profile["class"] == "positive":
                        all_pass &= interval[0] >= 0.80
                    else:
                        all_pass &= interval[1] <= 0.05
            if all_pass:
                qualified.append({"span": gate["span"], "peak": gate["peak"],
                                  "arm_id": arm["id"], "concentration": arm["concentration"]})
        per_profile[f"gate-{bit:02d}"] = gate
    screen = "EXISTS_GATE_IN_FROZEN_GRID_SCOPED" if qualified else "NO_GATE_IN_FROZEN_GRID_MEETS_BOTH_CRITERIA_SCOPED"
    return {"decision": "METHOD_PASS_SCOPED" if not errors else "HOLD_METHOD_GATE",
            "diagnostic_screen": screen, "errors": errors,
            "rows": len(raw_rows), "gate_count": gate_count,
            "qualified_gates": qualified, "gate_results": per_profile,
            "scope": "finite authored overdispersion concentration arms and frozen grid only"}


def audit(data, truth, raw):
    result = _audit(data, truth, raw)
    mutations = []
    cases = [
        ("flipped_decision_bit", lambda d, r: r["rows"][0].__setitem__("gate_mask", r["rows"][0]["gate_mask"] ^ 1)),
        ("duplicate_candidate_row", lambda d, r: r["rows"].append(copy.deepcopy(r["rows"][0]))),
        ("altered_observation_count", lambda d, r: d["rows"][0]["successes"].__setitem__(0, (d["rows"][0]["successes"][0] + 1) % (d["rows"][0]["n"] + 1))),
        ("altered_gate_threshold", lambda d, r: d["span_grid"].__setitem__(0, d["span_grid"][0] + 0.01)),
        ("removed_candidate_row", lambda d, r: r["rows"].pop()),
    ]
    for name, mutate in cases:
        data_mut, raw_mut = copy.deepcopy(data), copy.deepcopy(raw)
        mutate(data_mut, raw_mut)
        rejected = bool(_audit(data_mut, truth, raw_mut)["errors"])
        mutations.append({"mutation": name, "rejected": rejected})
    if not all(item["rejected"] for item in mutations):
        result["errors"].append("mutation_survived")
        result["decision"] = "HOLD_METHOD_GATE"
    result["mutation_controls"] = mutations
    return result


if __name__ == "__main__":
    with open("observed_counts.json", encoding="utf-8") as f:
        observed = json.load(f)
    with open("SCORING.json", encoding="utf-8") as f:
        truth = json.load(f)
    with open("candidate.raw.json", encoding="utf-8") as f:
        raw = json.load(f)
    print(json.dumps(audit(observed, truth, raw), sort_keys=True, separators=(",", ":")))
