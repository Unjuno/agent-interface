#!/usr/bin/env python3
"""Frozen synthetic concurrent Needle LoRA/System-1 workload; no action I/O."""
import argparse
import hashlib
import json
import threading
import time
from pathlib import Path

import torch
import torch.nn.functional as F

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.use_deterministic_algorithms(True)
PERIOD_NS = 16_666_667
SEEDS = (88117, 88229, 88301)
ARRIVALS = 12
STEPS_PER_ARRIVAL = 16
QUERIES = 120
BATCH = 128


def digest_obj(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def floats(t):
    return t.detach().cpu().tolist()


def tensor(x):
    return torch.tensor(x, dtype=torch.float32)


def make_seed(seed):
    g = torch.Generator(device="cpu").manual_seed(seed)
    w1 = torch.randn((16, 8), generator=g) * 0.22
    b1 = torch.randn((16,), generator=g) * 0.04
    w2 = torch.randn((4, 16), generator=g) * 0.16
    b2 = torch.randn((4,), generator=g) * 0.02
    teacher = torch.randn((4, 8), generator=g)
    teacher_b = torch.randn((4,), generator=g) * 0.1
    supports = torch.randn((ARRIVALS, BATCH, 8), generator=g)
    queries = torch.randn((QUERIES, 8), generator=g)
    support_y = (supports @ teacher.T + teacher_b).argmax(dim=2)
    query_y = (queries @ teacher.T + teacher_b).argmax(dim=1)
    a = torch.randn((2, 16), generator=g) * 0.025
    b = torch.zeros((4, 2))
    base = {"w1": floats(w1), "b1": floats(b1), "w2": floats(w2), "b2": floats(b2)}
    base_sha = digest_obj(base)
    task = {"support_x": floats(supports), "support_y": support_y.tolist(),
            "query_x": floats(queries), "query_y": query_y.tolist(),
            "teacher": floats(teacher), "teacher_b": floats(teacher_b)}
    initial = {"a": floats(a), "b": floats(b)}
    return base, task, initial, base_sha


def predict(base, a, b, xs):
    h = torch.tanh(F.linear(xs, tensor(base["w1"]), tensor(base["b1"])))
    w = tensor(base["w2"]) + b @ a
    return F.linear(h, w, tensor(base["b2"]))


def train_step(base, a, b, x, y, optimizer):
    optimizer.zero_grad(set_to_none=True)
    logits = predict(base, a, b, x)
    loss = F.cross_entropy(logits, y)
    loss.backward()
    optimizer.step()
    return float(loss.detach())


def snapshot(a, b, version):
    item = {"version": int(version), "a": floats(a), "b": floats(b)}
    item["sha256"] = digest_obj(item)
    return item


def intervals_overlap(start, end, intervals):
    now = time.perf_counter_ns()
    return any(lo < end and (hi if hi is not None else now) > start for lo, hi in intervals)


def atomic_publish(cell, lock, item):
    with lock:
        cell["current"] = item


def capture_active(cell, lock):
    with lock:
        return cell["current"]


def advance_generation(cell, lock):
    with lock:
        cell["value"] += 1
        return cell["value"]


def generation_is_stable(before, after):
    return before == after and before % 2 == 0


def run_arm(seed, arm, base, task, initial, base_sha):
    a0, b0 = tensor(initial["a"]), tensor(initial["b"])
    immutable_base = json.loads(json.dumps(base))
    active_lock = threading.Lock()
    gen_lock = threading.Lock()
    active = {"current": {"version": 0, "a": a0.clone(), "b": b0.clone()}}
    published = {"0": snapshot(a0, b0, 0)}
    generation = {"value": 0}
    train_intervals = []
    train_lock = threading.Lock()
    losses = []
    worker_error = []
    start_gate = threading.Event()
    stop_gate = threading.Event()
    xq = tensor(task["query_x"])
    yq = task["query_y"]

    if arm == "BASELINE":
        a_live, b_live = a0.clone(), b0.clone()
    else:
        a_live, b_live = a0.clone().requires_grad_(True), b0.clone().requires_grad_(True)

    def record_interval(begin, finish):
        with train_lock:
            train_intervals.append([begin, finish])

    def begin_interval(begin):
        with train_lock:
            train_intervals.append([begin, None])
            return len(train_intervals) - 1

    def end_interval(index, finish):
        with train_lock:
            train_intervals[index][1] = finish

    def training_worker():
        try:
            if not start_gate.wait(5):
                raise RuntimeError("start gate timeout")
            wa = a0.clone().requires_grad_(True)
            wb = b0.clone().requires_grad_(True)
            opt = torch.optim.AdamW([wa, wb], lr=0.035, weight_decay=0.0)
            sx, sy = tensor(task["support_x"]), torch.tensor(task["support_y"], dtype=torch.long)
            update = 0
            for arrival in range(ARRIVALS):
                for _ in range(STEPS_PER_ARRIVAL):
                    begin = time.perf_counter_ns()
                    interval_id = begin_interval(begin)
                    loss = train_step(base, wa, wb, sx[arrival], sy[arrival], opt)
                    finish = time.perf_counter_ns()
                    losses.append({"arrival": arrival + 1, "update": update + 1, "loss": loss,
                                   "start_ns": begin, "end_ns": finish})
                    update += 1
                    if arm == "SHARED_LIVE":
                        advance_generation(generation, gen_lock)  # odd: writer owns shared tensors
                        with torch.no_grad():
                            a_live.copy_(wa)
                            b_live.copy_(wb)
                        v = (generation["value"] + 1) // 2
                        published[str(v)] = snapshot(a_live, b_live, v)
                        advance_generation(generation, gen_lock)  # even: complete generation
                        finish = time.perf_counter_ns()
                        losses[-1]["end_ns"] = finish
                    end_interval(interval_id, finish)
                if arm == "COW":
                    item = {"version": arrival + 1, "a": wa.detach().clone(), "b": wb.detach().clone()}
                    atomic_publish(active, active_lock, item)
                    published[str(arrival + 1)] = snapshot(wa, wb, arrival + 1)
        except BaseException as exc:  # captured as formal evidence, never retried
            worker_error.append(repr(exc))
        finally:
            stop_gate.set()

    worker = None
    if arm != "BASELINE":
        worker = threading.Thread(target=training_worker, name=f"trainer-{seed}-{arm}", daemon=False)
        worker.start()

    records = []
    t0 = time.perf_counter_ns()
    start_gate.set()
    for i in range(QUERIES):
        scheduled = t0 + i * PERIOD_NS
        while True:
            now = time.perf_counter_ns()
            if now >= scheduled:
                break
            time.sleep(min((scheduled - now) / 1e9, 0.002))
        begin = time.perf_counter_ns()
        if arm == "COW":
            item = capture_active(active, active_lock)
            before = after = item["version"]
            a, b = item["a"], item["b"]
        elif arm == "SHARED_LIVE":
            before = generation["value"]
            with torch.no_grad():
                logits_t = predict(base, a_live, b_live, xq[i:i+1])
            after = generation["value"]
            logits = logits_t[0].tolist()
            end = time.perf_counter_ns()
            with train_lock:
                overlapped = intervals_overlap(begin, end, train_intervals)
            records.append({"index": i, "scheduled_ns": scheduled, "start_ns": begin,
                "end_ns": end, "latency_ns": end-begin, "deadline_ns": scheduled+PERIOD_NS,
                "deadline_miss": end > scheduled+PERIOD_NS, "x": task["query_x"][i],
                "label": yq[i], "logits": logits, "generation_before": before,
                "generation_after": after, "writer_overlap": (before != after or before % 2 == 1),
                "train_interval_overlap": overlapped})
            continue
        else:
            item = published["0"]
            before = after = item["version"]
            a, b = a0, b0
        with torch.no_grad():
            logits_t = predict(base, a, b, xq[i:i+1])
        end = time.perf_counter_ns()
        with train_lock:
            overlapped = intervals_overlap(begin, end, train_intervals)
        logits = logits_t[0].tolist()
        records.append({"index": i, "scheduled_ns": scheduled, "start_ns": begin,
            "end_ns": end, "latency_ns": end-begin, "deadline_ns": scheduled+PERIOD_NS,
            "deadline_miss": end > scheduled+PERIOD_NS, "x": task["query_x"][i],
            "label": yq[i], "logits": logits, "version_before": before,
            "version_after": after, "train_interval_overlap": overlapped})
    if worker is not None:
        worker.join(timeout=20)
        if worker.is_alive():
            worker_error.append("worker join timeout")
    with train_lock:
        intervals = list(train_intervals)
    result = {"schema": "needle-concurrent-online-lora.raw.v1", "seed": seed, "arm": arm,
        "constants": {"arrivals": ARRIVALS, "steps_per_arrival": STEPS_PER_ARRIVAL,
                      "queries": QUERIES, "period_ns": PERIOD_NS, "batch": BATCH},
        "base": base, "base_sha256": base_sha, "immutable_base_after_sha256": digest_obj(immutable_base),
        "task": task, "initial": initial, "published": published, "queries": records,
        "training_steps": losses, "training_intervals": intervals, "worker_errors": worker_error,
        "training_finished_before_query_loop_end": stop_gate.is_set(),
        "authority": False, "action_emissions": 0}
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for seed in SEEDS:
        base, task, initial, base_sha = make_seed(seed)
        for arm in ("BASELINE", "COW", "SHARED_LIVE"):
            result = run_arm(seed, arm, base, task, initial, base_sha)
            path = out / f"seed_{seed}_{arm.lower()}.json"
            path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n", encoding="utf-8")
            print(json.dumps({"seed": seed, "arm": arm, "queries": len(result["queries"]),
                "updates": len(result["training_steps"]), "errors": result["worker_errors"],
                "train_ns": (result["training_intervals"][-1][1]-result["training_intervals"][0][0]) if result["training_intervals"] else 0}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
