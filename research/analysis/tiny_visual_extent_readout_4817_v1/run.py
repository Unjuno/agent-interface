from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

from models import fit, forward_logits, initialize
from prepare import dataset

ALLOCATION = "tiny-visual-extent-readout-4817-20260927-01"
DATA_SEED = 89100471
INIT_SEED = 89100472
STEPS = 1000
LEARNING_RATE = 0.2
THRESHOLD = 0.75
SOURCE_NAMES = ("prepare.py", "models.py", "run.py", "audit.py", "controls.py", "test_construction.py")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pack_inputs(train, base, held):
    packed = {"train_x": train[0], "train_y": train[1], "base_x": base[0], "base_y": base[1]}
    for index, key in enumerate(sorted(held)):
        packed[f"held_{index}_x"] = held[key][0]
        packed[f"held_{index}_y"] = held[key][1]
    return packed


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False)
    train, base, held = dataset(DATA_SEED)
    inputs = pack_inputs(train, base, held)
    input_path = out / "INPUTS.npz"
    np.savez_compressed(input_path, **inputs)

    models = {}
    fit_seconds = {}
    initial_models = {"max_only": initialize(INIT_SEED, False), "max_mean": initialize(INIT_SEED, True)}
    initial_path = out / "INITIAL_WEIGHTS.npz"
    np.savez(initial_path, **{f"{arm}_{name}": value for arm, model in initial_models.items() for name, value in zip(("kernel", "bias", "dense", "output_bias"), model)})
    for arm, extent in (("max_only", False), ("max_mean", True)):
        start = time.perf_counter()
        models[arm] = fit(train[0], train[1], INIT_SEED, STEPS, LEARNING_RATE, extent)
        fit_seconds[arm] = time.perf_counter() - start
    weights_path = out / "WEIGHTS.npz"
    np.savez(weights_path, **{f"{arm}_{name}": value for arm, model in models.items() for name, value in zip(("kernel", "bias", "dense", "output_bias"), model)})

    logits = {}
    logits["max_only"] = {"train": forward_logits(train[0], models["max_only"], False).tolist(),
                           "base": forward_logits(base[0], models["max_only"], False).tolist()}
    logits["max_mean"] = {"train": forward_logits(train[0], models["max_mean"], True).tolist(),
                           "base": forward_logits(base[0], models["max_mean"], True).tolist()}
    centers = sorted(held)
    for index, center in enumerate(centers):
        hx, _ = held[center]
        for arm, extent in (("max_only", False), ("max_mean", True)):
            logits[arm][f"held_{index}"] = forward_logits(hx, models[arm], extent).tolist()

    raw = {
        "schema": "tiny-visual-extent-readout-construction-v1",
        "allocation": ALLOCATION,
        "data_seed": DATA_SEED,
        "init_seed": INIT_SEED,
        "steps": STEPS,
        "learning_rate": LEARNING_RATE,
        "threshold": THRESHOLD,
        "held_centers": centers,
        "fit_seconds": fit_seconds,
        "logits": logits,
        "input_sha256": sha256(input_path),
        "initial_weights_sha256": sha256(initial_path),
        "weights_sha256": sha256(weights_path),
        "source_sha256": {name: sha256(Path(__file__).parent / name) for name in SOURCE_NAMES},
        "environment": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__},
        "formal_fits": 0,
        "construction_fits": 2,
    }
    (out / "RAW.json").write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir")
    args = parser.parse_args()
    main(args.out_dir)
