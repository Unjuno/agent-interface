"""Frozen synthetic confidence-trajectory System-1 training/evaluation runner."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import time

import torch
from torch import nn

SEEDS = list(range(2026100100, 2026101001, 100))
FAMILIES = ["mono_a", "mono_b", "alias_accel", "plateau_noop", "self_correct_noop",
            "uncertain_yield", "stale_yield", "oscillation_yield", "spike_yield", "required_action"]
ARMS = {
    "CURRENT_ONLY": [0, 1, 6, 7, 8],
    "LEVEL_VELOCITY": [0, 1, 2, 3, 6, 7, 8],
    "LEVEL_VELOCITY_ACCEL": list(range(9)),
    "CAUSAL_SMOOTHED": [0, 1, 2, 3, 4, 5, 6, 7, 8],
}
CLASS_NAMES = ["ACTION_A", "ACTION_B", "NO_OP", "YIELD"]
GROUP = {
    "mono_a": "action", "mono_b": "action", "alias_accel": "alias",
    "plateau_noop": "noop", "self_correct_noop": "noop", "uncertain_yield": "yield",
    "stale_yield": "invalid", "oscillation_yield": "noise", "spike_yield": "noise",
    "required_action": "required",
}


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def example(rng, seed, split, family, index):
    noise = rng.uniform(-0.018, 0.018)
    irregular = rng.choice([0.5, 1.0, 1.5, 2.0])
    dt0 = rng.choice([0.5, 1.0, 1.5, 2.0]) if rng.random() < 0.35 else 1.0
    dt1 = irregular
    pA = [0.4, 0.4, 0.4]
    pB = [0.4, 0.4, 0.4]
    progress, valid, label = 0.0, 1.0, 3
    alias_id = None
    if family == "mono_a":
        pA, pB, label = [0.56, 0.68, 0.82], [0.36, 0.31, 0.25], 0
    elif family == "mono_b":
        pA, pB, label = [0.36, 0.31, 0.25], [0.56, 0.68, 0.82], 1
    elif family == "alias_accel":
        dt0 = dt1 = 1.0
        pair = index // 2
        alias_id = f"{split}-{seed}-{pair}"
        if index % 2 == 0:
            pA, pB, progress, label = [0.38, 0.44, 0.50], [0.30, 0.34, 0.38], 0.15, 0
        else:
            pA, pB, progress, label = [0.34, 0.44, 0.50], [0.30, 0.34, 0.38], 0.15, 2
        noise = 0.0
    elif family == "plateau_noop":
        pA, pB, progress, label = [0.63, 0.63, 0.63], [0.51, 0.51, 0.51], 0.65, 2
    elif family == "self_correct_noop":
        pA, pB, progress, label = [0.68, 0.74, 0.79], [0.30, 0.27, 0.23], 0.92, 2
    elif family == "uncertain_yield":
        pA, pB, progress, label = [0.31, 0.34, 0.35], [0.30, 0.32, 0.34], 0.05, 3
    elif family == "stale_yield":
        pA, pB, progress, valid, label = [0.42, 0.58, 0.79], [0.5, 0.4, 0.3], 0.1, 0.0, 3
    elif family == "oscillation_yield":
        pA, pB, progress, label = [0.32, 0.76, 0.38], [0.70, 0.28, 0.66], 0.05, 3
    elif family == "spike_yield":
        pA, pB, progress, label = [0.36, 0.48, 0.88], [0.35, 0.42, 0.40], 0.05, 3
    elif family == "required_action":
        pA, pB, progress, label = [0.45, 0.60, 0.78], [0.31, 0.29, 0.27], 0.03, 0
    else:
        raise ValueError("unknown family")
    if noise:
        pA = [max(0.01, min(0.99, x + rng.uniform(-noise, noise))) for x in pA]
        pB = [max(0.01, min(0.99, x + rng.uniform(-noise, noise))) for x in pB]
    vA = (pA[2] - pA[1]) / dt1
    vA0 = (pA[1] - pA[0]) / dt0
    vB = (pB[2] - pB[1]) / dt1
    vB0 = (pB[1] - pB[0]) / dt0
    accelA = (vA - vA0) / ((dt0 + dt1) / 2)
    accelB = (vB - vB0) / ((dt0 + dt1) / 2)
    smoothA = 0.5 * vA + 0.5 * vA0
    smoothB = 0.5 * vB + 0.5 * vB0
    features = [pA[2], pB[2], vA, vB, accelA, accelB, progress, valid, dt1 / 2.0]
    smoothed = [pA[2], pB[2], vA, vB, smoothA, smoothB, progress, valid, dt1 / 2.0]
    if noise:
        features = [x + rng.uniform(-0.005, 0.005) if i < 6 else x for i, x in enumerate(features)]
        smoothed = [x + rng.uniform(-0.005, 0.005) if i < 6 else x for i, x in enumerate(smoothed)]
    history_status = (rng.choice(["stale", "missing", "epoch_mismatch"]) if family == "stale_yield" else "current")
    stress = (family in ("oscillation_yield", "spike_yield") or dt0 != 1.0 or dt1 != 1.0 or
              (family == "alias_accel" and index % 2 == 1))
    return {"seed": seed, "split": split, "family": family, "group": GROUP[family],
            "index": index, "alias_id": alias_id, "history_A": pA, "history_B": pB,
            "dt": [dt0, dt1], "features": features, "smoothed_features": smoothed,
            "history_status": history_status, "stress": stress,
            "label": label, "class_name": CLASS_NAMES[label]}


def dataset(seed, split):
    rng = random.Random(seed * 1009 + (13 if split == "train" else 29))
    rows = []
    regular = 160 if split == "train" else 80
    aliases = regular * 2
    for family in FAMILIES:
        count = aliases if family == "alias_accel" else regular
        rows.extend(example(rng, seed, split, family, i) for i in range(count))
    rng.shuffle(rows)
    return rows


def metric(y, pred):
    n = len(y)
    nonexec = [i for i, z in enumerate(y) if z in (2, 3)]
    noop = [i for i, z in enumerate(y) if z == 2]
    required = [i for i, z in enumerate(y) if z in (0, 1)]
    false_exec = sum(pred[i] in (0, 1) for i in nonexec)
    unnecessary = sum(pred[i] in (0, 1) for i in noop)
    false_noop = sum(pred[i] == 2 for i in required)
    return {"accuracy": sum(a == b for a, b in zip(y, pred)) / n,
            "false_executable_rate": false_exec / max(1, len(nonexec)),
            "unnecessary_action_rate": unnecessary / max(1, len(noop)),
            "false_noop_required_rate": false_noop / max(1, len(required)),
            "rows": n}


def row_metrics(rows, pred):
    all_m = metric([r["label"] for r in rows], pred)
    subsets = {}
    for name, keep in {
        "alias": lambda r: r["group"] == "alias",
        "stress": lambda r: r["stress"],
        "noop": lambda r: r["label"] == 2,
        "required": lambda r: r["label"] in (0, 1),
        "invalid": lambda r: r["history_status"] != "current",
    }.items():
        idx = [i for i, row in enumerate(rows) if keep(row)]
        if idx:
            subsets[name] = metric([rows[i]["label"] for i in idx], [pred[i] for i in idx])
    return {"overall": all_m, "subgroups": subsets}


def train_arm(seed, arm, train_rows, test_rows):
    ids = ARMS[arm]
    x = torch.tensor([[(r["smoothed_features"] if arm == "CAUSAL_SMOOTHED" else r["features"])[j]
                       if j in ids else 0.0 for j in range(9)] for r in train_rows], dtype=torch.float32)
    y = torch.tensor([r["label"] for r in train_rows], dtype=torch.long)
    torch.manual_seed(seed + 701)
    model = nn.Linear(9, 4)
    initial = {k: v.detach().clone() for k, v in model.state_dict().items()}
    opt = torch.optim.AdamW(model.parameters(), lr=0.025, weight_decay=0.001)
    generator = torch.Generator().manual_seed(seed + 1701)
    order = torch.randperm(len(y), generator=generator)
    start = time.perf_counter_ns()
    for step in range(180):
        take = order[(step * 128) % len(y): (step * 128) % len(y) + 128]
        if len(take) < 128:
            take = torch.cat((take, order[:128 - len(take)]))
        logits = model(x[take])
        loss = nn.functional.cross_entropy(logits, y[take])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    elapsed_ms = (time.perf_counter_ns() - start) / 1e6
    tx = torch.tensor([[(r["smoothed_features"] if arm == "CAUSAL_SMOOTHED" else r["features"])[j]
                        if j in ids else 0.0 for j in range(9)] for r in test_rows], dtype=torch.float32)
    with torch.no_grad():
        logits = model(tx)
        pred = logits.argmax(dim=1).tolist()
        decision_latencies_ms = []
        for i in range(len(tx)):
            tick = time.perf_counter_ns()
            model(tx[i:i + 1])
            decision_latencies_ms.append((time.perf_counter_ns() - tick) / 1e6)
    # History validity is a hard, common fail-closed gate, not learned authority.
    for i, row in enumerate(test_rows):
        if row["history_status"] != "current":
            pred[i] = 3
    ytest = [r["label"] for r in test_rows]
    state = {k: v.detach().cpu().tolist() for k, v in model.state_dict().items()}
    initial_state = {k: v.cpu().tolist() for k, v in initial.items()}
    ordered_latency = sorted(decision_latencies_ms)
    p95_index = max(0, math.ceil(0.95 * len(ordered_latency)) - 1)
    p50_index = max(0, math.ceil(0.50 * len(ordered_latency)) - 1)
    return {"metrics": row_metrics(test_rows, pred), "elapsed_train_ms": elapsed_ms,
            "decision_latency_ms": decision_latencies_ms,
            "decision_latency_p50_ms": ordered_latency[p50_index],
            "decision_latency_p95_ms": ordered_latency[p95_index],
            "state_bytes": len(canonical(state)),
            "predictions": pred, "logits": logits.tolist(), "state": state,
            "initial_state": initial_state, "feature_indices": ids}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_MUST_BE_PRECREATED_EMPTY")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    results = {"schema": "confidence-trajectory-run-v1", "seeds": [],
               "torch": torch.__version__, "threads": torch.get_num_threads()}
    for seed in SEEDS:
        train_rows, test_rows = dataset(seed, "train"), dataset(seed, "test")
        arm_results = {}
        for arm in ARMS:
            arm_results[arm] = train_arm(seed, arm, train_rows, test_rows)
        seed_doc = {"seed": seed, "train_rows": train_rows, "test_rows": test_rows,
                    "arms": arm_results}
        seed_dir = out / f"seed-{seed}"
        seed_dir.mkdir()
        raw = canonical(seed_doc) + b"\n"
        (seed_dir / "evidence.json").write_bytes(raw)
        results["seeds"].append({"seed": seed, "rows_train": len(train_rows),
                                  "rows_test": len(test_rows), "evidence_sha256": sha(raw),
                                  "evidence_bytes": len(raw),
                                  "metrics": {a: arm_results[a]["metrics"] for a in ARMS},
                                  "elapsed_train_ms": {a: arm_results[a]["elapsed_train_ms"] for a in ARMS},
                                  "decision_latency_p50_ms": {a: arm_results[a]["decision_latency_p50_ms"] for a in ARMS},
                                  "decision_latency_p95_ms": {a: arm_results[a]["decision_latency_p95_ms"] for a in ARMS},
                                  "state_bytes": {a: arm_results[a]["state_bytes"] for a in ARMS}})
    raw = canonical(results) + b"\n"
    (out / "RUN.json").write_bytes(raw)
    print(json.dumps({"seeds": len(results["seeds"]), "rows": sum(x["rows_test"] for x in results["seeds"]),
                      "run_sha256": sha(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()

