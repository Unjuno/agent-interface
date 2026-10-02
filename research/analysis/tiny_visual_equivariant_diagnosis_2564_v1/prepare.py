from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

ALLOCATION = "tiny-visual-equivariant-cnn-2564-20260927-01"
FORMAL_SEEDS = [8963800, 8963900, 8964000, 8964100, 8964200]
CONSTRUCTION_SEED = 8963700
ARMS = ("control", "treatment")
SUPPORT_CENTERS = ((20, 15), (8, 8), (32, 8), (8, 22), (32, 22))
EVAL_CENTERS = ((14, 8), (26, 8), (14, 22), (26, 22), (8, 15), (20, 25), (32, 15), (20, 8))
IMAGE_SHAPE = (30, 40)


def digest(row: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(row, dtype=np.float32).tobytes(order="C")).hexdigest()


def make_tiles(n: int, seed: int, centers=None, fixed_center=None, target_size: int = 9):
    if n not in (80, 160) or target_size not in (5, 9):
        raise ValueError("frozen splits use 80/160 rows and 5x5/9x9 targets")
    if (centers is None) == (fixed_center is None):
        raise ValueError("choose exactly one positive-center policy")
    rng = np.random.default_rng(seed)
    images = rng.normal(0, 0.03, (n, *IMAGE_SHAPE)).astype(np.float32)
    labels = np.zeros(n, dtype=np.int64)
    rows: list[dict[str, Any]] = []
    half = target_size // 2
    for i in range(n):
        positive = (i % 2 == 0)
        labels[i] = int(positive)
        center = None
        if positive:
            center = centers[(i // 2) % len(centers)] if centers is not None else fixed_center
            cx, cy = center
        else:
            cx, cy = 4, 4
            half = 2
        images[i, cy-half:cy+half+1, cx-half:cx+half+1] += np.float32(0.8)
        rows.append({"case_id": f"case-{i:03d}", "label": int(positive),
                     "positive_center": list(center) if center is not None else None,
                     "target_size": 9 if positive else 5,
                     "distractor_center": None if positive else [4, 4],
                     "image_sha256": digest(images[i])})
        if not positive:
            half = target_size // 2
    return images[:, None, :, :], labels, rows


def training_data(seed: int, arm: str):
    if arm == "control":
        return make_tiles(160, seed, fixed_center=(20, 15))
    if arm == "treatment":
        return make_tiles(160, seed, centers=SUPPORT_CENTERS)
    raise ValueError(f"unknown arm: {arm}")


def evaluation_data(seed: int, center: tuple[int, int], label: str):
    return make_tiles(80, seed, fixed_center=center)


def construction_summary(seed: int = CONSTRUCTION_SEED):
    cx, cy, cr = training_data(seed + 1, "control")
    tx, ty, tr = training_data(seed + 1, "treatment")
    assert np.array_equal(cy, ty) and int(cy.sum()) == 80
    assert np.array_equal(cx[1::2], tx[1::2])
    assert not np.array_equal(cx[0::2], tx[0::2])
    assert len(cr) == len(tr) == 160
    evals = {}
    for i, center in enumerate(EVAL_CENTERS):
        x, y, rows = evaluation_data(seed + 2 + i, center, f"heldout_{i}")
        assert x.shape == (80, 1, 30, 40) and int(y.sum()) == 40
        assert len({r["image_sha256"] for r in rows}) == 80
        evals[str(center)] = {"rows": len(rows), "positive": int(y.sum()), "negative": 40,
                              "centers_disjoint_from_support": center not in SUPPORT_CENTERS}
    assert all(v["centers_disjoint_from_support"] for v in evals.values())
    return {"allocation": ALLOCATION, "construction_seed": seed, "train_rows_per_arm": 160,
            "positive_rows_per_arm": 80, "negative_rows_per_arm": 80,
            "support_centers": [list(p) for p in SUPPORT_CENTERS], "heldout": evals,
            "base_center": [20, 15], "paired_noise_and_negative_rows": True,
            "inputs_sha256": {"control": hashlib.sha256(cx.tobytes()).hexdigest(),
                              "treatment": hashlib.sha256(tx.tobytes()).hexdigest()}}


if __name__ == "__main__":
    import json
    print(json.dumps(construction_summary(), indent=2, sort_keys=True))

