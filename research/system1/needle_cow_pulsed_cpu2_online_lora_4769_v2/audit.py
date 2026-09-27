"""Independent raw-only replay/auditor; deliberately does not import runner.py."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.use_deterministic_algorithms(True)

SEEDS = (91004321, 91004531, 91004749)
ARMS = {"CPU2_CONTINUOUS": 2, "CPU2_PULSED": 2}
ARRIVALS, BATCH, STEPS, QUERIES, PERIOD_NS = 12, 512, 16, 120, 16_666_667
PULSE_AFTER_QUERY_INDICES = tuple(10 * i for i in range(ARRIVALS))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def tensor(value):
    return torch.tensor(value, dtype=torch.float32)


def floats(value):
    return value.detach().cpu().tolist()


def regenerate(seed):
    """Independent reconstruction of generator, teacher labels, and init."""
    g = torch.Generator(device="cpu").manual_seed(seed)
    w1 = torch.randn((16, 8), generator=g) * 0.22
    b1 = torch.randn((16,), generator=g) * 0.04
    w2 = torch.randn((4, 16), generator=g) * 0.16
    b2 = torch.randn((4,), generator=g) * 0.02
    teacher = torch.randn((4, 8), generator=g)
    teacher_b = torch.randn((4,), generator=g) * 0.1
    support_x = torch.randn((ARRIVALS, BATCH, 8), generator=g)
    query_x = torch.randn((QUERIES, 8), generator=g)
    support_y = (support_x @ teacher.T + teacher_b).argmax(dim=2)
    query_y = (query_x @ teacher.T + teacher_b).argmax(dim=1)
    a = torch.randn((2, 16), generator=g) * 0.025
    b = torch.zeros((4, 2))
    base = {"w1": floats(w1), "b1": floats(b1), "w2": floats(w2), "b2": floats(b2)}
    task = {"support_x": floats(support_x), "support_y": support_y.tolist(),
            "query_x": floats(query_x), "query_y": query_y.tolist(),
            "teacher": floats(teacher), "teacher_b": floats(teacher_b)}
    return base, task, {"a": floats(a), "b": floats(b)}


def oracle(base, adapter, x):
    query = tensor(x).unsqueeze(0)
    hidden = torch.tanh(F.linear(query, tensor(base["w1"]), tensor(base["b1"])))
    effective = tensor(base["w2"]) + tensor(adapter["b"]) @ tensor(adapter["a"])
    logits = F.linear(hidden, effective, tensor(base["b2"]))[0]
    if logits.ndim != 1 or logits.numel() != 4:
        raise ValueError("oracle_shape")
    return logits


def valid_logits(logits):
    return isinstance(logits, torch.Tensor) and logits.ndim == 1 and logits.numel() == 4


def available_snapshot(published, version):
    if not isinstance(version, int) or str(version) not in published:
        raise ValueError("unknown_or_stale_version")
    return published[str(version)]


def replay_training(base, task, initial, raw_steps):
    """Recompute all 192 optimizer updates and each durable COW publication."""
    a = tensor(initial["a"]).requires_grad_(True)
    b = tensor(initial["b"]).requires_grad_(True)
    optimizer = torch.optim.AdamW([a, b], lr=0.035, weight_decay=0.0)
    sx = tensor(task["support_x"])
    sy = torch.tensor(task["support_y"], dtype=torch.long)
    snapshots = {"0": {"version": 0, "a": floats(a), "b": floats(b)}}
    replayed_losses = []
    for arrival in range(ARRIVALS):
        for _ in range(STEPS):
            optimizer.zero_grad(set_to_none=True)
            hidden = torch.tanh(F.linear(sx[arrival], tensor(base["w1"]), tensor(base["b1"])))
            logits = F.linear(hidden, tensor(base["w2"]) + b @ a, tensor(base["b2"]))
            loss = F.cross_entropy(logits, sy[arrival])
            loss.backward()
            optimizer.step()
            replayed_losses.append(float(loss.detach()))
        version = arrival + 1
        snapshots[str(version)] = {"version": version, "a": floats(a), "b": floats(b)}
    if len(raw_steps) != len(replayed_losses):
        raise ValueError("training_step_count")
    for logged, expected in zip(raw_steps, replayed_losses):
        if not math.isclose(logged["loss"], expected, rel_tol=0, abs_tol=0):
            raise ValueError(f"training_loss_replay:{logged.get('update')}")
    return snapshots


def snapshot_digest(item):
    state = {"version": item["version"], "a": item["a"], "b": item["b"]}
    return digest(state)


def identity_errors(raw, path, seed, arm):
    errors = []
    if raw.get("seed") != seed or raw.get("arm") != arm:
        errors.append("seed_or_arm_identity")
    if Path(path).name != f"seed_{seed}_{arm.lower()}.json":
        errors.append("filename_identity")
    return errors


def check_cell(path, seed, arm):
    raw = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    expected_cpus = ARMS[arm]
    if raw.get("schema") != "needle-cow-pulsed-cpu2.raw.v1":
        errors.append("schema")
    errors.extend(identity_errors(raw, path, seed, arm))
    if raw.get("expected_cpus") != expected_cpus or expected_cpus != 2 or not math.isclose(
            raw.get("cpu_quota", {}).get("quota_cores", -1), expected_cpus, abs_tol=1e-9):
        errors.append("cpu_quota_identity")
    if raw.get("torch_threads") != {"intraop": 1, "interop": 1}:
        errors.append("thread_identity")
    if raw.get("authority") is not False or raw.get("action_emissions") != 0:
        errors.append("authority_or_effect")
    base, task, initial = regenerate(seed)
    if raw.get("base") != base or raw.get("base_sha256") != digest(base) or raw.get("immutable_base_after_sha256") != digest(base):
        errors.append("base_reconstruction_or_immutability")
    if raw.get("task") != task or raw.get("initial") != initial:
        errors.append("seeded_data_or_initialization")
    if raw.get("constants") != {"arrivals": ARRIVALS, "steps_per_arrival": STEPS,
                                "batch": BATCH, "queries": QUERIES, "period_ns": PERIOD_NS}:
        errors.append("constants")
    expected_pulses = list(PULSE_AFTER_QUERY_INDICES) if arm == "CPU2_PULSED" else []
    if raw.get("pulse_after_query_indices") != expected_pulses:
        errors.append("pulse_schedule")
    arrival_schedule = raw.get("arrival_schedule", [])
    if len(arrival_schedule) != ARRIVALS:
        errors.append("arrival_schedule_count")
    query_rows = raw.get("queries", [])
    for ix, event in enumerate(arrival_schedule):
        expected_trigger = PULSE_AFTER_QUERY_INDICES[ix] if arm == "CPU2_PULSED" else None
        expected_trigger_end = (query_rows[expected_trigger].get("end_ns")
                                 if expected_trigger is not None and len(query_rows) > expected_trigger else None)
        if (event.get("arrival") != ix + 1 or event.get("first_update") != ix * STEPS + 1
                or event.get("last_update") != (ix + 1) * STEPS
                or event.get("trigger_query_index") != expected_trigger
                or event.get("trigger_query_end_ns") != expected_trigger_end
                or not isinstance(event.get("training_start_ns"), int)
                or not isinstance(event.get("training_end_ns"), int)
                or not isinstance(event.get("published_ns"), int)
                or event["training_start_ns"] > event["training_end_ns"]
                or event["training_end_ns"] > event["published_ns"]
                or (expected_trigger is not None and event["training_start_ns"] < expected_trigger_end)):
            errors.append(f"arrival_schedule:{ix}")
    raw_steps = raw.get("training_steps", [])
    if len(raw_steps) != ARRIVALS * STEPS or raw.get("worker_errors"):
        errors.append("training_count_or_worker_error")
    try:
        expected_states = replay_training(base, task, initial, raw_steps)
    except Exception as exc:
        expected_states = {}
        errors.append(f"independent_training_replay:{type(exc).__name__}:{exc}")
    published = raw.get("published", {})
    if set(published) != set(expected_states):
        errors.append("published_version_set")
    for version, expected in expected_states.items():
        item = published.get(version)
        if not item or snapshot_digest(item) != item.get("sha256"):
            errors.append(f"snapshot_digest:{version}")
        elif item.get("version") != expected["version"] or item.get("a") != expected["a"] or item.get("b") != expected["b"]:
            errors.append(f"snapshot_training_replay:{version}")
    intervals = raw.get("training_intervals", [])
    if len(intervals) != ARRIVALS * STEPS or any(len(x) != 2 or x[1] is None or x[0] >= x[1] for x in intervals):
        errors.append("interval_count_or_bounds")
    if len(raw_steps) == ARRIVALS * STEPS:
        for index, (record, interval) in enumerate(zip(raw_steps, intervals)):
            expected_arrival = index // STEPS + 1
            if (record.get("update") != index + 1 or record.get("arrival") != expected_arrival
                    or record.get("start_ns") != interval[0] or record.get("end_ns") != interval[1]):
                errors.append(f"step_interval_binding:{index}")
    rows = query_rows
    if len(rows) != QUERIES:
        errors.append("query_count")
    origin = raw.get("query_origin_ns")
    if not isinstance(origin, int):
        errors.append("query_origin_missing")
    correct, overlap_count, misses, latencies = 0, 0, 0, []
    previous_version = 0
    for index, row in enumerate(rows):
        scheduled = origin + index * PERIOD_NS if isinstance(origin, int) else None
        if (row.get("index") != index or row.get("scheduled_ns") != scheduled
                or row.get("deadline_ns") != (scheduled + PERIOD_NS if scheduled is not None else None)
                or row.get("x") != task["query_x"][index] or row.get("label") != task["query_y"][index]):
            errors.append(f"query_binding:{index}")
            continue
        begin, end = row.get("start_ns"), row.get("end_ns")
        if row.get("latency_ns") != end - begin or row.get("deadline_miss") != (end > row["deadline_ns"]):
            errors.append(f"query_timing:{index}")
        actual_overlap = any(a < end and b > begin for a, b in intervals if b is not None)
        if row.get("train_interval_overlap") != actual_overlap:
            errors.append(f"query_overlap:{index}")
        overlap_count += int(actual_overlap)
        misses += int(row.get("deadline_miss", False))
        latencies.append(row["latency_ns"] / 1e6)
        version = row.get("version_before")
        if (not isinstance(version, int) or version != row.get("version_after")
                or version < previous_version or str(version) not in published):
            errors.append(f"query_version:{index}")
            continue
        previous_version = version
        try:
            selected = available_snapshot(published, version)
            recomputed = oracle(base, selected, row["x"])
            actual = torch.tensor(row["logits"], dtype=torch.float32)
            if not valid_logits(actual) or not torch.equal(recomputed, actual):
                errors.append(f"proposal_recompute:{index}")
            else:
                correct += int(int(torch.argmax(actual)) == row["label"])
        except Exception as exc:
            errors.append(f"proposal_recompute_exception:{index}:{type(exc).__name__}")
    return {"seed": seed, "arm": arm, "cpu_quota": raw.get("cpu_quota"),
            "queries": len(rows), "updates": len(raw_steps), "accuracy": correct / max(1, len(rows)),
            "overlap_queries": overlap_count, "deadline_misses": misses,
            "p50_ms": percentile(latencies, .50), "p95_ms": percentile(latencies, .95),
            "errors": errors, "snapshots": published}


def percentile(values, q):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)] if ordered else None


def audit(raw_root, output):
    root = Path(raw_root)
    expected_files = {f"seed_{seed}_{arm.lower()}.json" for seed in SEEDS for arm in ARMS}
    raw_files = list(root.rglob("seed_*.json"))
    present_files = {p.name for p in raw_files}
    errors = []
    if present_files != expected_files:
        errors.append("formal_file_set")
    cells = []
    for seed in SEEDS:
        for arm in ARMS:
            matches = [p for p in raw_files if p.name == f"seed_{seed}_{arm.lower()}.json"]
            if len(matches) == 1:
                try:
                    cells.append(check_cell(matches[0], seed, arm))
                except Exception as exc:
                    cells.append({"seed": seed, "arm": arm, "cpu_quota": None,
                                  "queries": 0, "updates": 0, "accuracy": 0.0,
                                  "overlap_queries": 0, "deadline_misses": 0,
                                  "p50_ms": None, "p95_ms": None,
                                  "errors": [f"auditor_exception:{type(exc).__name__}:{exc}"],
                                  "snapshots": {}})
            elif len(matches) > 1:
                errors.append(f"duplicate_raw:{seed}:{arm}")
    by_pair = {}
    for cell in cells:
        by_pair.setdefault(cell["seed"], {})[cell["arm"]] = cell
    for seed, pair in by_pair.items():
        if set(pair) != set(ARMS):
            errors.append(f"paired_cells:{seed}")
            continue
        left = pair["CPU2_CONTINUOUS"]["snapshots"]
        right = pair["CPU2_PULSED"]["snapshots"]
        if any(left[v].get("a") != right[v].get("a") or left[v].get("b") != right[v].get("b") for v in left if v in right):
            errors.append(f"cpu_treatment_changed_training_path:{seed}")
    errors.extend(f"{cell['seed']}:{cell['arm']}:{error}" for cell in cells for error in cell["errors"])
    cpu2 = [c for c in cells if c["arm"] == "CPU2_PULSED"]
    all_integrity = len(cells) == len(expected_files) and not errors
    all_pressure = len(cpu2) == len(SEEDS) and all(c["overlap_queries"] >= 8 for c in cpu2)
    all_latency = len(cpu2) == len(SEEDS) and all(c["p95_ms"] is not None and c["p95_ms"] <= 16.67 for c in cpu2)
    all_deadlines = len(cpu2) == len(SEEDS) and all(c["deadline_misses"] == 0 for c in cpu2)
    if not all_integrity:
        decision = "STOP_SEED_OR_VERSION_PROVENANCE"
    elif not all_pressure:
        decision = "HOLD_NO_CONCURRENCY_PRESSURE"
    elif not all_latency or not all_deadlines:
        decision = "HOLD_LATENCY_BUDGET"
    else:
        decision = "PASS_COW_PULSED_SCHEDULING_SCOPED"
    report = {"schema": "needle-cow-pulsed-cpu2.audit.v1",
              "allocation": "needle-cow-pulsed-cpu2-online-lora-4769-v2-20260928",
              "decision": decision, "integrity_pass": all_integrity, "errors": errors,
              "gates": {"audit_zero_errors": all_integrity, "cpu2_overlap_min_8": all_pressure,
                        "cpu2_p95_le_16_67ms": all_latency, "cpu2_deadline_misses_zero": all_deadlines},
              "cells": [{k: v for k, v in c.items() if k != "snapshots"} for c in cells]}
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_bytes(canonical(report) + b"\n")
    print(json.dumps({"decision": decision, "cells": len(cells), "errors": len(errors),
                      "cpu2_overlap": [c["overlap_queries"] for c in cpu2],
                      "cpu2_p95_ms": [c["p95_ms"] for c in cpu2],
                      "cpu2_deadline_misses": [c["deadline_misses"] for c in cpu2]}, sort_keys=True), flush=True)
    if not all_integrity:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    audit(args.raw, args.out)
