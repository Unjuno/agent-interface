"""COW online rank-2 LoRA under matched 1- and 2-vCPU Docker quotas."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time

import torch
import torch.nn.functional as F

torch.set_num_threads(1)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    # Construction tests may import the independent auditor in this process.
    pass
torch.use_deterministic_algorithms(True)

SEEDS = (9765101, 9765203, 9765307)
ARMS = {"COW_CPU1": 1, "COW_CPU2": 2}
ARRIVALS = 12
STEPS_PER_ARRIVAL = 16
BATCH = 512
QUERIES = 120
PERIOD_NS = 16_666_667


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def floats(tensor):
    return tensor.detach().cpu().tolist()


def tensor(value):
    return torch.tensor(value, dtype=torch.float32)


def parse_cpu_max(value):
    fields = value.split()
    if len(fields) != 2 or fields[0] == "max":
        raise RuntimeError("STOP_CPU_QUOTA_UNBOUNDED_OR_UNREADABLE")
    quota, period = map(int, fields)
    if quota <= 0 or period <= 0:
        raise RuntimeError("STOP_CPU_QUOTA_INVALID")
    return {"cpu_max": " ".join(fields), "quota_cores": quota / period}


def cpu_quota():
    return parse_cpu_max(Path("/sys/fs/cgroup/cpu.max").read_text(encoding="ascii"))


def deadline_missed(finish, deadline):
    return finish > deadline


def make_seed(seed):
    generator = torch.Generator(device="cpu").manual_seed(seed)
    w1 = torch.randn((16, 8), generator=generator) * 0.22
    b1 = torch.randn((16,), generator=generator) * 0.04
    w2 = torch.randn((4, 16), generator=generator) * 0.16
    b2 = torch.randn((4,), generator=generator) * 0.02
    teacher = torch.randn((4, 8), generator=generator)
    teacher_b = torch.randn((4,), generator=generator) * 0.1
    supports = torch.randn((ARRIVALS, BATCH, 8), generator=generator)
    queries = torch.randn((QUERIES, 8), generator=generator)
    support_y = (supports @ teacher.T + teacher_b).argmax(dim=2)
    query_y = (queries @ teacher.T + teacher_b).argmax(dim=1)
    a = torch.randn((2, 16), generator=generator) * 0.025
    b = torch.zeros((4, 2))
    base = {"w1": floats(w1), "b1": floats(b1), "w2": floats(w2), "b2": floats(b2)}
    task = {"support_x": floats(supports), "support_y": support_y.tolist(),
            "query_x": floats(queries), "query_y": query_y.tolist(),
            "teacher": floats(teacher), "teacher_b": floats(teacher_b)}
    initial = {"a": floats(a), "b": floats(b)}
    return base, task, initial


def predict(base, a, b, x):
    hidden = torch.tanh(F.linear(x, tensor(base["w1"]), tensor(base["b1"])))
    effective = tensor(base["w2"]) + b @ a
    return F.linear(hidden, effective, tensor(base["b2"]))


def train_step(base, a, b, x, y, optimizer):
    optimizer.zero_grad(set_to_none=True)
    loss = F.cross_entropy(predict(base, a, b, x), y)
    loss.backward()
    optimizer.step()
    return float(loss.detach())


def state_record(a, b, version):
    item = {"version": int(version), "a": floats(a), "b": floats(b)}
    item["sha256"] = digest(item)
    return item


def immutable_snapshot(a, b, version):
    return {"version": int(version), "a": a.detach().clone(), "b": b.detach().clone()}


def atomic_publish(active, lock, item):
    with lock:
        active["current"] = item


def capture_active(active, lock):
    with lock:
        return active["current"]


def intervals_overlap(start, end, intervals):
    now = time.perf_counter_ns()
    return any(begin < end and (finish if finish is not None else now) > start
               for begin, finish in intervals)


def run_cell(seed, arm, output):
    expected_cpus = ARMS[arm]
    quota = cpu_quota()
    env_cpus = int(os.environ.get("NEEDLE_EXPECTED_CPUS", "0"))
    if env_cpus != expected_cpus or not math.isclose(quota["quota_cores"], expected_cpus, abs_tol=1e-9):
        raise SystemExit("STOP_CPU_QUOTA_BINDING")
    base, task, initial = make_seed(seed)
    base_sha = digest(base)
    a0, b0 = tensor(initial["a"]), tensor(initial["b"])
    active_lock = threading.Lock()
    active = {"current": immutable_snapshot(a0, b0, 0)}
    published = {"0": state_record(a0, b0, 0)}
    interval_lock = threading.Lock()
    intervals = []
    step_records = []
    worker_errors = []
    start_gate = threading.Event()
    stop_gate = threading.Event()
    support_x = tensor(task["support_x"])
    support_y = torch.tensor(task["support_y"], dtype=torch.long)

    def training_worker():
        try:
            if not start_gate.wait(5):
                raise RuntimeError("start gate timeout")
            train_a = a0.clone().requires_grad_(True)
            train_b = b0.clone().requires_grad_(True)
            optimizer = torch.optim.AdamW([train_a, train_b], lr=0.035, weight_decay=0.0)
            update = 0
            for arrival in range(ARRIVALS):
                for _ in range(STEPS_PER_ARRIVAL):
                    begin = time.perf_counter_ns()
                    with interval_lock:
                        interval_index = len(intervals)
                        intervals.append([begin, None])
                    loss = train_step(base, train_a, train_b,
                                      support_x[arrival], support_y[arrival], optimizer)
                    finish = time.perf_counter_ns()
                    step_records.append({"arrival": arrival + 1, "update": update + 1,
                                         "loss": loss, "start_ns": begin, "end_ns": finish})
                    update += 1
                    with interval_lock:
                        intervals[interval_index][1] = finish
                version = arrival + 1
                item = immutable_snapshot(train_a, train_b, version)
                atomic_publish(active, active_lock, item)
                published[str(version)] = state_record(train_a, train_b, version)
        except BaseException as exc:
            worker_errors.append(f"{type(exc).__name__}:{exc}")
        finally:
            stop_gate.set()

    worker = threading.Thread(target=training_worker, name=f"trainer-{seed}-{arm}", daemon=False)
    worker.start()
    start_ns = time.perf_counter_ns()
    start_gate.set()
    query_rows = []
    query_x = task["query_x"]
    query_y = task["query_y"]
    for index in range(QUERIES):
        scheduled = start_ns + index * PERIOD_NS
        while True:
            remaining = scheduled - time.perf_counter_ns()
            if remaining <= 0:
                break
            time.sleep(min(remaining / 1e9, 0.002))
        begin = time.perf_counter_ns()
        captured = capture_active(active, active_lock)
        version = captured["version"]
        captured_a = captured["a"]
        captured_b = captured["b"]
        with torch.no_grad():
            logits = predict(base, captured_a, captured_b, tensor([query_x[index]]))[0]
        finish = time.perf_counter_ns()
        with interval_lock:
            overlap = intervals_overlap(begin, finish, intervals)
        deadline = scheduled + PERIOD_NS
        query_rows.append({"index": index, "scheduled_ns": scheduled,
                           "deadline_ns": deadline, "start_ns": begin, "end_ns": finish,
                           "latency_ns": finish - begin, "deadline_miss": deadline_missed(finish, deadline),
                           "x": query_x[index], "label": query_y[index],
                           "logits": floats(logits), "version_before": version,
                           "version_after": version, "train_interval_overlap": overlap})
    worker.join(timeout=30)
    if worker.is_alive():
        worker_errors.append("worker join timeout")
    with interval_lock:
        closed_intervals = [list(pair) for pair in intervals]
    if any(finish is None for _, finish in closed_intervals):
        worker_errors.append("open training interval")
    return {"schema": "needle-cow-two-cpu.raw.v1", "seed": seed, "arm": arm,
            "expected_cpus": expected_cpus, "cpu_quota": quota,
            "torch_threads": {"intraop": torch.get_num_threads(),
                              "interop": torch.get_num_interop_threads()},
            "constants": {"arrivals": ARRIVALS, "steps_per_arrival": STEPS_PER_ARRIVAL,
                          "batch": BATCH, "queries": QUERIES, "period_ns": PERIOD_NS},
            "base": base, "base_sha256": base_sha, "immutable_base_after_sha256": digest(base),
            "task": task, "initial": initial, "query_origin_ns": start_ns,
            "published": published,
            "queries": query_rows, "training_steps": step_records,
            "training_intervals": closed_intervals, "worker_errors": worker_errors,
            "training_finished_before_query_loop_end": stop_gate.is_set(),
            "authority": False, "action_emissions": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.seed not in SEEDS:
        raise SystemExit("STOP_UNREGISTERED_SEED")
    output = Path(args.out)
    if not output.is_dir() or any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    result = run_cell(args.seed, args.arm, output)
    if result["seed"] != args.seed:
        raise SystemExit("STOP_SEED_IDENTITY")
    target = output / f"seed_{args.seed}_{args.arm.lower()}.json"
    target.write_bytes(canonical(result) + b"\n")
    print(json.dumps({"seed": result["seed"], "arm": result["arm"],
                      "cpu_quota": result["cpu_quota"],
                      "queries": len(result["queries"]),
                      "updates": len(result["training_steps"]),
                      "worker_errors": result["worker_errors"]},
                     sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
