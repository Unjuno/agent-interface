from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path

import numpy as np


SEEDS = [8962800, 8962900, 8963000, 8963100, 8963200]
ARMS = ("control", "treatment")
CENTERS = ((20, 15), (8, 8), (32, 8), (8, 22), (32, 22))
STRATA = {"base": (20, 15), "translation_a": (20, 25), "translation_b": (8, 15)}
IMAGE_SHAPE = (30, 40)
EXPECTED_IMAGE_ID = "sha256:ba509e8a38d311c07539c49a7a2970b6f19869de42b8008be07a85568e2c9824"


def hash_image(row):
    return hashlib.sha256(np.asarray(row, dtype=np.float32).tobytes(order="C")).hexdigest()


def independent_split(seed, count, policy):
    random = np.random.default_rng(seed)
    pixels = random.normal(0, 0.03, (count, *IMAGE_SHAPE)).astype(np.float32)
    labels, metadata = [], []
    for index in range(count):
        is_positive = index % 2 == 0
        target = None
        if is_positive:
            if policy == "control":
                target = (20, 15)
            elif policy == "treatment":
                target = CENTERS[(index // 2) % len(CENTERS)]
            elif isinstance(policy, tuple):
                target = policy
            else:
                raise ValueError("invalid independent split policy")
            px, py = target
            pixels[index, py - 4:py + 5, px - 4:px + 5] += np.float32(0.8)
        else:
            pixels[index, 2:7, 2:7] += np.float32(0.8)
        labels.append(int(is_positive))
        metadata.append({"case_id": f"case-{index:03d}", "label": int(is_positive),
                         "positive_center": list(target) if target is not None else None,
                         "distractor_center": None if is_positive else [4, 4],
                         "image_sha256": hash_image(pixels[index])})
    return pixels.reshape(count, -1), labels, metadata


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_weights(path):
    raw = base64.b64decode(path.read_text(encoding="ascii").strip(), validate=True)
    with np.load(io.BytesIO(raw), allow_pickle=False) as package:
        return raw, tuple(np.asarray(package[key], dtype=np.float32) for key in ("w1", "b1", "w2", "b2"))


def independent_forward(model, x):
    first, first_bias, second, second_bias = model
    hidden_pre = np.matmul(x, first) + first_bias
    hidden = np.where(hidden_pre > 0, hidden_pre, 0)
    logits = np.matmul(hidden, second) + second_bias
    logits = np.minimum(np.maximum(logits, -30), 30)
    return 1.0 / (1.0 + np.exp(-logits))


def independent_init_digest(seed):
    random = np.random.default_rng(seed)
    first = random.normal(0, 0.04, (1200, 16)).astype(np.float32)
    first_bias = np.zeros(16, dtype=np.float32)
    second = random.normal(0, 0.04, 16).astype(np.float32)
    second_bias = np.float32(0)
    return hashlib.sha256(first.tobytes() + first_bias.tobytes() + second.tobytes() + second_bias.tobytes()).hexdigest()


def audit(root: Path) -> dict:
    errors = []
    try:
        environment = json.loads((root / "environment.json").read_text(encoding="utf-8"))
        if environment.get("image_id") != EXPECTED_IMAGE_ID or environment.get("fits") != 10:
            errors.append("environment_image_or_fit_count")
        if environment.get("external_model_api_requests") != 0 or environment.get("host_gui_or_authority") is not False:
            errors.append("environment_scope")
    except (OSError, ValueError, TypeError):
        errors.append("environment_receipt")
    receipts = read_jsonl(root / "training_receipts.jsonl")
    train_records = read_jsonl(root / "training_manifest.jsonl")
    eval_records = read_jsonl(root / "evaluation_manifest.jsonl")
    output_records = read_jsonl(root / "predictions.jsonl")
    if len(receipts) != 10:
        errors.append(f"training_receipt_count:{len(receipts)}")
    if len(train_records) != 1600:
        errors.append(f"training_manifest_count:{len(train_records)}")
    if len(eval_records) != 1200:
        errors.append(f"evaluation_manifest_count:{len(eval_records)}")
    if len(output_records) != 2400:
        errors.append(f"prediction_count:{len(output_records)}")

    train_keyed = {(r["seed"], r["arm"], r["case_id"]): r for r in train_records}
    eval_keyed = {(r["seed"], r["stratum"], r["case_id"]): r for r in eval_records}
    out_keyed = {(r["seed"], r["arm"], r["stratum"], r["case_id"]): r for r in output_records}
    if len(train_keyed) != len(train_records):
        errors.append("duplicate_training_manifest_key")
    if len(eval_keyed) != len(eval_records):
        errors.append("duplicate_evaluation_manifest_key")
    if len(out_keyed) != len(output_records):
        errors.append("duplicate_prediction_key")

    metric = {}
    receipt_keyed = {(r["seed"], r["arm"]): r for r in receipts}
    if len(receipt_keyed) != len(receipts):
        errors.append("duplicate_training_receipt")
    for seed in SEEDS:
        for arm in ARMS:
            count = 160
            policy = arm
            regenerated_x, regenerated_y, regenerated_meta = independent_split(seed + 1, count, policy)
            expected_train_sha = hashlib.sha256(regenerated_x.tobytes(order="C")).hexdigest()
            actual_train_rows = [train_keyed.get((seed, arm, f"case-{i:03d}")) for i in range(160)]
            if any(row is None for row in actual_train_rows):
                errors.append(f"missing_training_rows:{seed}:{arm}")
            else:
                for expected, actual in zip(regenerated_meta, actual_train_rows):
                    if any(actual.get(key) != expected.get(key) for key in ("case_id", "label", "positive_center", "distractor_center", "image_sha256")):
                        errors.append(f"training_input_mismatch:{seed}:{arm}:{expected['case_id']}")
                rec = receipt_keyed.get((seed, arm), {})
                if rec.get("training_inputs_sha256") != expected_train_sha:
                    errors.append(f"training_matrix_digest:{seed}:{arm}")
                if rec.get("init_weights_sha256") != independent_init_digest(seed + 5):
                    errors.append(f"initial_weight_digest:{seed}:{arm}")
                if rec.get("steps") != 250 or rec.get("learning_rate") != 0.800000011920929:
                    # JSON roundtripping of float32(0.8) is expected to retain its exact scalar value.
                    if rec.get("steps") != 250 or not np.isclose(rec.get("learning_rate", -1), 0.8, rtol=0, atol=1e-7):
                        errors.append(f"training_recipe:{seed}:{arm}")
            receipt = receipt_keyed.get((seed, arm), {})
            weight_path = root / "weights" / f"{seed}-{arm}.npz.b64"
            try:
                weight_bytes, model = load_weights(weight_path)
                weight_sha = hashlib.sha256(weight_bytes).hexdigest()
                if receipt.get("final_weights_sha256") != weight_sha:
                    errors.append(f"weight_digest:{seed}:{arm}")
                if list(model[0].shape) != [1200, 16] or list(model[1].shape) != [16] or list(model[2].shape) != [16] or model[3].shape not in ((), (1,)):
                    errors.append(f"weight_shape:{seed}:{arm}")
            except (OSError, ValueError, KeyError, base64.binascii.Error):
                errors.append(f"weight_package:{seed}:{arm}")
                continue
            metric[(seed, arm)] = {}
            for stratum_index, (stratum, center) in enumerate(STRATA.items()):
                x, labels, expected_rows = independent_split(seed + 2 + stratum_index, 80, center)
                actual_manifest = [eval_keyed.get((seed, stratum, f"case-{i:03d}")) for i in range(80)]
                if any(row is None for row in actual_manifest):
                    errors.append(f"missing_evaluation_rows:{seed}:{stratum}")
                    continue
                for expected, actual in zip(expected_rows, actual_manifest):
                    if any(actual.get(key) != expected.get(key) for key in ("case_id", "label", "positive_center", "distractor_center", "image_sha256")):
                        errors.append(f"evaluation_input_mismatch:{seed}:{stratum}:{expected['case_id']}")
                expected_probs = independent_forward(model, x)
                positives, accepted_positive, negative_count, false_accepts, correct = 0, 0, 0, 0, 0
                for index, expected in enumerate(expected_rows):
                    record = out_keyed.get((seed, arm, stratum, expected["case_id"]))
                    if record is None:
                        errors.append(f"missing_prediction:{seed}:{arm}:{stratum}:{expected['case_id']}")
                        continue
                    probability = record.get("probability")
                    label = labels[index]
                    if record.get("label") != label or record.get("image_sha256") != expected["image_sha256"]:
                        errors.append(f"prediction_binding:{seed}:{arm}:{stratum}:{expected['case_id']}")
                    if not isinstance(probability, (float, int)) or not np.isfinite(probability) or not 0 <= probability <= 1:
                        errors.append(f"probability_invalid:{seed}:{arm}:{stratum}:{expected['case_id']}")
                        continue
                    expected_decision = "ACCEPT" if probability >= 0.75 else ("YIELD" if probability >= 0.25 else "REJECT")
                    if abs(float(probability) - float(expected_probs[index])) > 1e-7:
                        errors.append(f"prediction_recompute:{seed}:{arm}:{stratum}:{expected['case_id']}")
                    if record.get("weight_sha256") != weight_sha or record.get("model_decision") != expected_decision or record.get("classification") != int(probability >= 0.5):
                        errors.append(f"prediction_derivation:{seed}:{arm}:{stratum}:{expected['case_id']}")
                    if label:
                        positives += 1
                        accepted_positive += int(probability >= 0.75)
                    else:
                        negative_count += 1
                        false_accepts += int(probability >= 0.75)
                    correct += int(int(probability >= 0.5) == label)
                metric[(seed, arm)][stratum] = {"positive_rows": positives,
                    "positive_accepts": accepted_positive,
                    "positive_accept_rate": accepted_positive / positives if positives else 0.0,
                    "negative_rows": negative_count, "false_accepts": false_accepts,
                    "accuracy_at_0_5": correct / 80}

    gate_path = root / "gate_fixture.json"
    gate_rows = json.loads(gate_path.read_text(encoding="utf-8")) if gate_path.is_file() else []
    expected_gate = {"current_matching_positive": True, "stale_high_positive": False,
                     "digest_mismatch_high_positive": False, "current_negative": False}
    actual_gate = {row.get("case_id"): row.get("final_accept") for row in gate_rows}
    if len(gate_rows) != len(expected_gate) or actual_gate != expected_gate:
        errors.append("receipt_freshness_fixture")
    for row in gate_rows:
        expected_model = "ACCEPT" if row.get("model_probability", 0) >= 0.75 else ("YIELD" if row.get("model_probability", 0) >= 0.25 else "REJECT")
        if row.get("model_decision") != expected_model:
            errors.append(f"gate_model_derivation:{row.get('case_id')}")

    seed_deltas, control_shift, treatment_shift = [], 0, 0
    treatment_negatives, treatment_false = 0, 0
    for seed in SEEDS:
        ctrl = metric.get((seed, "control"), {})
        trt = metric.get((seed, "treatment"), {})
        ctrl_hits = sum(ctrl.get(k, {}).get("positive_accepts", 0) for k in ("translation_a", "translation_b"))
        trt_hits = sum(trt.get(k, {}).get("positive_accepts", 0) for k in ("translation_a", "translation_b"))
        control_shift += ctrl_hits
        treatment_shift += trt_hits
        seed_deltas.append(trt_hits > ctrl_hits)
        for stratum in STRATA:
            treatment_negatives += trt.get(stratum, {}).get("negative_rows", 0)
            treatment_false += trt.get(stratum, {}).get("false_accepts", 0)
    shift_positive_denominator = len(SEEDS) * 2 * 40
    shift_delta = treatment_shift / shift_positive_denominator - control_shift / shift_positive_denominator
    base_control = sum(metric.get((s, "control"), {}).get("base", {}).get("positive_accepts", 0) for s in SEEDS)
    base_treatment = sum(metric.get((s, "treatment"), {}).get("base", {}).get("positive_accepts", 0) for s in SEEDS)
    base_denominator = len(SEEDS) * 40
    base_noninferior = base_treatment / base_denominator >= base_control / base_denominator - 0.05
    data_complete = (len(metric) == 10 and all(len(metric.get((seed, arm), {})) == 3 for seed in SEEDS for arm in ARMS))
    if not data_complete or errors:
        decision = "HOLD_AUDIT_OR_PROVENANCE"
    elif treatment_false:
        decision = "FAIL_FALSE_ACCEPT"
    elif shift_delta >= 0.20 and sum(seed_deltas) >= 4 and base_noninferior and treatment_negatives == 600:
        decision = "PASS_TARGET_POSITION_SUPPORT_SCOPED"
    else:
        decision = "HOLD_NO_SAFE_BENEFIT"
    return {"schema": "tiny-visual-target-position-2564-audit-v1", "decision": decision,
            "complete": data_complete, "errors": errors,
            "heldout_translation_positive_accepts": {"treatment": treatment_shift,
                "control": control_shift, "denominator_per_arm": shift_positive_denominator,
                "absolute_delta": shift_delta, "seeds_treatment_better": sum(seed_deltas)},
            "base_positive_accepts": {"treatment": base_treatment, "control": base_control,
                "denominator": base_denominator, "noninferior_by_0_05": base_noninferior},
            "treatment_negative_cases": treatment_negatives,
            "treatment_false_accepts": treatment_false,
            "false_accept_definition": "model_probability>=0.75 on any treatment negative; independent of receipt/freshness gate",
            "receipt_fixture": actual_gate,
            "per_seed_arm_stratum": {f"{seed}:{arm}": metrics for (seed, arm), metrics in metric.items()}}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")

