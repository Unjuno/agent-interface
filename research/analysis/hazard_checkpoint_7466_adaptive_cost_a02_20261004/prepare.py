#!/usr/bin/env python3
"""Deterministically materialize frozen public and oracle-only A02 fixtures."""
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRAIN_HIGH, TRAIN_LOW = 0.28, 0.02
HORIZON = 240


def stream(seed, n, family):
    rng = random.Random(seed)
    phase = seed % 10
    signals = ["HIGH" if (t + phase) % 10 in (4, 5) else "LOW" for t in range(n)]
    labels = []
    for symbol in signals:
        if family == "informative":
            p = TRAIN_HIGH if symbol == "HIGH" else TRAIN_LOW
        elif family == "independent":
            p = 0.10
        elif family == "reversed":
            p = TRAIN_LOW if symbol == "HIGH" else TRAIN_HIGH
        else:
            raise ValueError(family)
        labels.append(int(rng.random() < p))
    return signals, labels


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


train = []
for i in range(64):
    sig, lab = stream(1000 + i, 96, "informative")
    train.extend({"symbol": s, "interrupted": y} for s, y in zip(sig, lab))
validation = []
for i in range(32):
    sig, lab = stream(2000 + i, 96, "informative")
    validation.extend({"symbol": s, "interrupted": y} for s, y in zip(sig, lab))

public_cases, oracle_cases = [], []
for cohort in ("informative", "independent", "reversed"):
    for i in range(24):
        seed = 10000 + i
        sig, lab = stream(seed, HORIZON, cohort)
        opaque = hashlib.sha256(f"7466-a02-{cohort}-{seed}".encode()).hexdigest()[:16]
        public_cases.append({
            "episode_id": opaque,
            "signals": sig,
            "legal": [int(t % 2 == 0) for t in range(HORIZON)],
            "task_units": 60,
            "horizon": HORIZON,
        })
        oracle_cases.append({"episode_id": opaque, "cohort": cohort, "interruptions": lab})

write_json(ROOT / "training.json", {"fit": train, "validation": validation})
write_json(ROOT / "public.json", {"episodes": public_cases, "checkpoint_costs": [1, 2, 4], "replay_costs": [1, 3], "fixed_interval": 8, "task_event_interval": 10})
write_json(ROOT / "oracle.json", {"episodes": oracle_cases})
print(json.dumps({
    "training_observations": len(train),
    "validation_observations": len(validation),
    "heldout_episodes": len(public_cases),
    "oracle_episodes": len(oracle_cases),
    "public_sha256": hashlib.sha256((ROOT / "public.json").read_bytes()).hexdigest(),
    "oracle_sha256": hashlib.sha256((ROOT / "oracle.json").read_bytes()).hexdigest(),
}, sort_keys=True))
