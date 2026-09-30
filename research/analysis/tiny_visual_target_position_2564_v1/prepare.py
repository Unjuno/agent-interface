from __future__ import annotations

import hashlib
from typing import Any

import numpy as np


ALLOCATION = "tiny-visual-target-position-support-2564-20260927-01"
FORMAL_SEEDS = [8962800, 8962900, 8963000, 8963100, 8963200]
CONSTRUCTION_SEED = 8962700
ARMS = ("control", "treatment")
SUPPORT_CENTERS = ((20, 15), (8, 8), (32, 8), (8, 22), (32, 22))
EVAL_CENTERS = {"base": (20, 15), "translation_a": (20, 25), "translation_b": (8, 15)}
IMAGE_SHAPE = (30, 40)


def digest(row: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(row, dtype=np.float32).tobytes(order="C")).hexdigest()


def make_tiles(n: int, seed: int, positive_centers: tuple[tuple[int, int], ...] | None = None,
               fixed_positive_center: tuple[int, int] | None = None) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    if n not in (80, 160):
        raise ValueError("all frozen train/evaluation splits contain exactly 80 or 160 rows")
    if (positive_centers is None) == (fixed_positive_center is None):
        raise ValueError("select exactly one positive-center policy")
    rng = np.random.default_rng(seed)
    images = rng.normal(0, 0.03, (n, *IMAGE_SHAPE)).astype(np.float32)
    labels = np.zeros(n, dtype=np.int64)
    rows: list[dict[str, Any]] = []
    for i in range(n):
        positive = i % 2 == 0
        labels[i] = int(positive)
        center = None
        if positive:
            if positive_centers is not None:
                center = positive_centers[(i // 2) % len(positive_centers)]
            else:
                center = fixed_positive_center
            cx, cy = center
            images[i, cy - 4:cy + 5, cx - 4:cx + 5] += np.float32(0.8)
        else:
            images[i, 2:7, 2:7] += np.float32(0.8)
        rows.append({"case_id": f"case-{i:03d}", "label": int(positive),
                     "positive_center": list(center) if center is not None else None,
                     "distractor_center": None if positive else [4, 4],
                     "image_sha256": digest(images[i])})
    return images.reshape(n, -1), labels, rows


def training_data(seed: int, arm: str):
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    if arm == "control":
        return make_tiles(160, seed, fixed_positive_center=(20, 15))
    return make_tiles(160, seed, positive_centers=SUPPORT_CENTERS)


def evaluation_data(seed: int, stratum: str):
    if stratum not in EVAL_CENTERS:
        raise ValueError(f"unknown stratum: {stratum}")
    return make_tiles(80, seed, fixed_positive_center=EVAL_CENTERS[stratum])


def construction_summary(seed: int = CONSTRUCTION_SEED) -> dict[str, Any]:
    control_x, control_y, control_rows = training_data(seed + 1, "control")
    treatment_x, treatment_y, treatment_rows = training_data(seed + 1, "treatment")
    if not np.array_equal(control_y, treatment_y):
        raise ValueError("paired arm labels differ")
    if control_y.sum() != 80 or len(control_y) != 160:
        raise ValueError("class balance or row count invalid")
    if not np.array_equal(control_x[1::2], treatment_x[1::2]):
        raise ValueError("negative/distractor control rows differ across arms")
    if np.array_equal(control_x[0::2], treatment_x[0::2]):
        raise ValueError("positive target-position treatment is vacuous")
    for stratum in EVAL_CENTERS:
        x, y, rows = evaluation_data(seed + 2 + list(EVAL_CENTERS).index(stratum), stratum)
        if len(x) != 80 or int(y.sum()) != 40 or len({r["image_sha256"] for r in rows}) != 80:
            raise ValueError(f"invalid evaluation split: {stratum}")
    return {"allocation": ALLOCATION, "construction_seed": seed,
            "control_rows": len(control_rows), "treatment_rows": len(treatment_rows),
            "positive_rows_per_arm": int(control_y.sum()), "negative_rows_per_arm": 80,
            "same_paired_noise_and_negative_rows": True,
            "control_positive_positions": [[20, 15]],
            "treatment_positive_positions": [list(p) for p in SUPPORT_CENTERS],
            "heldout_positive_positions": {k: list(v) for k, v in EVAL_CENTERS.items()},
            "training_input_sha256": {"control": hashlib.sha256(control_x.tobytes()).hexdigest(),
                                      "treatment": hashlib.sha256(treatment_x.tobytes()).hexdigest()}}


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction", action="store_true")
    parser.add_argument("--seed", type=int, default=CONSTRUCTION_SEED)
    args = parser.parse_args()
    if not args.construction:
        parser.error("only the no-fit construction check is available from prepare.py")
    print(json.dumps(construction_summary(args.seed), indent=2, sort_keys=True))

