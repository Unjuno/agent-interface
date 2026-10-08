"""Fresh-seed, source-bound #4844 synthetic typed-mode allocation."""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
from pathlib import Path

ALLOCATION = "typed-mode-4844-successor-20260928-02"
TRAIN_SEED = 484421
TEST_SEED = 484422
N_TRAIN = 2000
N_TEST = 4800
ALPHA = 1.0
THRESHOLD = 0.65
FLIP_P = 0.08
DROP_P = 0.20
MODES = 5
DISPOSITIONS = (0, 0, 1, 2, 2)
NAMES = ("REBIND", "WAIT_OBSERVE", "REOBSERVE")
PROTOTYPES = (
    (0, 0, 0, 0, 0, 0),
    (1, 1, 1, 1, 1, 1),
    (0, 1, 0, 1, 0, 1),
    (1, 0, 1, 0, 1, 0),
    (0, 0, 1, 1, 0, 1),
)
BLOCKS = ("COMPLETE", "SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT", "NUISANCE_SHIFT")
PRIMARY = ("SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT")
ROWS_PER_BLOCK = 960


def _sample(rng: random.Random, mode: int, block: str, *, training: bool) -> tuple[tuple[int, ...], tuple[bool, ...]]:
    bits = list(PROTOTYPES[mode])
    for i in range(6):
        if rng.random() < FLIP_P:
            bits[i] ^= 1
    mask = [True] * 6
    if block == "SINGLE_MISSING":
        mask[1] = False
    elif block == "MULTI_MISSING":
        mask[1] = mask[4] = False
    elif block == "COMPOSITION_HOLDOUT":
        bits[0] ^= 1
        bits[5] ^= 1
    elif block == "NUISANCE_SHIFT":
        bits[3] ^= 1
    if training or block != "COMPLETE":
        for i in range(6):
            if rng.random() < DROP_P:
                mask[i] = False
    return tuple(bits), tuple(mask)


def _encode(bits: tuple[int, ...], mask: tuple[bool, ...]) -> tuple[int, ...]:
    return tuple(value if observed else -1 for value, observed in zip(bits, mask))


def _fit(rows: list[tuple[int, ...]], labels: list[int], n_classes: int):
    counts = [0] * n_classes
    ones = [[0] * 6 for _ in range(n_classes)]
    seen = [[0] * 6 for _ in range(n_classes)]
    for row, label in zip(rows, labels):
        counts[label] += 1
        for j, value in enumerate(row):
            if value >= 0:
                seen[label][j] += 1
                ones[label][j] += value
    return counts, ones, seen


def _predict(row: tuple[int, ...], model):
    counts, ones, seen = model
    n_classes = len(counts)
    scores = []
    for cls in range(n_classes):
        score = math.log((counts[cls] + ALPHA) / (sum(counts) + n_classes * ALPHA))
        for j, value in enumerate(row):
            if value < 0:
                continue
            p = (ones[cls][j] + ALPHA) / (seen[cls][j] + 2 * ALPHA)
            score += math.log(p if value else 1 - p)
        scores.append(score)
    maximum = max(scores)
    exps = [math.exp(score - maximum) for score in scores]
    total = sum(exps)
    probabilities = [value / total for value in exps]
    return max(range(n_classes), key=lambda cls: (probabilities[cls], -cls)), probabilities


def _emit(row: tuple[int, ...], direct_model, mode_model):
    direct_class, direct_probs = _predict(row, direct_model)
    _, mode_probs = _predict(row, mode_model)
    disposition_probs = [
        sum(mode_probs[mode] for mode, disposition in enumerate(DISPOSITIONS) if disposition == cls)
        for cls in range(3)
    ]
    typed_class = max(range(3), key=lambda cls: (disposition_probs[cls], -cls))
    direct = direct_class if max(direct_probs) >= THRESHOLD else None
    typed = typed_class if max(mode_probs) >= THRESHOLD else None
    return direct, typed


def _row_record(block: str, mode: int, direct, typed) -> dict:
    truth = DISPOSITIONS[mode]
    return {
        "block": block,
        "mode": mode,
        "truth": truth,
        "direct": direct,
        "typed": typed,
        "direct_wrong": direct is not None and direct != truth,
        "typed_wrong": typed is not None and typed != truth,
        "direct_covered": direct is not None,
        "typed_covered": typed is not None,
        "direct_unsafe": False,
        "typed_unsafe": False,
    }


def _summarize(rows: list[dict]) -> dict:
    result = {}
    for block in BLOCKS:
        part = [row for row in rows if row["block"] == block]
        result[block] = {
            "n": len(part),
            "direct_wrong": sum(row["direct_wrong"] for row in part),
            "typed_wrong": sum(row["typed_wrong"] for row in part),
            "direct_coverage": sum(row["direct_covered"] for row in part) / len(part),
            "typed_coverage": sum(row["typed_covered"] for row in part) / len(part),
            "direct_unsafe": sum(row["direct_unsafe"] for row in part),
            "typed_unsafe": sum(row["typed_unsafe"] for row in part),
        }
    return result


def run(train_seed: int = TRAIN_SEED, test_seed: int = TEST_SEED) -> dict:
    train_rng = random.Random(train_seed)
    test_rng = random.Random(test_seed)
    train_rows, train_modes = [], []
    for i in range(N_TRAIN):
        mode = i % MODES
        bits, mask = _sample(train_rng, mode, "TRAIN", training=True)
        train_rows.append(_encode(bits, mask))
        train_modes.append(mode)
    direct_model = _fit(train_rows, [DISPOSITIONS[m] for m in train_modes], 3)
    mode_model = _fit(train_rows, train_modes, MODES)

    heldout = []
    per_mode = ROWS_PER_BLOCK // MODES
    for block in BLOCKS:
        for mode in range(MODES):
            for _ in range(per_mode):
                bits, mask = _sample(test_rng, mode, block, training=False)
                direct, typed = _emit(_encode(bits, mask), direct_model, mode_model)
                heldout.append(_row_record(block, mode, direct, typed))

    full_rows = []
    for mode, prototype in enumerate(PROTOTYPES):
        direct, typed = _emit(tuple(prototype), direct_model, mode_model)
        full_rows.append({"mode": mode, "truth": DISPOSITIONS[mode], "direct": direct, "typed": typed})
    unknown = _emit((-1, -1, -1, -1, -1, -1), direct_model, mode_model)
    contradiction = _emit((0, 0, 0, 1, 0, 1), direct_model, mode_model)
    raw = {
        "schema": "typed-mode-4844-successor-raw-v1",
        "allocation": ALLOCATION,
        "train_seed": train_seed,
        "test_seed": test_seed,
        "n_train": N_TRAIN,
        "n_test": N_TEST,
        "alpha": ALPHA,
        "threshold": THRESHOLD,
        "flip_p": FLIP_P,
        "drop_p": DROP_P,
        "blocks": list(BLOCKS),
        "primary_blocks": list(PRIMARY),
        "disposition_names": list(NAMES),
        "full_observation": full_rows,
        "unknown": {"direct": unknown[0], "typed": unknown[1]},
        "contradictory": {"direct": contradiction[0], "typed": contradiction[1]},
        "summary": _summarize(heldout),
        "rows": heldout,
    }
    return raw


if __name__ == "__main__":
    result = run()
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    out = Path(os.environ.get("OUT_DIR", "/out"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw.json").write_bytes(encoded)
    print(json.dumps({"allocation": ALLOCATION, "rows": len(result["rows"]), "sha256": hashlib.sha256(encoded).hexdigest(), "summary": result["summary"]}, sort_keys=True))
