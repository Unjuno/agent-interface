#!/usr/bin/env python3
"""Fresh-seed matched-coverage typed-mode experiment for Issue #5198."""
import hashlib
import json
import math
import random
from pathlib import Path

ALLOCATION = "typed-mode-4844-risk-calibration-20260928-01"
FORMAL_SEEDS = {"train": 67010231, "calibration": 67010232, "test": 67010233}
CONSTRUCTION_SEEDS = (550503, 550504, 550505)
TRAIN_N = 2000
PER_BLOCK = 960
MODES = 5
DISPOSITIONS = (0, 0, 1, 2, 2)
PROTOTYPES = ((0,0,0,0,0,0),(1,1,1,1,1,1),(0,1,0,1,0,1),(1,0,1,0,1,0),(0,0,1,1,0,1))
FLIP_P = 0.08
DROP_P = 0.20
ALPHA = 1.0
TARGET_COVERAGE = 0.65
BLOCKS = ("COMPLETE", "SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT", "NUISANCE_SHIFT")
PRIMARY = ("SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT")


def sample(rng, mode, block):
    bits = list(PROTOTYPES[mode])
    if block == "COMPOSITION_HOLDOUT":
        bits[0] ^= 1
        bits[5] ^= 1
    if block == "NUISANCE_SHIFT":
        bits[3] ^= 1
    for j in range(6):
        if rng.random() < FLIP_P:
            bits[j] ^= 1
    mask = [True] * 6
    if block == "SINGLE_MISSING":
        mask[1] = False
    elif block == "MULTI_MISSING":
        mask[1] = mask[4] = False
    if block != "COMPLETE":
        for j in range(6):
            if rng.random() < DROP_P:
                mask[j] = False
    return tuple(bits[j] if mask[j] else -1 for j in range(6))


def fit(xs, ys, classes):
    count = [0] * classes
    ones = [[0] * 6 for _ in range(classes)]
    seen = [[0] * 6 for _ in range(classes)]
    for x, y in zip(xs, ys):
        count[y] += 1
        for j, value in enumerate(x):
            if value >= 0:
                seen[y][j] += 1
                ones[y][j] += value
    return count, ones, seen


def posterior(x, model):
    count, ones, seen = model
    total = sum(count)
    scores = []
    for c in range(len(count)):
        score = math.log((count[c] + ALPHA) / (total + len(count) * ALPHA))
        for j, value in enumerate(x):
            if value < 0:
                continue
            p = (ones[c][j] + ALPHA) / (seen[c][j] + 2 * ALPHA)
            score += math.log(p if value else 1 - p)
        scores.append(score)
    peak = max(scores)
    exp_scores = [math.exp(v - peak) for v in scores]
    total_exp = sum(exp_scores)
    return [v / total_exp for v in exp_scores]


def top_prediction(x, direct_model, typed_model):
    dp = posterior(x, direct_model)
    mp = posterior(x, typed_model)
    direct_idx = min(range(len(dp)), key=lambda i: (-dp[i], i))
    mapped = [sum(mp[i] for i, d in enumerate(DISPOSITIONS) if d == k) for k in range(3)]
    typed_idx = min(range(len(mapped)), key=lambda i: (-mapped[i], i))
    return {"direct_class": direct_idx, "direct_confidence": dp[direct_idx],
            "typed_class": typed_idx, "typed_confidence": mapped[typed_idx]}


def choose_threshold(confidences, target=TARGET_COVERAGE):
    candidates = sorted(set(confidences))
    candidates.append(math.nextafter(max(candidates), math.inf))
    scored = []
    for threshold in candidates:
        coverage = sum(c >= threshold for c in confidences) / len(confidences)
        scored.append((abs(coverage - target), -coverage, threshold, coverage))
    _, _, threshold, coverage = min(scored)
    return threshold, coverage


def eval_rows(seed, per_block, direct_model, typed_model, thresholds):
    rng = random.Random(seed)
    rows = []
    for block in BLOCKS:
        for i in range(per_block):
            mode = i % MODES
            x = sample(rng, mode, block)
            truth = DISPOSITIONS[mode]
            top = top_prediction(x, direct_model, typed_model)
            dc, tc = top["direct_confidence"], top["typed_confidence"]
            de = top["direct_class"] if dc >= thresholds["direct"] else None
            te = top["typed_class"] if tc >= thresholds["typed"] else None
            rows.append({"block": block, "mode": mode, "truth": truth, "x": x,
                         **top, "direct_emit": de, "typed_emit": te,
                         "direct_wrong": de is not None and de != truth,
                         "typed_wrong": te is not None and te != truth,
                         "direct_covered": de is not None, "typed_covered": te is not None})
    return rows


def summarize(rows):
    result = {}
    for block in BLOCKS:
        subset = [r for r in rows if r["block"] == block]
        n = len(subset)
        result[block] = {
            "n": n,
            "direct_wrong": sum(r["direct_wrong"] for r in subset),
            "typed_wrong": sum(r["typed_wrong"] for r in subset),
            "direct_coverage": sum(r["direct_covered"] for r in subset) / n,
            "typed_coverage": sum(r["typed_covered"] for r in subset) / n,
        }
    return result


def controls(direct_model, typed_model, thresholds):
    prototypes = []
    for mode, x in enumerate(PROTOTYPES):
        p = top_prediction(x, direct_model, typed_model)
        d = p["direct_class"] if p["direct_confidence"] >= thresholds["direct"] else None
        t = p["typed_class"] if p["typed_confidence"] >= thresholds["typed"] else None
        prototypes.append({"mode": mode, "expected": DISPOSITIONS[mode], "direct": d, "typed": t})
    fail_closed = []
    for name, x in (("unknown", (-1,) * 6), ("contradictory", (0,0,0,1,0,1))):
        p = top_prediction(x, direct_model, typed_model)
        d = p["direct_class"] if p["direct_confidence"] >= thresholds["direct"] else None
        t = p["typed_class"] if p["typed_confidence"] >= thresholds["typed"] else None
        fail_closed.append({"kind": name, "direct": d, "typed": t})
    return {"prototypes": prototypes, "fail_closed": fail_closed}


def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def run_experiment(seeds, per_block=PER_BLOCK):
    train_seed, calibration_seed, test_seed = seeds
    train_rng = random.Random(train_seed)
    train_rows = []
    for i in range(TRAIN_N):
        mode = i % MODES
        train_rows.append({"mode": mode, "x": sample(train_rng, mode, "TRAIN")})
    xs = [r["x"] for r in train_rows]
    modes = [r["mode"] for r in train_rows]
    direct_model = fit(xs, [DISPOSITIONS[m] for m in modes], 3)
    typed_model = fit(xs, modes, MODES)

    uncalibrated = {"direct": 0.0, "typed": 0.0}
    calibration = eval_rows(calibration_seed, per_block, direct_model, typed_model, uncalibrated)
    thresholds = {
        "direct": choose_threshold([r["direct_confidence"] for r in calibration]),
        "typed": choose_threshold([r["typed_confidence"] for r in calibration]),
    }
    calibration_summary = {
        "target_coverage": TARGET_COVERAGE,
        "direct_threshold": thresholds["direct"][0],
        "direct_coverage": thresholds["direct"][1],
        "typed_threshold": thresholds["typed"][0],
        "typed_coverage": thresholds["typed"][1],
        "n": len(calibration),
    }
    tested = eval_rows(test_seed, per_block, direct_model, typed_model,
                       {k: thresholds[k][0] for k in thresholds})
    controls_obj = controls(direct_model, typed_model, {k: thresholds[k][0] for k in thresholds})
    train_digest = hashlib.sha256(canonical_bytes(train_rows)).hexdigest()
    return {
        "schema": "typed-mode-risk-calibration-v1",
        "allocation": ALLOCATION,
        "seeds": {"train": train_seed, "calibration": calibration_seed, "test": test_seed},
        "config": {"train_n": TRAIN_N, "per_block": per_block, "blocks": BLOCKS,
                   "modes": MODES, "dispositions": DISPOSITIONS, "prototypes": PROTOTYPES,
                   "flip_p": FLIP_P, "drop_p": DROP_P, "alpha": ALPHA,
                   "target_coverage": TARGET_COVERAGE, "threshold_rule": "nearest pooled coverage; tie higher coverage then lower threshold"},
        "train": {"n": len(train_rows), "mode_counts": [modes.count(i) for i in range(MODES)],
                  "rows_sha256": train_digest},
        "calibration": {"summary": calibration_summary, "rows": calibration},
        "test": {"summary": summarize(tested), "rows": tested},
        "controls": controls_obj,
    }


def main():
    result = run_experiment(tuple(FORMAL_SEEDS[k] for k in ("train", "calibration", "test")))
    raw = canonical_bytes(result)
    out = Path("/out")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_bytes(raw)
    print(json.dumps({"allocation": ALLOCATION, "rows": len(result["test"]["rows"]),
                      "result_bytes": len(raw), "result_sha256": hashlib.sha256(raw).hexdigest(),
                      "calibration": result["calibration"]["summary"],
                      "test": result["test"]["summary"]}, sort_keys=True))


if __name__ == "__main__":
    main()
