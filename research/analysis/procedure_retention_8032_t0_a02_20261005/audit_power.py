"""Independent raw-only auditor; intentionally does not import power_model."""

import hashlib
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MASK = (1 << 64) - 1


class Stream:
    def __init__(self, initial):
        self.word = initial & MASK

    def next_fraction(self):
        self.word = (self.word + 0x9E3779B97F4A7C15) & MASK
        value = self.word
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK
        value ^= value >> 31
        return (value >> 11) * (1.0 / 9007199254740992.0)


def validate_mass(vector):
    return len(vector) == 5 and all(0 <= item <= 1 for item in vector) and abs(sum(vector) - 1) < 1e-12


def derive_alternative(control, target):
    tails = [sum(control[index:]) for index in range(1, 5)]

    def shifted(ratio):
        new_tails = []
        for tail in tails:
            if tail == 0:
                new_tails.append(0.0)
            elif tail == 1:
                new_tails.append(1.0)
            else:
                odds = ratio * tail / (1.0 - tail)
                new_tails.append(odds / (1 + odds))
        vector = [1 - new_tails[0]]
        vector += [new_tails[i - 1] - new_tails[i] for i in range(1, 4)]
        vector.append(new_tails[-1])
        return vector

    def d_value(treatment):
        scores = [0, .25, .5, .75, 1]
        means = [sum(p * s for p, s in zip(v, scores)) for v in (control, treatment)]
        variances = [sum(p * (s - mean) ** 2 for p, s in zip(v, scores)) for v, mean in zip((control, treatment), means)]
        scale = math.sqrt(sum(variances) / 2)
        return (means[1] - means[0]) / scale

    low, high = 1.0, 1e8
    for _ in range(80):
        middle = (low + high) / 2
        if d_value(shifted(middle)) < target:
            low = middle
        else:
            high = middle
    ratio = (low + high) / 2
    treatment = shifted(ratio)
    return ratio, treatment, d_value(treatment)


def categorical_counts(stream, vector, n):
    boundaries = []
    total = 0.0
    for mass in vector:
        total += mass
        boundaries.append(total)
    counts = [0, 0, 0, 0, 0]
    for _ in range(n):
        draw = stream.next_fraction()
        category = 0
        while category < 4 and draw >= boundaries[category]:
            category += 1
        counts[category] += 1
    return counts


def ordinal_wins(left, right):
    return sum(left[k] * (sum(right[:k]) + right[k] / 2) for k in range(5))


def null_variance(left, right):
    size_a, size_b = sum(left), sum(right)
    size = size_a + size_b
    tied = sum((left[k] + right[k]) ** 3 - (left[k] + right[k]) for k in range(5))
    return size_a * size_b / 12 * (size + 1 - tied / (size * (size - 1)))


def interval(count, total):
    z = 1.959963984540054
    rate = count / total
    den = 1 + z * z / total
    mid = (rate + z * z / (2 * total)) / den
    half = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / den
    return [max(0.0, mid - half), min(1.0, mid + half)]


def reconstruct(vector_a, vector_b, size, repetitions, seed, critical):
    stream = Stream(seed)
    rejected = 0
    raw_counts_hash = hashlib.sha256()
    for _ in range(repetitions):
        a = categorical_counts(stream, vector_a, size)
        b = categorical_counts(stream, vector_b, size)
        u_value = ordinal_wins(a, b)
        variance = null_variance(a, b)
        statistic = (u_value - size * size / 2) / math.sqrt(variance) if variance else 0
        rejected += abs(statistic) >= critical
        raw_counts_hash.update(struct.pack("<5Q", *(a[k] + b[k] for k in range(5))))
    return rejected, raw_counts_hash.hexdigest()


def close_vector(left, right, tolerance=1e-12):
    return len(left) == len(right) and all(abs(a - b) <= tolerance for a, b in zip(left, right))


def audit_data(raw, protocol, freeze):
    errors = []
    if raw.get("allocation") != protocol["allocation"]:
        errors.append("allocation_mismatch")
    for filename, expected in freeze["sha256"].items():
        actual = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
        if actual != expected:
            errors.append("source_hash_mismatch:" + filename)
    expected_protocol_hash = hashlib.sha256((ROOT / "protocol.json").read_bytes()).hexdigest()
    if raw.get("protocol_sha256") != expected_protocol_hash:
        errors.append("raw_protocol_hash_mismatch")
    if raw.get("candidate_sha256") != freeze["sha256"].get("run_candidate.py"):
        errors.append("raw_candidate_identity_mismatch")
    if raw.get("power_model_sha256") != freeze["sha256"].get("power_model.py"):
        errors.append("raw_model_identity_mismatch")
    expected_image = "python:3.12-slim local WSLc image " + freeze["wslc"]["image_id"]
    if raw.get("image") != expected_image:
        errors.append("raw_image_identity_mismatch")
    expected_grid = len(protocol["ordinal_scenarios"]) * 2 * len(protocol["simulation"]["sample_sizes_per_arm"])
    if len(raw.get("cells", [])) != expected_grid:
        errors.append("cell_count_mismatch")
    cell_ids = set()
    critical = 2.498
    for scenario_index, scenario in enumerate(protocol["ordinal_scenarios"]):
        baseline = scenario["baseline_pmf"]
        if not validate_mass(baseline):
            errors.append("invalid_protocol_pmf:" + scenario["id"])
            continue
        for effect_index, target_d in enumerate((.35, .50)):
            ratio, shifted, achieved = derive_alternative(baseline, target_d)
            for size in protocol["simulation"]["sample_sizes_per_arm"]:
                seed = protocol["simulation"]["seed_base"] + scenario_index * 1000 + effect_index * 100 + size
                key = (scenario["id"], target_d, size)
                cell_ids.add(key)
                record = next((row for row in raw.get("cells", []) if (row.get("scenario"), row.get("target_d"), row.get("n_per_arm")) == key), None)
                if record is None:
                    errors.append("missing_cell:" + repr(key))
                    continue
                if record.get("seed") != seed or record.get("replicates") != protocol["simulation"]["replicates_per_power_cell"]:
                    errors.append("cell_frozen_parameter_mismatch:" + repr(key))
                    continue
                if not close_vector(record.get("baseline_pmf", []), baseline):
                    errors.append("baseline_distribution_mismatch:" + repr(key))
                    continue
                if not close_vector(record.get("alternative_pmf", []), shifted):
                    errors.append("alternative_distribution_mismatch:" + repr(key))
                    continue
                if abs(record.get("odds_ratio", -1) - ratio) > 1e-10 or abs(record.get("achieved_d", -1) - achieved) > 1e-10:
                    errors.append("effect_calibration_mismatch:" + repr(key))
                    continue
                reject_count, trace_hash = reconstruct(baseline, shifted, size, record["replicates"], seed, critical)
                if reject_count != record.get("rejections"):
                    errors.append("rejection_count_mismatch:" + repr(key))
                if trace_hash != record.get("pooled_category_counts_sha256"):
                    errors.append("raw_trace_digest_mismatch:" + repr(key))
                if abs(record.get("power", -1) - reject_count / record["replicates"]) > 1e-15:
                    errors.append("power_ratio_mismatch:" + repr(key))
                if not close_vector(record.get("wilson95", []), interval(reject_count, record["replicates"])):
                    errors.append("wilson_interval_mismatch:" + repr(key))
                if record.get("grid_gate_at_target") != (interval(reject_count, record["replicates"])[0] >= .80):
                    errors.append("target_gate_mismatch:" + repr(key))
                if record.get("alpha") != protocol["decision"]["alpha_each_two_sided"] or record.get("critical_abs_z") != critical:
                    errors.append("test_threshold_mismatch:" + repr(key))
                if record.get("recruited_per_arm_15pct") != math.ceil(size / .85):
                    errors.append("attrition_rounding_mismatch:" + repr(key))
    null_cfg = protocol["simulation"]["null_control"]
    null_raw = raw.get("null_control") or {}
    null_pmf = protocol["ordinal_scenarios"][0]["baseline_pmf"]
    null_count, null_digest = reconstruct(null_pmf, null_pmf, null_cfg["n_per_arm"], null_cfg["replicates"], null_cfg["seed"], critical)
    if (null_raw.get("rejections") != null_count or null_raw.get("pooled_category_counts_sha256") != null_digest
            or null_raw.get("n_per_arm") != null_cfg["n_per_arm"]
            or null_raw.get("replicates") != null_cfg["replicates"]
            or null_raw.get("seed") != null_cfg["seed"]
            or abs(null_raw.get("power", -1) - null_count / null_cfg["replicates"]) > 1e-15):
        errors.append("null_control_raw_mismatch")
    if null_raw.get("wilson95") is None or not close_vector(null_raw["wilson95"], interval(null_count, null_cfg["replicates"])):
        errors.append("null_control_interval_mismatch")
    return {
        "allocation": protocol["allocation"],
        "cells_reconstructed": len(cell_ids),
        "null_rejections_reconstructed": null_count,
        "audit": "PASS_RAW_RECONSTRUCTION" if not errors else "FAIL_AUDIT",
        "errors": errors,
    }


def main():
    raw = json.loads((ROOT / "candidate_raw.json").read_text(encoding="utf-8"))
    protocol = json.loads((ROOT / "protocol.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    print(json.dumps(audit_data(raw, protocol, freeze), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
