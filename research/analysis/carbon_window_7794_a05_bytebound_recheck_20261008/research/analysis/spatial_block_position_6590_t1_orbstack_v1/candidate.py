from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np

from protocol import (ACCEPT_MIN, DISTRACTOR, EVAL_CENTERS_PER_QUADRANT,
                      EVAL_REPLICATES, INIT_STD, LEARNING_RATE, QUADRANTS, SEEDS, STEPS, SUPPORT,
                      digest_model, edge_margin, fit, init_model, make_rows,
                      nearest_support_distance, predict, quadrant,
                      validate_design, write_jsonl)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path, out: Path) -> dict:
    errors = validate_design(json.loads((root / "design.json").read_text(encoding="utf-8")))
    if errors:
        raise ValueError(f"frozen design invalid: {errors}")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("formal output must be new and empty; no retries")
    out.mkdir(parents=True, exist_ok=True)
    (out / "weights").mkdir()
    started_all = time.perf_counter()
    training_rows: list[dict] = []
    evaluation_rows: list[dict] = []
    predictions: list[dict] = []
    receipts: list[dict] = []
    site_map = json.loads((root / "design.json").read_text(encoding="utf-8"))["cohorts"]
    block_centers = [tuple(p) for q in QUADRANTS for p in site_map["spatial_block"][q]]
    random_centers = [tuple(p) for q in QUADRANTS for p in site_map["position_random"][q]]
    eval_specs = (
        ("base", None, (72, 72), 10000),
        ("position_random", random_centers, None, 20000),
        ("spatial_block", block_centers, None, 30000),
    )
    eval_rows_per_class = EVAL_CENTERS_PER_QUADRANT * len(QUADRANTS) * EVAL_REPLICATES

    for seed in SEEDS:
        prepared_eval = {}
        for name, centers, fixed, offset in eval_specs:
            x_eval, y_eval, meta = make_rows(seed + offset, centers, fixed,
                                               eval_rows_per_class, f"eval:{seed}:{name}")
            prepared_eval[name] = (x_eval, y_eval, meta)
            evaluation_rows.extend({"seed": seed, "cohort": name, **row} for row in meta)
        models = {}
        for arm in ("control", "diversified"):
            train_centers = None if arm == "control" else list(SUPPORT)
            train_fixed = (72, 72) if arm == "control" else None
            x_train, y_train, meta_train = make_rows(seed + 1, train_centers,
                                                      train_fixed, 80,
                                                      f"train:{seed}")
            training_rows.extend({"seed": seed, "arm": arm, **row} for row in meta_train)
            init_seed = seed + 5
            init_hash = digest_model(init_model(init_seed))
            fit_started = time.perf_counter()
            model = fit(x_train, y_train, init_seed)
            fit_seconds = time.perf_counter() - fit_started
            weight_path = out / "weights" / f"{seed}-{arm}.npz"
            np.savez_compressed(weight_path, w1=model[0], b1=model[1],
                                w2=model[2], b2=np.asarray(model[3], dtype=np.float32))
            weight_hash = sha256(weight_path)
            model_hash = digest_model(model)
            models[arm] = (model, weight_hash, model_hash)
            receipts.append({"seed": seed, "arm": arm, "init_seed": init_seed,
                             "initial_weights_sha256": init_hash,
                             "training_rows": int(len(y_train)),
                             "positive_rows": int(y_train.sum()),
                             "negative_rows": int(len(y_train) - y_train.sum()),
                             "training_inputs_sha256": hashlib.sha256(x_train.tobytes(order="C")).hexdigest(),
                             "training_labels_sha256": hashlib.sha256(y_train.tobytes(order="C")).hexdigest(),
                             "initialization_std": float(INIT_STD),
                             "steps": STEPS, "learning_rate": float(LEARNING_RATE),
                             "fit_seconds": fit_seconds, "weights_file": weight_path.name,
                             "weights_file_sha256": weight_hash,
                             "model_arrays_sha256": model_hash})
            for cohort, (x_eval, y_eval, meta_eval) in prepared_eval.items():
                probabilities = predict(model, x_eval)
                for row, label, probability in zip(meta_eval, y_eval.tolist(), probabilities.tolist()):
                    center = row["positive_center"]
                    predictions.append({
                        "seed": seed, "arm": arm, "cohort": cohort,
                        "source_id": row["source_id"], "row_index": row["row_index"],
                        "label": int(label), "positive_center": center,
                        "quadrant": quadrant(tuple(center)) if center else None,
                        "nearest_support_distance": nearest_support_distance(tuple(center)) if center else None,
                        "edge_margin": edge_margin(tuple(center)) if center else None,
                        "distractor_distance": (float(np.hypot(center[0] - DISTRACTOR[0], center[1] - DISTRACTOR[1]))
                                                if center else None),
                        "image_sha256": row["image_sha256"],
                        "weights_file_sha256": weight_hash,
                        "probability": float(probability),
                        "decision": "ACCEPT" if probability >= ACCEPT_MIN else (
                            "YIELD" if probability >= 0.25 else "REJECT"),
                        "classification": int(probability >= 0.5),
                    })

    write_jsonl(out / "training_manifest.jsonl", training_rows)
    write_jsonl(out / "evaluation_manifest.jsonl", evaluation_rows)
    write_jsonl(out / "predictions.jsonl", predictions)
    write_jsonl(out / "training_receipts.jsonl", receipts)
    env = {"allocation": "spatial-block-position-6590-t1-orbstack-20261002-01",
           "runtime": "OrbStack Docker Engine", "platform": platform.platform(),
           "python": sys.version, "numpy": np.__version__,
           "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
           "network_expected": "none", "candidate_invocations": 1,
           "local_model_fits": len(receipts), "external_model_api_requests": 0,
           "gpu": False, "gui_or_effects": False,
           "training_rows": len(training_rows), "evaluation_rows": len(evaluation_rows),
           "prediction_rows": len(predictions),
           "training_wall_seconds": time.perf_counter() - started_all}
    (out / "environment.json").write_text(json.dumps(env, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    file_hashes = {p.relative_to(out).as_posix(): sha256(p)
                   for p in sorted(out.rglob("*")) if p.is_file()}
    (out / "RAW_SHA256.json").write_text(json.dumps(file_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return env


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.out), indent=2, sort_keys=True))
