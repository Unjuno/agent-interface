#!/usr/bin/env python3
"""Audit-only reconstruction of immutable Issue #5198 allocation-01 raw."""
import copy
import hashlib
import json
import math
import random
import sys
from pathlib import Path

AUDIT_ALLOCATION = "typed-mode-4844-calibration-v5-posthoc-audit-20260928-01"
SOURCE_ALLOCATION = "typed-mode-4844-risk-calibration-20260928-01"
EXPECTED_RAW_SHA256 = "b55b8d9e58497c47ef5a2152d1236d27fdb6918a018cbeebf2a75f0b5f709470"
EXPECTED_RAW_BYTES = 2794446
SEEDS = {"train": 67010231, "calibration": 67010232, "test": 67010233}
TRAIN_ROWS = 2000
FULL_BLOCK_ROWS = 960
MODE_TO_LABEL = (0, 0, 1, 2, 2)
MODE_CUES = ((0,0,0,0,0,0),(1,1,1,1,1,1),(0,1,0,1,0,1),(1,0,1,0,1,0),(0,0,1,1,0,1))
BLOCK_SEQUENCE = ("COMPLETE", "SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT", "NUISANCE_SHIFT")
PRIMARY_BLOCKS = ("SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT")
TARGET_COVERAGE = 0.65


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def visible_cues(generator, latent, condition):
    cue_state = list(MODE_CUES[latent])
    if condition == "COMPOSITION_HOLDOUT":
        cue_state[0] = 1 - cue_state[0]
        cue_state[5] = 1 - cue_state[5]
    elif condition == "NUISANCE_SHIFT":
        cue_state[3] = 1 - cue_state[3]
    for position in range(6):
        if generator.random() < 0.08:
            cue_state[position] = 1 - cue_state[position]
    shown = [True, True, True, True, True, True]
    if condition == "SINGLE_MISSING":
        shown[1] = False
    elif condition == "MULTI_MISSING":
        shown[1] = shown[4] = False
    if condition != "COMPLETE":
        for position in range(6):
            if generator.random() < 0.20:
                shown[position] = False
    return tuple(cue_state[i] if shown[i] else -1 for i in range(6))


def estimate(samples, labels, cardinality):
    counts = [0 for _ in range(cardinality)]
    yes = [[0 for _ in range(6)] for _ in range(cardinality)]
    observed = [[0 for _ in range(6)] for _ in range(cardinality)]
    for vector, category in zip(samples, labels):
        counts[category] += 1
        for feature, value in enumerate(vector):
            if value >= 0:
                observed[category][feature] += 1
                yes[category][feature] += value
    return counts, yes, observed


def probabilities(vector, parameters):
    counts, yes, observed = parameters
    mass = []
    denominator = sum(counts) + len(counts)
    for category, count in enumerate(counts):
        score = math.log((count + 1.0) / denominator)
        for feature, value in enumerate(vector):
            if value < 0:
                continue
            p_one = (yes[category][feature] + 1.0) / (observed[category][feature] + 2.0)
            score += math.log(p_one if value == 1 else 1.0 - p_one)
        mass.append(score)
    top = max(mass)
    weights = [math.exp(value - top) for value in mass]
    normalizer = sum(weights)
    return [value / normalizer for value in weights]


def predict_pair(vector, model_disposition, model_mode):
    p_direct = probabilities(vector, model_disposition)
    p_mode = probabilities(vector, model_mode)
    direct_index = min(range(3), key=lambda i: (-p_direct[i], i))
    p_typed = [sum(p_mode[j] for j in range(5) if MODE_TO_LABEL[j] == i) for i in range(3)]
    typed_index = min(range(3), key=lambda i: (-p_typed[i], i))
    return direct_index, p_direct[direct_index], typed_index, p_typed[typed_index]


def threshold_at_coverage(confidences):
    possible = sorted(set(confidences))
    possible.append(math.nextafter(possible[-1], math.inf))
    ranked = []
    for cutoff in possible:
        realized = sum(value >= cutoff for value in confidences) / len(confidences)
        ranked.append((abs(realized - TARGET_COVERAGE), -realized, cutoff, realized))
    best = min(ranked)
    return best[2], best[3]


def scored_rows(seed, count_per_block, model_direct, model_typed, thresholds):
    rng = random.Random(seed)
    output = []
    for block_name in BLOCK_SEQUENCE:
        for position in range(count_per_block):
            mode = position % 5
            cues = visible_cues(rng, mode, block_name)
            truth = MODE_TO_LABEL[mode]
            direct_class, direct_conf, typed_class, typed_conf = predict_pair(cues, model_direct, model_typed)
            emitted_d = direct_class if direct_conf >= thresholds["direct"] else None
            emitted_t = typed_class if typed_conf >= thresholds["typed"] else None
            output.append({"block": block_name, "mode": mode, "truth": truth, "x": cues,
                           "direct_class": direct_class, "direct_confidence": direct_conf,
                           "typed_class": typed_class, "typed_confidence": typed_conf,
                           "direct_emit": emitted_d, "typed_emit": emitted_t,
                           "direct_wrong": emitted_d is not None and emitted_d != truth,
                           "typed_wrong": emitted_t is not None and emitted_t != truth,
                           "direct_covered": emitted_d is not None, "typed_covered": emitted_t is not None})
    return output


def block_metrics(rows):
    summaries = {}
    for block_name in BLOCK_SEQUENCE:
        group = [item for item in rows if item["block"] == block_name]
        size = len(group)
        summaries[block_name] = {
            "n": size,
            "direct_wrong": sum(item["direct_wrong"] for item in group),
            "typed_wrong": sum(item["typed_wrong"] for item in group),
            "direct_coverage": sum(item["direct_covered"] for item in group) / size,
            "typed_coverage": sum(item["typed_covered"] for item in group) / size,
        }
    return summaries


def decision_controls(model_direct, model_typed, thresholds):
    prototype_results = []
    for mode_id, canonical in enumerate(MODE_CUES):
        d, dc, t, tc = predict_pair(canonical, model_direct, model_typed)
        prototype_results.append({"mode": mode_id, "expected": MODE_TO_LABEL[mode_id],
                                  "direct": d if dc >= thresholds["direct"] else None,
                                  "typed": t if tc >= thresholds["typed"] else None})
    fail_closed_results = []
    sentinels = (("unknown", (-1,) * 6), ("contradictory", (0,0,0,1,0,1)))
    for name, cues in sentinels:
        d, dc, t, tc = predict_pair(cues, model_direct, model_typed)
        fail_closed_results.append({"kind": name, "direct": d if dc >= thresholds["direct"] else None,
                                    "typed": t if tc >= thresholds["typed"] else None})
    return {"prototypes": prototype_results, "fail_closed": fail_closed_results}


def regenerate(seed_bundle=SEEDS, per_block=FULL_BLOCK_ROWS):
    generator = random.Random(seed_bundle["train"])
    train = []
    for index in range(TRAIN_ROWS):
        label = index % 5
        train.append({"mode": label, "x": visible_cues(generator, label, "TRAIN")})
    vectors = [record["x"] for record in train]
    labels = [record["mode"] for record in train]
    direct_model = estimate(vectors, [MODE_TO_LABEL[label] for label in labels], 3)
    typed_model = estimate(vectors, labels, 5)
    all_rows = scored_rows(seed_bundle["calibration"], per_block, direct_model, typed_model,
                           {"direct": 0.0, "typed": 0.0})
    d_cut, d_cov = threshold_at_coverage([record["direct_confidence"] for record in all_rows])
    t_cut, t_cov = threshold_at_coverage([record["typed_confidence"] for record in all_rows])
    chosen = {"direct": d_cut, "typed": t_cut}
    calibration_summary = {"target_coverage": TARGET_COVERAGE,
                           "direct_threshold": d_cut, "direct_coverage": d_cov,
                           "typed_threshold": t_cut, "typed_coverage": t_cov,
                           "n": len(all_rows)}
    test_rows = scored_rows(seed_bundle["test"], per_block, direct_model, typed_model, chosen)
    normalized_train = [{"mode": row["mode"], "x": row["x"]} for row in train]
    train_digest = hashlib.sha256(json_bytes(normalized_train)).hexdigest()
    return {
        "schema": "typed-mode-risk-calibration-v1",
        "allocation": SOURCE_ALLOCATION,
        "seeds": dict(seed_bundle),
        "config": {"train_n": TRAIN_ROWS, "per_block": per_block, "blocks": BLOCK_SEQUENCE,
                   "modes": 5, "dispositions": MODE_TO_LABEL, "prototypes": MODE_CUES,
                   "flip_p": 0.08, "drop_p": 0.20, "alpha": 1.0,
                   "target_coverage": TARGET_COVERAGE,
                   "threshold_rule": "nearest pooled coverage; tie higher coverage then lower threshold"},
        "train": {"n": len(train), "mode_counts": [labels.count(mode) for mode in range(5)],
                  "rows_sha256": train_digest},
        "calibration": {"summary": calibration_summary, "rows": all_rows},
        "test": {"summary": block_metrics(test_rows), "rows": test_rows},
        "controls": decision_controls(direct_model, typed_model, chosen),
    }


def original_gates(reference):
    calibration = reference["calibration"]["summary"]
    test = reference["test"]
    rows = test["rows"]
    summary = test["summary"]
    direct_pooled = sum(record["direct_covered"] for record in rows) / len(rows)
    typed_pooled = sum(record["typed_covered"] for record in rows) / len(rows)
    calibration_ok = (abs(calibration["direct_coverage"] - TARGET_COVERAGE) <= 0.02 and
                      abs(calibration["typed_coverage"] - TARGET_COVERAGE) <= 0.02)
    heldout_coverage_ok = (abs(direct_pooled - typed_pooled) <= 0.03 and all(
        abs(summary[b]["direct_coverage"] - summary[b]["typed_coverage"]) <= 0.05 for b in PRIMARY_BLOCKS))
    controls = reference["controls"]
    prototypes_ok = all(p["direct"] == p["expected"] and p["typed"] == p["expected"]
                        for p in controls["prototypes"])
    abstention_ok = all(c["direct"] is None and c["typed"] is None for c in controls["fail_closed"])
    risk_ok = all(summary[b]["direct_wrong"] > 0 and
                  summary[b]["typed_wrong"] <= summary[b]["direct_wrong"] * 0.75 and
                  summary[b]["typed_wrong"] <= summary[b]["direct_wrong"] for b in PRIMARY_BLOCKS)
    if not calibration_ok or not heldout_coverage_ok:
        decision = "HOLD_CALIBRATION_COVERAGE_INSTABILITY"
    elif not prototypes_ok or not abstention_ok:
        decision = "FAIL_CONTROL_OR_INTEGRITY"
    elif risk_ok:
        decision = "PASS_TYPED_MODE_MATCHED_COVERAGE_SCOPED"
    else:
        decision = "FAIL_TYPED_MODE_NO_SELECTIVE_RISK_ADVANTAGE"
    return {"decision": decision, "calibration_coverage_ok": calibration_ok,
            "heldout_coverage_match_ok": heldout_coverage_ok, "prototype_controls_ok": prototypes_ok,
            "fail_closed_controls_ok": abstention_ok, "primary_risk_gate_ok": risk_ok,
            "direct_pooled_coverage": direct_pooled, "typed_pooled_coverage": typed_pooled}


def corruptions(reference):
    return [
        lambda x: x.__setitem__("schema", "bad"),
        lambda x: x.__setitem__("allocation", "bad"),
        lambda x: x["seeds"].__setitem__("test", x["seeds"]["test"] + 1),
        lambda x: x["train"].__setitem__("rows_sha256", "f" * 64),
        lambda x: x["config"].__setitem__("target_coverage", 0.5),
        lambda x: x["calibration"]["summary"].__setitem__("typed_threshold", 0.0),
        lambda x: x["calibration"]["rows"][0].__setitem__("x", [1,1,1,1,1,1]),
        lambda x: x["calibration"]["rows"][0].__setitem__("mode", (x["calibration"]["rows"][0]["mode"] + 1) % 5),
        lambda x: x["calibration"]["rows"][0].__setitem__("direct_confidence", 0.0),
        lambda x: x["calibration"]["rows"][0].__setitem__("typed_confidence", 0.0),
        lambda x: x["test"]["rows"][0].__setitem__("block", "MULTI_MISSING"),
        lambda x: x["test"]["rows"][0].__setitem__("truth", (x["test"]["rows"][0]["truth"] + 1) % 3),
        lambda x: x["test"]["rows"][0].__setitem__("direct_emit", None),
        lambda x: x["test"]["rows"][0].__setitem__("typed_wrong", not x["test"]["rows"][0]["typed_wrong"]),
        lambda x: x["test"]["summary"]["COMPLETE"].__setitem__("typed_wrong", 999),
        lambda x: x["controls"]["fail_closed"][1].__setitem__("typed", 2),
    ]


def _mutated(reference, mutate):
    candidate = copy.deepcopy(reference)
    mutate(candidate)
    return candidate


def audit_bytes(raw, expected_sha=EXPECTED_RAW_SHA256, expected_size=EXPECTED_RAW_BYTES):
    parsed = json.loads(raw)
    issues = []
    observed_sha = hashlib.sha256(raw).hexdigest()
    if len(raw) != expected_size or observed_sha != expected_sha:
        issues.append("input_identity_mismatch")
    if json_bytes(parsed) != raw:
        issues.append("noncanonical_json")
    if parsed.get("allocation") != SOURCE_ALLOCATION or parsed.get("seeds") != SEEDS:
        issues.append("source_allocation_mismatch")
    reconstructed_python = regenerate()
    reference_json = json.loads(json_bytes(reconstructed_python))
    if parsed != reference_json:
        issues.append("normalized_reconstruction_mismatch")
    rejects = sum(_mutated(reference_json, mutation) != reference_json
                  for mutation in corruptions(reference_json))
    if rejects != 16:
        issues.append("corruption_control_failure")
    return {"audit_allocation": AUDIT_ALLOCATION, "source_allocation": SOURCE_ALLOCATION,
            "pass": not issues, "errors": issues, "raw_sha256": observed_sha, "raw_bytes": len(raw),
            "calibration_rows": len(parsed.get("calibration", {}).get("rows", [])),
            "test_rows": len(parsed.get("test", {}).get("rows", [])),
            "corruption_controls": {"rejected": rejects, "total": 16},
            "supplemental_preregistered_decision": original_gates(reference_json) if not issues else None,
            "note": "post-hoc supplemental audit only; original #5198 disposition is not replaced"}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_posthoc.py RAW_JSON EXPECTED_SHA256")
    raw = Path(sys.argv[1]).read_bytes()
    result = audit_bytes(raw, sys.argv[2], EXPECTED_RAW_BYTES)
    target = Path("/audit")
    target.mkdir(parents=True, exist_ok=True)
    (target / "audit.json").write_bytes(json_bytes(result))
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)
