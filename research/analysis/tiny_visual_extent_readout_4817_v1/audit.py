from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def independent_logits(x, kernel, bias, dense, output_bias, extent):
    # Deliberately independent direct-loop implementation, not imported from models.py.
    n, _, height, width = x.shape
    activations = np.zeros((n, height - 2, width - 2, 4), dtype=np.float64)
    for row in range(height - 2):
        for col in range(width - 2):
            for channel in range(4):
                total = float(bias[channel])
                for dy in range(3):
                    for dx in range(3):
                        total += float(x[:, 0, row + dy, col + dx].astype(np.float64) * kernel[channel, dy, dx])
                activations[:, row, col, channel] = np.maximum(0.0, total)
    flattened = activations.reshape(n, -1, 4)
    maximum = np.max(flattened, axis=1)
    pooled = np.concatenate((maximum, np.mean(flattened, axis=1)), axis=1) if extent else maximum
    return pooled @ dense.astype(np.float64) + float(output_bias)


def metrics(logits, labels, threshold):
    logits = np.asarray(logits, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.float64)
    probabilities = 1.0 / (1.0 + np.exp(-np.clip(logits, -30.0, 30.0)))
    positive = labels == 1
    negative = labels == 0
    return {
        "accuracy_at_0_5": float(np.mean((probabilities >= 0.5) == labels)),
        "positive_accept_at_0_75": float(np.mean(probabilities[positive] >= threshold)),
        "negative_false_accept_at_0_75": float(np.mean(probabilities[negative] >= threshold)),
        "positive_mean_probability": float(np.mean(probabilities[positive])),
        "negative_mean_probability": float(np.mean(probabilities[negative])),
        "rows": int(len(labels)),
        "positive_rows": int(np.sum(positive)),
        "negative_rows": int(np.sum(negative)),
    }


def main(raw_path, inputs_path, weights_path, initial_path, source_dir, audit_path=None):
    raw_path, inputs_path, weights_path, initial_path = map(Path, (raw_path, inputs_path, weights_path, initial_path))
    source_dir = Path(source_dir)
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "tiny-visual-extent-readout-construction-v1": errors.append("schema")
    if raw.get("allocation") != "tiny-visual-extent-readout-4817-20260927-01": errors.append("allocation")
    if raw.get("formal_fits") != 0 or raw.get("construction_fits") != 2: errors.append("fit_counts")
    if raw.get("steps") != 1000 or raw.get("learning_rate") != 0.2 or raw.get("threshold") != 0.75: errors.append("frozen_protocol")
    if raw.get("input_sha256") != digest(inputs_path): errors.append("input_hash")
    if raw.get("weights_sha256") != digest(weights_path): errors.append("weights_hash")
    if raw.get("initial_weights_sha256") != digest(initial_path): errors.append("initial_weights_hash")
    for name, expected in raw.get("source_sha256", {}).items():
        path = source_dir / name
        if not path.is_file() or digest(path) != expected: errors.append(f"source_hash:{name}")
    if set(raw.get("source_sha256", {})) != {"prepare.py", "models.py", "run.py", "audit.py", "controls.py", "test_construction.py"}:
        errors.append("source_set")

    with np.load(inputs_path, allow_pickle=False) as inputs, np.load(weights_path, allow_pickle=False) as weights, np.load(initial_path, allow_pickle=False) as initial:
        required = {"train_x", "train_y", "base_x", "base_y"} | {f"held_{i}_{suffix}" for i in range(8) for suffix in ("x", "y")}
        if set(inputs.files) != required: errors.append("input_keys")
        if inputs["train_x"].shape != (160, 1, 30, 40) or inputs["train_y"].shape != (160,): errors.append("train_shape")
        if inputs["base_x"].shape != (80, 1, 30, 40) or inputs["base_y"].shape != (80,): errors.append("base_shape")
        arms = ("max_only", "max_mean")
        names = ("kernel", "bias", "dense", "output_bias")
        if set(weights.files) != {f"{a}_{n}" for a in arms for n in names}: errors.append("weight_keys")
        if set(initial.files) != {f"{a}_{n}" for a in arms for n in names}: errors.append("initial_weight_keys")
        if not errors:
            if not np.array_equal(initial["max_only_kernel"], initial["max_mean_kernel"]): errors.append("initial_kernel_mismatch")
            if not np.array_equal(initial["max_only_bias"], initial["max_mean_bias"]): errors.append("initial_bias_mismatch")
            if not np.array_equal(initial["max_only_dense"], initial["max_mean_dense"][:4]): errors.append("initial_max_path_mismatch")
            if not np.all(initial["max_mean_dense"][4:] == 0): errors.append("initial_mean_path_not_zero")
            if not np.array_equal(initial["max_only_output_bias"], initial["max_mean_output_bias"]): errors.append("initial_output_bias_mismatch")

            metrics_out = {}
            recomputed_logits = {}
            for arm, extent in (("max_only", False), ("max_mean", True)):
                model = tuple(weights[f"{arm}_{name}"] for name in names)
                categories = {"train": (inputs["train_x"], inputs["train_y"]), "base": (inputs["base_x"], inputs["base_y"])}
                for i in range(8): categories[f"held_{i}"] = (inputs[f"held_{i}_x"], inputs[f"held_{i}_y"])
                metrics_out[arm] = {}
                recomputed_logits[arm] = {}
                for key, (x, y) in categories.items():
                    logits = independent_logits(x, *model, extent)
                    saved = np.asarray(raw["logits"][arm][key], dtype=np.float64)
                    if saved.shape != logits.shape or not np.allclose(saved, logits, rtol=1e-6, atol=1e-6):
                        errors.append(f"prediction_mismatch:{arm}:{key}")
                    recomputed_logits[arm][key] = logits.tolist()
                    metrics_out[arm][key] = metrics(logits, y, raw["threshold"])
            for arm in arms:
                if set(raw.get("logits", {}).get(arm, {})) != {"train", "base", *(f"held_{i}" for i in range(8))}:
                    errors.append(f"logit_categories:{arm}")

            candidate = metrics_out["max_mean"]
            baseline = metrics_out["max_only"]
            held_positive = [candidate[f"held_{i}"]["positive_accept_at_0_75"] for i in range(8)]
            held_negative = [candidate[f"held_{i}"]["negative_false_accept_at_0_75"] for i in range(8)]
            summary = {
                "max_only_train": baseline["train"],
                "max_only_base": baseline["base"],
                "max_only_held_positive_accept_mean": float(np.mean([baseline[f"held_{i}"]["positive_accept_at_0_75"] for i in range(8)])),
                "max_mean_train": candidate["train"],
                "max_mean_base": candidate["base"],
                "max_mean_held_positive_accept_mean": float(np.mean(held_positive)),
                "max_mean_held_positive_accept_by_center": held_positive,
                "max_mean_held_negative_false_accept_mean": float(np.mean(held_negative)),
                "max_mean_held_negative_false_accept_by_center": held_negative,
                "metrics": metrics_out,
                "recomputed_logits": recomputed_logits,
            }
            competent = (
                candidate["train"]["accuracy_at_0_5"] >= 0.95
                and candidate["base"]["accuracy_at_0_5"] >= 0.95
                and summary["max_mean_held_positive_accept_mean"] >= 0.90
                and summary["max_mean_held_negative_false_accept_mean"] <= 0.01
            )
            baseline_worse = summary["max_only_held_positive_accept_mean"] < 0.70
            if errors:
                decision = "STOP_PROVENANCE_OR_AUDIT"
            elif not competent:
                decision = "STOP_NO_CONSTRUCTION_COMPETENCE"
            elif not baseline_worse:
                decision = "HOLD_READOUT_NOT_DISCRIMINATING"
            else:
                decision = "PASS_EXTENT_READOUT_CONSTRUCTION_SCOPED"
            summary.update({"decision": decision, "errors": errors, "integrity_pass": not errors})

    result = {k: v for k, v in summary.items() if k != "recomputed_logits"}
    if audit_path:
        Path(audit_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    if len(sys.argv) != 7:
        raise SystemExit("usage: audit.py RAW INPUTS WEIGHTS INITIAL_WEIGHTS SOURCE_DIR AUDIT_OUT")
    raise SystemExit(main(*sys.argv[1:]))

