"""Independent raw-only audit; intentionally imports no candidate module."""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path

import numpy as np

W = H = 144
R = 4
P = 9
SUPPORT_POINTS = ((72, 72), (51, 51), (93, 51), (51, 93), (93, 93))
DISTRACTOR_POINT = (4, 4)
BLOCK_NAMES = ("northwest", "northeast", "southwest", "southeast")
SEED_SET = (659101, 659102, 659103, 659104, 659105)
WIDTH_HIDDEN = 16
ITERATIONS = 250
RATE = np.float32(0.8)
SCALE = np.float32(0.04 * math.sqrt(1200 / (W * H)))
ACCEPT_THRESHOLD = 0.75
YIELD_THRESHOLD = 0.25


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def qname(point):
    return ("north" if point[1] < H // 2 else "south") + ("west" if point[0] < W // 2 else "east")


def margin(point):
    x, y = point
    return min(x - 5, W - x - 5, y - 5, H - y - 5)


def support_distance(point):
    return min(d(point, center) for center in SUPPORT_POINTS)


def independent_design():
    candidates = []
    for row in range(10, H - 9, P):
        for col in range(10, W - 9, P):
            site = (col, row)
            support_clear = all(max(abs(col - sx), abs(row - sy)) >= P for sx, sy in SUPPORT_POINTS)
            distractor_clear = max(abs(col - DISTRACTOR_POINT[0]), abs(row - DISTRACTOR_POINT[1])) >= P
            if margin(site) >= 5 and support_clear and distractor_clear:
                candidates.append(site)
    table = {name: {} for name in ("position_random", "spatial_block")}
    for stratum in table:
        for block in ("northwest", "northeast", "southeast"):
            sites = [p for p in candidates if qname(p) == block]
            if stratum == "position_random":
                sites = [p for p in sites if 9 <= support_distance(p) < 27]
                sites.sort(key=lambda p: (support_distance(p), p[1], p[0]))
            else:
                sites = [p for p in sites if support_distance(p) >= 27]
                sites.sort(key=lambda p: (-support_distance(p), p[1], p[0]))
            table[stratum][block] = [list(p) for p in sites[:16]]
        table[stratum]["southwest"] = [[p[1], p[0]] for p in table[stratum]["northeast"]]
    return {"schema": "spatial-block-position-6590-t1-design-v1", "tile": [W, H],
            "patch": [9, 9], "grid_origin": [10, 10], "grid_pitch": P,
            "edge_margin_min": 5, "training_support": [list(p) for p in SUPPORT_POINTS],
            "negative_distractor": list(DISTRACTOR_POINT),
            "random_nearest_support_distance": "9 <= euclidean < 27",
            "block_nearest_support_distance": "euclidean >= 27",
            "centers_per_quadrant_per_cohort": 16, "cohorts": table}


def build_rows(seed, centers, fixed_center, count, split):
    if (centers is None) == (fixed_center is None):
        raise ValueError("invalid positive site policy")
    generator = np.random.default_rng(seed)
    matrix = np.empty((2 * count, H, W), dtype=np.float32)
    target = np.zeros(2 * count, dtype=np.int64)
    records = []
    for j in range(count):
        location = centers[j % len(centers)] if centers is not None else fixed_center
        for label in (1, 0):
            index = 2 * j + (0 if label else 1)
            pixels = generator.normal(0, 0.03, (H, W)).astype(np.float32)
            if label:
                x, y = location
                pixels[y - R:y + R + 1, x - R:x + R + 1] += np.float32(0.8)
                target[index] = 1
            else:
                pixels[0:9, 0:9] += np.float32(0.8)
            matrix[index] = pixels
            records.append({"source_id": f"{split}:{seed}:{index:05d}", "seed": seed,
                            "row_index": index, "label": label,
                            "positive_center": list(location) if label else None,
                            "distractor_center": list(DISTRACTOR_POINT) if not label else None,
                            "image_sha256": sha(pixels.tobytes(order="C"))})
    return matrix.reshape(2 * count, -1), target, records


def initialize(seed):
    generator = np.random.default_rng(seed)
    first = generator.normal(0, float(SCALE), (W * H, WIDTH_HIDDEN)).astype(np.float32)
    hidden_bias = np.zeros(WIDTH_HIDDEN, np.float32)
    second = generator.normal(0, 0.04, WIDTH_HIDDEN).astype(np.float32)
    output_bias = np.float32(0)
    return first, hidden_bias, second, output_bias


def refit(features, labels, seed):
    first, hidden_bias, second, output_bias = initialize(seed)
    labels = labels.astype(np.float32)
    for _ in range(ITERATIONS):
        pre = features @ first + hidden_bias
        hidden = np.maximum(pre, 0)
        logits = hidden @ second + output_bias
        probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -30, 30)))
        residual = (probs - labels) / labels.size
        grad_second = hidden.T @ residual
        grad_output_bias = np.float32(residual.sum())
        grad_hidden = residual[:, None] * second
        grad_hidden[pre <= 0] = 0
        grad_first = features.T @ grad_hidden
        grad_hidden_bias = grad_hidden.sum(axis=0)
        second -= RATE * grad_second
        output_bias -= RATE * grad_output_bias
        first -= RATE * grad_first
        hidden_bias -= RATE * grad_hidden_bias
    return first, hidden_bias, second, output_bias


def infer(model, features):
    first, hidden_bias, second, output_bias = model
    logits = np.maximum(features @ first + hidden_bias, 0) @ second + output_bias
    return 1.0 / (1.0 + np.exp(-np.clip(logits, -30, 30)))


def model_hash(model):
    return sha(b"".join(np.asarray(value).tobytes(order="C") for value in model))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def run(root: Path, out: Path) -> dict:
    start = time.perf_counter()
    errors = []
    frozen_design = json.loads((root / "design.json").read_text(encoding="utf-8"))
    expected_design = independent_design()
    if frozen_design != expected_design:
        errors.append("frozen_design_reconstruction_mismatch")

    candidate_dir = Path(os.environ.get("CANDIDATE_EVIDENCE", "/candidate"))
    train_manifest = read_jsonl(candidate_dir / "training_manifest.jsonl")
    eval_manifest = read_jsonl(candidate_dir / "evaluation_manifest.jsonl")
    prediction_rows = read_jsonl(candidate_dir / "predictions.jsonl")
    receipt_rows = read_jsonl(candidate_dir / "training_receipts.jsonl")
    environment = json.loads((candidate_dir / "environment.json").read_text(encoding="utf-8"))
    if (environment.get("candidate_invocations") != 1
            or environment.get("local_model_fits") != len(SEED_SET) * 2
            or environment.get("external_model_api_requests") != 0
            or environment.get("network_expected") != "none"
            or environment.get("gpu") is not False
            or environment.get("gui_or_effects") is not False):
        errors.append("candidate_environment_receipt_mismatch")
    raw_hashes = json.loads((candidate_dir / "RAW_SHA256.json").read_text(encoding="utf-8"))
    actual_files = {path.relative_to(candidate_dir).as_posix(): sha(path.read_bytes())
                    for path in candidate_dir.rglob("*") if path.is_file() and path.name != "RAW_SHA256.json"}
    if raw_hashes != actual_files:
        errors.append("raw_sha256_manifest_mismatch")
    receipt_by_key = {(row["seed"], row["arm"]): row for row in receipt_rows}
    train_by_key = {}
    train_inputs_by_key = {}
    cursor = 0
    for seed in SEED_SET:
        for arm in ("control", "diversified"):
            centers = None if arm == "control" else list(SUPPORT_POINTS)
            fixed = (72, 72) if arm == "control" else None
            xtrain, ytrain, expected_rows = build_rows(seed + 1, centers, fixed, 80, f"train:{seed}")
            actual_rows = train_manifest[cursor:cursor + len(expected_rows)]
            cursor += len(expected_rows)
            if actual_rows != [{"seed": seed, "arm": arm, **row} for row in expected_rows]:
                errors.append(f"training_manifest_mismatch:{seed}:{arm}")
            receipt = receipt_by_key.get((seed, arm))
            if receipt is None:
                errors.append(f"missing_training_receipt:{seed}:{arm}")
                continue
            if receipt.get("training_inputs_sha256") != sha(xtrain.tobytes(order="C")):
                errors.append(f"training_input_hash_mismatch:{seed}:{arm}")
            if receipt.get("training_labels_sha256") != sha(ytrain.tobytes(order="C")):
                errors.append(f"training_label_hash_mismatch:{seed}:{arm}")
            if receipt.get("training_rows") != 160 or receipt.get("positive_rows") != 80 or receipt.get("negative_rows") != 80:
                errors.append(f"training_denominator_mismatch:{seed}:{arm}")
            if (receipt.get("init_seed") != seed + 5 or receipt.get("steps") != ITERATIONS
                    or receipt.get("learning_rate") != float(RATE)
                    or receipt.get("initialization_std") != float(SCALE)):
                errors.append(f"training_recipe_mismatch:{seed}:{arm}")
            if receipt.get("initial_weights_sha256") != model_hash(initialize(seed + 5)):
                errors.append(f"paired_initialization_mismatch:{seed}:{arm}")
            independently_fit = refit(xtrain, ytrain, seed + 5)
            path = candidate_dir / "weights" / receipt.get("weights_file", "")
            if not path.is_file() or sha(path.read_bytes()) != receipt.get("weights_file_sha256"):
                errors.append(f"weight_file_hash_mismatch:{seed}:{arm}")
            else:
                with np.load(path) as weight_file:
                    supplied = (weight_file["w1"], weight_file["b1"],
                                weight_file["w2"], np.float32(weight_file["b2"]))
                if model_hash(supplied) != receipt.get("model_arrays_sha256"):
                    errors.append(f"weight_array_hash_mismatch:{seed}:{arm}")
                if model_hash(supplied) != model_hash(independently_fit):
                    errors.append(f"independent_refit_mismatch:{seed}:{arm}")
            train_by_key[(seed, arm)] = independently_fit
            train_inputs_by_key[(seed, arm)] = (xtrain, ytrain)

        control = train_inputs_by_key.get((seed, "control"))
        treatment = train_inputs_by_key.get((seed, "diversified"))
        if control is not None and treatment is not None:
            if not np.array_equal(control[1], treatment[1]):
                errors.append(f"paired_training_labels_mismatch:{seed}")
            if not np.array_equal(control[0][1::2], treatment[0][1::2]):
                errors.append(f"paired_negative_sources_mismatch:{seed}")
            if np.array_equal(control[0][0::2], treatment[0][0::2]):
                errors.append(f"diversified_training_arm_vacuous:{seed}")

    if cursor != len(train_manifest):
        errors.append("training_manifest_row_count_mismatch")
    if len(receipt_rows) != len(SEED_SET) * 2:
        errors.append("training_receipt_count_mismatch")

    eval_cursor = 0
    expected_rows_by_group = {}
    design_cohorts = expected_design["cohorts"]
    for seed in SEED_SET:
        for cohort, offset in (("base", 10000), ("position_random", 20000), ("spatial_block", 30000)):
            if cohort == "base":
                centers, fixed = None, (72, 72)
            else:
                centers = [tuple(p) for block in BLOCK_NAMES for p in design_cohorts[cohort][block]]
                fixed = None
            xeval, yeval, expected_rows = build_rows(seed + offset, centers, fixed, 512,
                                                     f"eval:{seed}:{cohort}")
            actual_rows = eval_manifest[eval_cursor:eval_cursor + len(expected_rows)]
            eval_cursor += len(expected_rows)
            decorated = [{"seed": seed, "cohort": cohort, **row} for row in expected_rows]
            if actual_rows != decorated:
                errors.append(f"evaluation_manifest_mismatch:{seed}:{cohort}")
            expected_rows_by_group[(seed, cohort)] = (xeval, yeval, expected_rows)
    if eval_cursor != len(eval_manifest):
        errors.append("evaluation_manifest_row_count_mismatch")

    expected_pred_count = 0
    prediction_index = {(r["seed"], r["arm"], r["cohort"], r["source_id"]): r for r in prediction_rows}
    if len(prediction_index) != len(prediction_rows):
        errors.append("duplicate_prediction_key")
    for seed in SEED_SET:
        for arm in ("control", "diversified"):
            model = train_by_key.get((seed, arm))
            if model is None:
                continue
            receipt = receipt_by_key[(seed, arm)]
            for cohort in ("base", "position_random", "spatial_block"):
                xeval, yeval, expected_meta = expected_rows_by_group[(seed, cohort)]
                probabilities = infer(model, xeval)
                expected_pred_count += len(yeval)
                for meta, label, prob in zip(expected_meta, yeval.tolist(), probabilities.tolist()):
                    key = (seed, arm, cohort, meta["source_id"])
                    actual = prediction_index.get(key)
                    if actual is None:
                        errors.append(f"missing_prediction:{seed}:{arm}:{cohort}:{meta['row_index']}")
                        continue
                    center = meta["positive_center"]
                    q = qname(tuple(center)) if center else None
                    expected_decision = "ACCEPT" if prob >= ACCEPT_THRESHOLD else (
                        "YIELD" if prob >= YIELD_THRESHOLD else "REJECT")
                    if (actual.get("label") != label or actual.get("positive_center") != center
                            or actual.get("quadrant") != q
                            or actual.get("nearest_support_distance") != (support_distance(tuple(center)) if center else None)
                            or actual.get("edge_margin") != (margin(tuple(center)) if center else None)
                            or (center is not None and not math.isclose(
                                actual.get("distractor_distance", float("nan")),
                                d(tuple(center), DISTRACTOR_POINT), rel_tol=1e-12, abs_tol=1e-12))
                            or actual.get("image_sha256") != meta["image_sha256"]
                            or actual.get("weights_file_sha256") != receipt.get("weights_file_sha256")
                            or actual.get("decision") != expected_decision
                            or actual.get("classification") != int(prob >= 0.5)
                            or not math.isclose(actual.get("probability", float("nan")), prob,
                                                rel_tol=1e-6, abs_tol=1e-7)):
                        errors.append(f"prediction_reconstruction_mismatch:{seed}:{arm}:{cohort}:{meta['row_index']}")
    if len(prediction_rows) != expected_pred_count:
        errors.append("prediction_row_count_mismatch")
    training_sources = {row.get("source_id") for row in train_manifest}
    evaluation_sources = {row.get("source_id") for row in eval_manifest}
    if training_sources & evaluation_sources:
        errors.append("training_evaluation_source_overlap")

    summaries = {}
    for arm in ("control", "diversified"):
        summaries[arm] = {}
        for cohort in ("base", "position_random", "spatial_block"):
            rows = [r for r in prediction_rows if r["arm"] == arm and r["cohort"] == cohort]
            pos = [r for r in rows if r["label"] == 1]
            neg = [r for r in rows if r["label"] == 0]
            summaries[arm][cohort] = {
                "positive_rows": len(pos), "positive_accepts": sum(r["decision"] == "ACCEPT" for r in pos),
                "positive_accept_rate": (sum(r["decision"] == "ACCEPT" for r in pos) / len(pos)) if pos else None,
                "positive_yield_rate": (sum(r["decision"] == "YIELD" for r in pos) / len(pos)) if pos else None,
                "positive_reject_rate": (sum(r["decision"] == "REJECT" for r in pos) / len(pos)) if pos else None,
                "negative_rows": len(neg), "false_accepts": sum(r["decision"] == "ACCEPT" for r in neg),
                "false_accept_rate": (sum(r["decision"] == "ACCEPT" for r in neg) / len(neg)) if neg else None,
            }
    block_tables = {}
    seed_contrasts = {}
    for seed in SEED_SET:
        seed_rates = {}
        for cohort in ("position_random", "spatial_block"):
            positives = [r for r in prediction_rows if r["seed"] == seed and r["arm"] == "diversified"
                         and r["cohort"] == cohort and r["label"] == 1]
            seed_rates[cohort] = (sum(r["decision"] == "ACCEPT" for r in positives) / len(positives)
                                  if positives else None)
        per_seed = {}
        for block in BLOCK_NAMES:
            rows = [r for r in prediction_rows if r["seed"] == seed and r["arm"] == "diversified"
                    and r["cohort"] == "spatial_block" and r["label"] == 1 and r["quadrant"] == block]
            center_support = len({tuple(r["positive_center"]) for r in rows})
            accepts = sum(r["decision"] == "ACCEPT" for r in rows)
            per_seed[block] = {"unique_centers": center_support, "positive_rows": len(rows),
                               "accepts": accepts, "accept_rate": accepts / len(rows) if rows else None}
            if center_support < 8 or len(rows) < 100:
                errors.append(f"block_support_below_frozen_floor:{seed}:{block}")
        block_tables[str(seed)] = per_seed
        seed_contrasts[str(seed)] = {"position_random_positive_accept_rate": seed_rates["position_random"],
                                     "spatial_block_positive_accept_rate": seed_rates["spatial_block"],
                                     "random_minus_block": (seed_rates["position_random"] - seed_rates["spatial_block"]
                                                            if seed_rates["position_random"] is not None
                                                            and seed_rates["spatial_block"] is not None else None)}

    treatment_random = summaries["diversified"]["position_random"]["positive_accept_rate"]
    treatment_block = summaries["diversified"]["spatial_block"]["positive_accept_rate"]
    gap = treatment_random - treatment_block if treatment_random is not None and treatment_block is not None else None
    competent = all(summaries[arm]["base"]["positive_accept_rate"] >= 0.80 for arm in ("control", "diversified"))
    negative_ok = all(summaries[arm][cohort]["false_accept_rate"] <= 0.05
                      for arm in ("control", "diversified")
                      for cohort in ("base", "position_random", "spatial_block"))
    if errors:
        decision = "HOLD_AUDIT_INTEGRITY"
    elif not competent or not negative_ok:
        decision = "HOLD_MODEL_INCOMPETENT_OR_FALSE_ACCEPT"
    elif gap >= 0.20:
        decision = "H_PASS_SCOPED"
    else:
        decision = "H_FAIL_SCOPED"
    result = {"schema": "spatial-block-position-6590-t1-audit-v1", "decision": decision,
              "errors": errors, "reconstructed_seeds": len(SEED_SET),
              "independently_refit_models": len(train_by_key),
              "prediction_rows_reconstructed": expected_pred_count,
              "summaries": summaries, "block_tables_by_seed": block_tables,
              "seed_contrasts": seed_contrasts,
              "diversified_random_minus_block_positive_accept_gap": gap,
              "base_competence_gate": competent, "false_accept_gate": negative_ok,
              "audit_seconds": time.perf_counter() - start}
    out.mkdir(parents=True, exist_ok=True)
    (out / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.out), indent=2, sort_keys=True))
