"""Deterministic partial-observation study for Issue #4844.

This module is intentionally standard-library-only. It contains no OS input,
network, model/provider calls, or authority-bearing output.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

MODES = ("FOCUS_LOST", "TARGET_STALE", "MODAL_BLOCKED", "APP_BUSY", "LAYOUT_CHANGED")
DISPOSITION = {
    "FOCUS_LOST": "REBIND",
    "TARGET_STALE": "YIELD",
    "MODAL_BLOCKED": "WAIT_OBSERVE",
    "APP_BUSY": "WAIT_OBSERVE",
    "LAYOUT_CHANGED": "REOBSERVE",
}
FEATURES = ("focus", "target", "modal", "busy", "geometry", "delayed_ack")
P1 = {
    "FOCUS_LOST": (0.88, 0.20, 0.12, 0.12, 0.12, 0.22),
    "TARGET_STALE": (0.15, 0.88, 0.12, 0.12, 0.22, 0.72),
    "MODAL_BLOCKED": (0.12, 0.26, 0.88, 0.10, 0.18, 0.20),
    "APP_BUSY": (0.12, 0.20, 0.12, 0.88, 0.20, 0.78),
    "LAYOUT_CHANGED": (0.12, 0.38, 0.18, 0.16, 0.88, 0.70),
}
TRAIN_SEEDS = (415571, 415572, 415573)
FORMAL_SEEDS = (415581, 415582, 415583)
TRAIN_PER_MODE = 96
ALPHA = 1.0
MIN_POSTERIOR = 0.65
MIN_MARGIN = 0.15


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def generate_rows(seed: int, per_mode: int, *, split: str, block: str) -> list[dict]:
    """Generate a fixed, class-balanced cue corpus from the declared model."""
    import random

    rng = random.Random(seed)
    rows = []
    for mode in MODES:
        for i in range(per_mode):
            truth = [int(rng.random() < p) for p in P1[mode]]
            observed = list(truth)
            if block == "SINGLE_MISSING":
                # Hide the defining cue and one independently selected cue.
                defining = MODES.index(mode)
                hidden = {defining, rng.randrange(len(FEATURES))}
                for j in hidden:
                    observed[j] = None
            elif block == "MULTI_MISSING":
                hidden = set(rng.sample(range(len(FEATURES)), 3))
                for j in hidden:
                    observed[j] = None
            elif block == "NUISANCE_SHIFT":
                # A preregistered environment shift changes only delayed_ack.
                observed[5] = 1 - observed[5]
            elif block == "COMPOSITION_HOLDOUT":
                # Mask a mode-specific cue pair, retaining the remaining evidence.
                masks = {
                    "FOCUS_LOST": (0, 5),
                    "TARGET_STALE": (1, 5),
                    "MODAL_BLOCKED": (2, 1),
                    "APP_BUSY": (3, 5),
                    "LAYOUT_CHANGED": (4, 1),
                }
                for j in masks[mode]:
                    observed[j] = None
            rows.append({
                "row_id": f"{split}:{seed}:{block}:{mode}:{i}",
                "split": split,
                "seed": seed,
                "block": block,
                "mode": mode,
                "features": observed,
                "expected": DISPOSITION[mode],
            })
    return rows


def generate_controls(seed: int) -> list[dict]:
    prototypes = {
        "FOCUS_LOST": [1, 0, 0, 0, 0, 0],
        "TARGET_STALE": [0, 1, 0, 0, 0, 1],
        "MODAL_BLOCKED": [0, 0, 1, 0, 0, 0],
        "APP_BUSY": [0, 0, 0, 1, 0, 1],
        "LAYOUT_CHANGED": [0, 0, 0, 0, 1, 0],
    }
    rows = []
    for mode in MODES:
        features = prototypes[mode]
        rows.append({"row_id": f"control:{seed}:FULL_DETERMINISTIC:{mode}",
                     "split": "control", "seed": seed, "block": "CONTROL",
                     "mode": mode, "features": features, "expected": DISPOSITION[mode]})
    rows.extend([
        {"row_id": f"control:{seed}:UNKNOWN_ALL_MISSING", "split": "control",
         "seed": seed, "block": "CONTROL", "mode": "UNKNOWN",
         "features": [None] * len(FEATURES), "expected": "YIELD"},
        {"row_id": f"control:{seed}:CONTRADICTORY", "split": "control",
         "seed": seed, "block": "CONTROL", "mode": "UNKNOWN",
         "features": [1] * len(FEATURES), "expected": "YIELD"},
    ])
    return rows


def fit(rows: list[dict], labels: tuple[str, ...], *, label_key: str) -> dict:
    counts = Counter(row[label_key] for row in rows)
    feature_ones = {label: [0] * len(FEATURES) for label in labels}
    feature_seen = {label: [0] * len(FEATURES) for label in labels}
    for row in rows:
        label = row[label_key]
        for j, value in enumerate(row["features"]):
            if value is not None:
                feature_seen[label][j] += 1
                feature_ones[label][j] += int(value)
    total = len(rows)
    return {"counts": dict(counts), "ones": feature_ones, "seen": feature_seen, "total": total}


def posterior(model: dict, labels: tuple[str, ...], features: list[int | None]) -> dict[str, float]:
    logs = {}
    for label in labels:
        n = model["counts"].get(label, 0)
        score = math.log((n + ALPHA) / (model["total"] + ALPHA * len(labels)))
        for j, value in enumerate(features):
            if value is None:
                continue
            seen = model["seen"][label][j]
            p1 = (model["ones"][label][j] + ALPHA) / (seen + 2 * ALPHA)
            p = p1 if value else 1.0 - p1
            score += math.log(p)
        logs[label] = score
    peak = max(logs.values())
    z = sum(math.exp(v - peak) for v in logs.values())
    return {key: math.exp(value - peak) / z for key, value in logs.items()}


def decide(probs: dict[str, float], key_to_action: dict[str, str]) -> dict:
    aggregated: dict[str, float] = {}
    for label, probability in probs.items():
        action = key_to_action[label]
        aggregated[action] = aggregated.get(action, 0.0) + probability
    ordered = sorted(aggregated.items(), key=lambda item: (-item[1], item[0]))
    action, confidence = ordered[0]
    margin = confidence - (ordered[1][1] if len(ordered) > 1 else 0.0)
    confident = confidence >= MIN_POSTERIOR and margin >= MIN_MARGIN
    return {"action": action if confident else "YIELD", "emitted": True,
            "abstained_to_yield": not confident,
            "confidence": round(confidence, 12), "margin": round(margin, 12),
            "posterior": {k: round(v, 12) for k, v in sorted(aggregated.items())}}


def predict(direct: dict, mode_model: dict, row: dict) -> dict:
    direct_p = posterior(direct, tuple(sorted(set(DISPOSITION.values()))), row["features"])
    mode_p = posterior(mode_model, MODES, row["features"])
    return {
        "direct": decide(direct_p, {a: a for a in sorted(set(DISPOSITION.values()))}),
        "mode": decide(mode_p, DISPOSITION),
    }


def make_formal(train_seeds: tuple[int, ...] = TRAIN_SEEDS,
                formal_seeds: tuple[int, ...] = FORMAL_SEEDS) -> dict:
    seeds = []
    blocks = ("COMPLETE", "SINGLE_MISSING", "MULTI_MISSING",
              "COMPOSITION_HOLDOUT", "NUISANCE_SHIFT")
    for index, seed in enumerate(formal_seeds):
        train = generate_rows(train_seeds[index], TRAIN_PER_MODE, split="support", block="COMPLETE")
        direct = fit(train, tuple(sorted(set(DISPOSITION.values()))), label_key="expected")
        mode_model = fit(train, MODES, label_key="mode")
        block_results = []
        for block in blocks:
            rows = generate_rows(seed, 64, split="heldout", block=block)
            evaluated = []
            for row in rows:
                evaluated.append({**row, "predictions": predict(direct, mode_model, row)})
            block_results.append({"name": block, "rows": evaluated})
        controls = [{**row, "predictions": predict(direct, mode_model, row)}
                    for row in generate_controls(seed)]
        seeds.append({"seed": seed, "support_seed": train_seeds[index],
                      "support_rows": len(train), "support_digest": digest(train),
                      "blocks": block_results, "controls": controls})
    return {"schema": "typed-mode-generalization-formal-v1", "issue": 4844,
            "allocation": "typed-mode-generalization-4155-v1", "seeds": seeds,
            "seed_schedule": {"support": list(train_seeds), "heldout": list(formal_seeds)},
            "policy": {"alpha": ALPHA, "minimum_posterior": MIN_POSTERIOR,
                       "minimum_margin": MIN_MARGIN, "mode_to_disposition": DISPOSITION},
            "disposition": {"FOCUS_LOST": "REBIND", "TARGET_STALE": "YIELD",
                            "MODAL_BLOCKED": "WAIT_OBSERVE", "APP_BUSY": "WAIT_OBSERVE",
                            "LAYOUT_CHANGED": "REOBSERVE"}}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: study.py OUTPUT.json", file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    if out.exists():
        print("output-exists", file=sys.stderr)
        return 3
    raw = make_formal()
    out.write_bytes(canonical(raw) + b"\n")
    print(json.dumps({"rows": sum(len(b["rows"]) for s in raw["seeds"] for b in s["blocks"]),
                      "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
