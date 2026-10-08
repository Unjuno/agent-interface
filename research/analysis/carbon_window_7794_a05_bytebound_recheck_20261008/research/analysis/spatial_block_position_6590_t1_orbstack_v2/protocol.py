"""Frozen #6590 T1 data and MLP protocol; candidate implementation."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

WIDTH = HEIGHT = 144
PATCH_RADIUS = 4
PITCH = 9
EDGE_MARGIN = 5
SUPPORT = ((72, 72), (51, 51), (93, 51), (51, 93), (93, 93))
DISTRACTOR = (4, 4)
QUADRANTS = ("northwest", "northeast", "southwest", "southeast")
SEEDS = (659101, 659102, 659103, 659104, 659105)
HIDDEN = 16
STEPS = 250
LEARNING_RATE = np.float32(0.8)
INIT_STD = np.float32(0.04 * math.sqrt(1200 / (WIDTH * HEIGHT)))
ACCEPT_MIN = 0.75
YIELD_MIN = 0.25
MIN_CENTERS = 8
MIN_ROWS_PER_BLOCK = 100
BASE_ACCEPT_MIN = 0.80
FALSE_ACCEPT_MAX = 0.05
EVAL_REPLICATES = 8
EVAL_CENTERS_PER_QUADRANT = 16


def distance(p: tuple[int, int], q: tuple[int, int]) -> float:
    return math.hypot(p[0] - q[0], p[1] - q[1])


def edge_margin(p: tuple[int, int]) -> int:
    x, y = p
    return min(x - PATCH_RADIUS - 1, WIDTH - (x + PATCH_RADIUS + 1),
               y - PATCH_RADIUS - 1, HEIGHT - (y + PATCH_RADIUS + 1))


def quadrant(p: tuple[int, int]) -> str:
    x, y = p
    return ("north" if y < HEIGHT // 2 else "south") + ("west" if x < WIDTH // 2 else "east")


def nearest_support_distance(p: tuple[int, int]) -> float:
    return min(distance(p, q) for q in SUPPORT)


def design() -> dict:
    grid = [(x, y) for y in range(10, HEIGHT - 9, PITCH)
            for x in range(10, WIDTH - 9, PITCH)]
    valid = [p for p in grid
             if edge_margin(p) >= EDGE_MARGIN
             and all(max(abs(p[0] - q[0]), abs(p[1] - q[1])) >= PITCH for q in SUPPORT)
             and max(abs(p[0] - DISTRACTOR[0]), abs(p[1] - DISTRACTOR[1])) >= PITCH]
    cohorts: dict[str, dict[str, list[list[int]]]] = {"position_random": {}, "spatial_block": {}}
    for cohort_name, predicate, ascending in (
            ("position_random", lambda d: 9 <= d < 27, True),
            ("spatial_block", lambda d: d >= 27, False)):
        selected: dict[str, list[tuple[int, int]]] = {}
        for q in ("northwest", "northeast", "southeast"):
            pool = [p for p in valid if quadrant(p) == q and predicate(nearest_support_distance(p))]
            # Rank by geometry only, before image generation or any fit/outcome.
            pool.sort(key=lambda p: ((nearest_support_distance(p) if ascending else -nearest_support_distance(p)),
                                     p[1], p[0]))
            selected[q] = pool[:EVAL_CENTERS_PER_QUADRANT]
        selected["southwest"] = [(y, x) for x, y in selected["northeast"]]
        for q in QUADRANTS:
            cohorts[cohort_name][q] = [list(p) for p in selected[q]]

    result = {
        "schema": "spatial-block-position-6590-t1-design-v1",
        "tile": [WIDTH, HEIGHT], "patch": [9, 9], "grid_origin": [10, 10],
        "grid_pitch": PITCH, "edge_margin_min": EDGE_MARGIN,
        "training_support": [list(p) for p in SUPPORT],
        "negative_distractor": list(DISTRACTOR),
        "random_nearest_support_distance": "9 <= euclidean < 27",
        "block_nearest_support_distance": "euclidean >= 27",
        "centers_per_quadrant_per_cohort": EVAL_CENTERS_PER_QUADRANT,
        "cohorts": cohorts,
    }
    return result


def validate_design(payload: dict) -> list[str]:
    errors: list[str] = []
    if payload != design():
        errors.append("design_reconstruction_mismatch")
        return errors
    for cohort in ("position_random", "spatial_block"):
        all_sites: list[tuple[int, int]] = []
        for q in QUADRANTS:
            sites = [tuple(p) for p in payload["cohorts"][cohort][q]]
            if len(sites) < MIN_CENTERS:
                errors.append(f"{cohort}:{q}:center_support_below_floor")
            if len(sites) != EVAL_CENTERS_PER_QUADRANT:
                errors.append(f"{cohort}:{q}:center_count_mismatch")
            if any(quadrant(p) != q for p in sites):
                errors.append(f"{cohort}:{q}:quadrant_mismatch")
            if any(edge_margin(p) < EDGE_MARGIN for p in sites):
                errors.append(f"{cohort}:{q}:edge_margin_mismatch")
            if any(max(abs(a[0] - b[0]), abs(a[1] - b[1])) < PITCH
                   for i, a in enumerate(sites) for b in sites[i + 1:]):
                errors.append(f"{cohort}:{q}:within_block_patch_overlap")
            all_sites.extend(sites)
        if len(set(all_sites)) != len(all_sites):
            errors.append(f"{cohort}:duplicate_center")
        if any(max(abs(a[0] - b[0]), abs(a[1] - b[1])) < PITCH
               for i, a in enumerate(all_sites) for b in all_sites[i + 1:]):
            errors.append(f"{cohort}:cross_block_patch_overlap")
    # Transposition provides matched opposite-region geometry controls.
    for source, target in (("northeast", "southwest"),):
        for p, transposed in zip(payload["cohorts"]["spatial_block"][source],
                                 payload["cohorts"]["spatial_block"][target]):
            if [p[1], p[0]] != transposed:
                errors.append(f"block_transpose_mismatch:{source}:{p}")
                break
    # At least one matched-distance pair crosses opposite quadrants, and at
    # least one same-region pair differs in support distance by >= 5 pixels.
    block = payload["cohorts"]["spatial_block"]
    cross = False
    for a, b in zip(block["northeast"], block["southwest"]):
        if abs(nearest_support_distance(tuple(a)) - nearest_support_distance(tuple(b))) < 1e-9:
            cross = True
            break
    if not cross:
        errors.append("no_opposite_region_distance_match")
    same = [tuple(p) for p in block["northwest"]]
    if not any(abs(nearest_support_distance(a) - nearest_support_distance(b)) >= 5
               for i, a in enumerate(same) for b in same[i + 1:]):
        errors.append("no_same_region_distance_contrast")
    random_set = {tuple(p) for q in QUADRANTS for p in payload["cohorts"]["position_random"][q]}
    block_set = {tuple(p) for q in QUADRANTS for p in payload["cohorts"]["spatial_block"][q]}
    if random_set & block_set:
        errors.append("random_block_center_overlap")
    return errors


def make_rows(seed: int, centers: list[tuple[int, int]] | None, fixed_center: tuple[int, int] | None,
              n_per_class: int, split: str) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    if (centers is None) == (fixed_center is None):
        raise ValueError("choose exactly one positive-center policy")
    rng = np.random.default_rng(seed)
    images = np.empty((2 * n_per_class, HEIGHT, WIDTH), dtype=np.float32)
    labels = np.zeros(2 * n_per_class, dtype=np.int64)
    rows: list[dict] = []
    for i in range(n_per_class):
        positive = i % (len(centers) if centers else 1) if centers else 0
        if centers is not None:
            center = centers[positive]
        else:
            center = fixed_center
        for class_index, label in enumerate((1, 0)):
            row_index = 2 * i + class_index
            image = rng.normal(0, 0.03, (HEIGHT, WIDTH)).astype(np.float32)
            if label:
                x, y = center
                image[y - 4:y + 5, x - 4:x + 5] += np.float32(0.8)
                labels[row_index] = 1
            else:
                image[0:9, 0:9] += np.float32(0.8)
            images[row_index] = image
            rows.append({"source_id": f"{split}:{seed}:{row_index:05d}", "seed": seed,
                         "row_index": row_index, "label": label,
                         "positive_center": list(center) if label else None,
                         "distractor_center": list(DISTRACTOR) if not label else None,
                         "image_sha256": hashlib.sha256(image.tobytes(order="C")).hexdigest()})
    return images.reshape(2 * n_per_class, -1), labels, rows


def init_model(seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.float32]:
    rng = np.random.default_rng(seed)
    w1 = rng.normal(0, float(INIT_STD), (WIDTH * HEIGHT, HIDDEN)).astype(np.float32)
    b1 = np.zeros(HIDDEN, np.float32)
    w2 = rng.normal(0, 0.04, HIDDEN).astype(np.float32)
    b2 = np.float32(0)
    return w1, b1, w2, b2


def fit(x: np.ndarray, y: np.ndarray, seed: int):
    w1, b1, w2, b2 = init_model(seed)
    y = y.astype(np.float32)
    for _ in range(STEPS):
        h0 = x @ w1 + b1
        h = np.maximum(h0, 0)
        z = h @ w2 + b2
        p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
        dz = (p - y) / len(y)
        dw2 = h.T @ dz
        db2 = np.float32(dz.sum())
        dh = dz[:, None] * w2
        dh[h0 <= 0] = 0
        dw1 = x.T @ dh
        db1 = dh.sum(0)
        w2 -= LEARNING_RATE * dw2
        b2 -= LEARNING_RATE * db2
        w1 -= LEARNING_RATE * dw1
        b1 -= LEARNING_RATE * db1
    return (w1, b1, w2, b2)


def predict(model, x: np.ndarray) -> np.ndarray:
    w1, b1, w2, b2 = model
    z = np.maximum(x @ w1 + b1, 0) @ w2 + b2
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def digest_model(model) -> str:
    return hashlib.sha256(b"".join(np.asarray(part).tobytes(order="C") for part in model)).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-design", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(design(), indent=2, sort_keys=True) + "\n"
    if args.write_design:
        args.write_design.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
