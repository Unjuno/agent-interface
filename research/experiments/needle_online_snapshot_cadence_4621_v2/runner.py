"""Frozen CPU experiment: rank-2 online LoRA with checkpoint cadence 1/4/16."""
import argparse
import base64
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import torch
from torch import nn
import torch.nn.functional as F

ALLOCATION = "needle-online-snapshot-cadence-4621-v2"
ISSUE = 4621
SEEDS = (77111, 77222, 77333)
CADENCES = (1, 4, 16)
D, H, C = 8, 16, 4
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 4096
BASE_STEPS, UPDATES_PER_ARRIVAL, BATCH = 400, 8, 32
LR_BASE, LR_ADAPTER = 0.025, 0.04
SNAPSHOT_SCHEMA = "needle-online-skill-snapshot-v1"
SCHEDULE_VERSION = "eight-adamw-updates-per-feedback-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_json(value):
    return sha_bytes(canonical(value))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")


def pack_ids(values):
    return base64.b64encode(bytes(int(x) for x in values)).decode("ascii")


def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))


def labels(x, flip=False):
    a = (x[:, 0] > 0).long()
    b = (x[:, 1] > 0).long()
    if flip:
        a = 1 - a
    return a * 2 + b


class Core(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(D, H), nn.Tanh())
        self.head = nn.Linear(H, C)

    def forward(self, x):
        return self.head(self.enc(x))


class LoRA(nn.Module):
    def __init__(self, core):
        super().__init__()
        self.core = core
        for parameter in self.core.parameters():
            parameter.requires_grad_(False)
        self.a = nn.Parameter(torch.zeros(H, 2))
        self.b = nn.Parameter(torch.zeros(2, C))

    def forward(self, x):
        hidden = self.core.enc(x)
        return self.core.head(hidden) + (hidden @ self.a @ self.b) / 2


def tensor_state(model):
    return {key: value.detach().cpu().tolist() for key, value in model.state_dict().items()}


def optimizer_state(model, optimizer):
    state = optimizer.state
    result = {"step": 0}
    for name, parameter in (("a", model.a), ("b", model.b)):
        item = state.get(parameter)
        if item is None:
            result[f"exp_avg_{name}"] = torch.zeros_like(parameter).detach().cpu().tolist()
            result[f"exp_avg_sq_{name}"] = torch.zeros_like(parameter).detach().cpu().tolist()
        else:
            result["step"] = int(item["step"].item())
            result[f"exp_avg_{name}"] = item["exp_avg"].detach().cpu().tolist()
            result[f"exp_avg_sq_{name}"] = item["exp_avg_sq"].detach().cpu().tolist()
    return result


def load_optimizer_state(model, optimizer, saved):
    step = int(saved["step"])
    if step == 0:
        return
    for name, parameter in (("a", model.a), ("b", model.b)):
        optimizer.state[parameter] = {
            "step": torch.tensor(float(step)),
            "exp_avg": torch.tensor(saved[f"exp_avg_{name}"], dtype=parameter.dtype),
            "exp_avg_sq": torch.tensor(saved[f"exp_avg_sq_{name}"], dtype=parameter.dtype),
        }


def snapshot_digest(snapshot):
    body = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    return sha_json(body)


def seal_snapshot(snapshot):
    result = copy.deepcopy(snapshot)
    result.pop("snapshot_sha256", None)
    result["snapshot_sha256"] = snapshot_digest(result)
    return result


def validate_snapshot(snapshot, seed, base_sha, schedule_sha, expected_cursor):
    if snapshot.get("schema") != SNAPSHOT_SCHEMA or snapshot.get("allocation") != ALLOCATION:
        raise ValueError("snapshot_schema_or_allocation")
    if snapshot.get("seed") != seed or snapshot.get("role") != "B":
        raise ValueError("snapshot_seed_or_role")
    if snapshot.get("base_sha256") != base_sha or snapshot.get("schedule_sha256") != schedule_sha:
        raise ValueError("snapshot_base_or_schedule")
    if snapshot.get("schedule_version") != SCHEDULE_VERSION:
        raise ValueError("snapshot_schedule_version")
    if snapshot.get("cursor") != expected_cursor:
        raise ValueError("snapshot_stale_duplicate_or_skipped_cursor")
    if snapshot.get("snapshot_sha256") != snapshot_digest(snapshot):
        raise ValueError("snapshot_digest")
    opt = snapshot.get("optimizer", {})
    if opt.get("step") != expected_cursor * UPDATES_PER_ARRIVAL:
        raise ValueError("snapshot_optimizer_step")


def route(role, version, adapters):
    if role == "A" and version == 0:
        return "BASE"
    if role == "B" and version == 1 and "B" in adapters:
        return "LORA_B"
    return "YIELD"


def make_schedule(seed):
    order = torch.randperm(N_SUPPORT, generator=torch.Generator(device="cpu").manual_seed(seed + 20)).tolist()
    rng = torch.Generator(device="cpu").manual_seed(seed + 21)
    seen, schedule = [], []
    for row in order:
        seen.append(row)
        batches = []
        for _ in range(UPDATES_PER_ARRIVAL):
            batch_ids = torch.randint(len(seen), (BATCH,), generator=rng).tolist()
            batches.append(batch_ids)
        schedule.append({"row": row, "seen": list(seen), "batches": batches})
    return order, schedule


def train_base(seed):
    torch.manual_seed(seed)
    xb, yb = data(N_BASE, seed + 1), None
    yb = labels(xb)
    core = Core()
    optimizer = torch.optim.AdamW(core.parameters(), lr=LR_BASE)
    rng = torch.Generator(device="cpu").manual_seed(seed + 10)
    core.train()
    for _ in range(BASE_STEPS):
        ids = torch.randint(len(xb), (BATCH,), generator=rng)
        loss = F.cross_entropy(core(xb[ids]), yb[ids])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    return xb, yb, core


def make_input(seed, out):
    xb_base, yb_base, core = train_base(seed)
    x_a, x_support, x_eval = data(N_HELDOUT, seed + 3), data(N_SUPPORT, seed + 2), data(N_HELDOUT, seed + 4)
    y_a, y_support, y_eval = labels(x_a), labels(x_support, flip=True), labels(x_eval, flip=True)
    order, schedule = make_schedule(seed)
    core_state = tensor_state(core)
    core_sha = sha_json(core_state)
    x_a_eval = x_a
    with torch.no_grad():
        pred_a = core(x_a_eval).argmax(-1).tolist()
    initial_generator = torch.Generator(device="cpu").manual_seed(seed + 30)
    initial_a = (torch.randn((H, 2), generator=initial_generator) * 0.04).tolist()
    raw = {
        "schema": "needle-snapshot-cadence-input-v1", "allocation": ALLOCATION, "seed": seed,
        "x_base": xb_base.tolist(), "y_base": yb_base.tolist(), "x_a_eval": x_a.tolist(),
        "y_a_eval": y_a.tolist(), "x_support": x_support.tolist(), "y_support": y_support.tolist(),
        "x_b_eval": x_eval.tolist(), "y_b_eval": y_eval.tolist(), "base_state": core_state,
        "base_sha256": core_sha, "role_a_predictions_b64": pack_ids(pred_a),
        "role_a_accuracy": sum(int(a == b) for a, b in zip(pred_a, y_a.tolist())) / N_HELDOUT,
        "initial_adapter": {"a": initial_a, "b": torch.zeros((2, C)).tolist()},
        "order": order, "schedule": schedule,
    }
    raw["schedule_sha256"] = sha_json({"order": order, "schedule": schedule})
    raw["input_sha256"] = sha_json(raw)
    write_new(Path(out) / f"input-{seed}.json", raw)
    return raw


def make_snapshot(raw, cursor, adapter, opt_state):
    return seal_snapshot({
        "schema": SNAPSHOT_SCHEMA, "allocation": ALLOCATION, "seed": raw["seed"], "role": "B",
        "base_sha256": raw["base_sha256"], "schedule_sha256": raw["schedule_sha256"],
        "schedule_version": SCHEDULE_VERSION, "cursor": cursor,
        "adapter": adapter, "optimizer": opt_state,
    })


def reconstruct(raw, snapshot):
    core = Core()
    core.load_state_dict({k: torch.tensor(v, dtype=torch.float32) for k, v in raw["base_state"].items()})
    model = LoRA(core)
    with torch.no_grad():
        model.a.copy_(torch.tensor(snapshot["adapter"]["a"], dtype=torch.float32))
        model.b.copy_(torch.tensor(snapshot["adapter"]["b"], dtype=torch.float32))
    optimizer = torch.optim.AdamW([model.a, model.b], lr=LR_ADAPTER)
    load_optimizer_state(model, optimizer, snapshot["optimizer"])
    return model, optimizer


def state_record(model, optimizer, xb_eval, yb_eval, arrival):
    model.eval()
    with torch.no_grad():
        predictions = model(xb_eval).argmax(-1).tolist()
    adapter = {"a": model.a.detach().cpu().tolist(), "b": model.b.detach().cpu().tolist()}
    opt_state = optimizer_state(model, optimizer)
    return {
        "arrival": arrival, "adapter": adapter, "optimizer": opt_state,
        "adapter_sha256": sha_json(adapter), "optimizer_sha256": sha_json(opt_state),
        "predictions_b64": pack_ids(predictions),
        "accuracy": sum(int(p == y) for p, y in zip(predictions, yb_eval.tolist())) / len(predictions),
    }


def apply_updates(model, optimizer, xb, yb, batches):
    model.train()
    started = time.perf_counter_ns()
    for ids in batches:
        index = torch.tensor(ids, dtype=torch.long)
        loss = F.cross_entropy(model(xb[index]), yb[index])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    return (time.perf_counter_ns() - started) / 1e6


def worker(args):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    raw = json.loads(Path(args.data).read_text(encoding="utf-8"))
    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    validate_snapshot(state, raw["seed"], raw["base_sha256"], raw["schedule_sha256"], args.start)
    model, optimizer = reconstruct(raw, state)
    print(json.dumps({"event": "READY", "cursor": args.start, "snapshot_sha256": state["snapshot_sha256"]}), flush=True)
    if args.validate_only:
        result = {"schema": "needle-snapshot-validate-v1", "cursor": args.start,
                  "adapter_sha256": sha_json({"a": model.a.detach().cpu().tolist(), "b": model.b.detach().cpu().tolist()}),
                  "optimizer_sha256": sha_json(optimizer_state(model, optimizer))}
        write_new(args.segment, result)
        return
    xb = torch.tensor(raw["x_support"], dtype=torch.float32)
    yb = torch.tensor(raw["y_support"], dtype=torch.long)
    xb_eval = torch.tensor(raw["x_b_eval"], dtype=torch.float32)
    yb_eval = torch.tensor(raw["y_b_eval"], dtype=torch.long)
    records, update_ms = [], []
    for cursor in range(args.start, args.end):
        entry = raw["schedule"][cursor]
        elapsed = apply_updates(model, optimizer, xb, yb, entry["batches"])
        update_ms.append(elapsed)
        records.append(state_record(model, optimizer, xb_eval, yb_eval, cursor + 1))
    adapter = {"a": model.a.detach().cpu().tolist(), "b": model.b.detach().cpu().tolist()}
    end_state = make_snapshot(raw, args.end, adapter, optimizer_state(model, optimizer))
    ckpt_started = time.perf_counter_ns()
    write_new(args.checkpoint, end_state)
    ckpt_write_ms = (time.perf_counter_ns() - ckpt_started) / 1e6
    result = {"schema": "needle-snapshot-segment-v1", "seed": raw["seed"], "start": args.start,
              "end": args.end, "records": records, "update_ms": update_ms,
              "checkpoint_sha256": end_state["snapshot_sha256"], "checkpoint_write_ms": ckpt_write_ms}
    write_new(args.segment, result)


def init_snapshot(raw):
    return make_snapshot(raw, 0, raw["initial_adapter"], {
        "step": 0, "exp_avg_a": torch.zeros((H, 2)).tolist(), "exp_avg_sq_a": torch.zeros((H, 2)).tolist(),
        "exp_avg_b": torch.zeros((2, C)).tolist(), "exp_avg_sq_b": torch.zeros((2, C)).tolist(),
    })


def reference(raw):
    state = init_snapshot(raw)
    validate_snapshot(state, raw["seed"], raw["base_sha256"], raw["schedule_sha256"], 0)
    model, optimizer = reconstruct(raw, state)
    xb, yb = torch.tensor(raw["x_support"], dtype=torch.float32), torch.tensor(raw["y_support"], dtype=torch.long)
    xb_eval, yb_eval = torch.tensor(raw["x_b_eval"], dtype=torch.float32), torch.tensor(raw["y_b_eval"], dtype=torch.long)
    records, updates = [], []
    for cursor, entry in enumerate(raw["schedule"]):
        updates.append(apply_updates(model, optimizer, xb, yb, entry["batches"]))
        records.append(state_record(model, optimizer, xb_eval, yb_eval, cursor + 1))
    return {"records": records, "update_ms": updates}


def launch_worker(data_path, state_path, segment_path, checkpoint_path, start, end, validate_only=False):
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "--data", str(data_path),
               "--state", str(state_path), "--segment", str(segment_path), "--checkpoint", str(checkpoint_path),
               "--start", str(start), "--end", str(end)]
    if validate_only:
        command.append("--validate-only")
    started = time.perf_counter_ns()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               encoding="utf-8", errors="replace", bufsize=1)
    ready_line = process.stdout.readline()
    ready_ms = (time.perf_counter_ns() - started) / 1e6
    tail, stderr = process.communicate()
    stdout = ready_line + tail
    if process.returncode != 0:
        raise RuntimeError(f"worker_exit_{process.returncode}: {stderr[-1000:]} {stdout[-1000:]}")
    try:
        ready = json.loads(ready_line)
    except Exception as exc:
        raise RuntimeError("worker_ready_record_missing") from exc
    if ready.get("event") != "READY" or ready.get("cursor") != start:
        raise RuntimeError("worker_ready_contract")
    return ready_ms, stdout, stderr, command


def run_cadence(raw, cadence, output):
    arm_dir = Path(output) / f"seed-{raw['seed']}" / f"cadence-{cadence}"
    arm_dir.mkdir(parents=True, exist_ok=False)
    input_path = Path(output) / f"input-{raw['seed']}.json"
    state_path = arm_dir / "checkpoint-000.json"
    write_new(state_path, init_snapshot(raw))
    records, update_times, boundaries, logs = [], [], [], []
    cursor, invocation = 0, 0
    while cursor < N_SUPPORT:
        end = min(cursor + cadence, N_SUPPORT)
        segment_path = arm_dir / f"segment-{cursor:02d}-{end:02d}.json"
        checkpoint_path = arm_dir / f"checkpoint-{end:03d}.json"
        ready_ms, stdout, stderr, command = launch_worker(input_path, state_path, segment_path,
                                                          checkpoint_path, cursor, end)
        invocation += 1
        segment = json.loads(segment_path.read_text(encoding="utf-8"))
        if segment.get("start") != cursor or segment.get("end") != end:
            raise RuntimeError("segment_cursor_contract")
        records.extend(segment["records"])
        update_times.extend(segment["update_ms"])
        boundaries.append({"start": cursor, "end": end, "cadence": cadence, "restart_ready_ms": ready_ms,
                           "checkpoint_write_ms": segment["checkpoint_write_ms"],
                           "checkpoint_sha256": segment["checkpoint_sha256"],
                           "checkpoint_path": str(checkpoint_path.relative_to(output)),
                           "command": command, "stdout": stdout, "stderr": stderr})
        logs.append({"command": command, "stdout": stdout, "stderr": stderr, "returncode": 0})
        state_path = checkpoint_path
        cursor = end
    validate_path = arm_dir / "validate-final.json"
    final_segment = arm_dir / "validate-final-result.json"
    ready_ms, stdout, stderr, command = launch_worker(input_path, state_path, final_segment,
                                                      validate_path, cursor, cursor, True)
    invocation += 1
    final_check = json.loads(final_segment.read_text(encoding="utf-8"))
    final_state = json.loads(state_path.read_text(encoding="utf-8"))
    boundaries[-1]["final_restore_ready_ms"] = ready_ms
    boundaries[-1]["final_restore_stdout"] = stdout
    boundaries[-1]["final_restore_stderr"] = stderr
    boundaries[-1]["final_restore_command"] = command
    logs.append({"command": command, "stdout": stdout, "stderr": stderr, "returncode": 0,
                 "validate_only": True})
    return {"cadence": cadence, "records": records, "update_ms": update_times,
            "boundaries": boundaries, "process_invocations": invocation, "process_logs": logs,
            "final_checkpoint": {"path": str(state_path.relative_to(output)),
                                 "sha256": sha_bytes(state_path.read_bytes()),
                                 "snapshot_sha256": final_state["snapshot_sha256"],
                                 "validation": final_check}}


def run_seed(seed, output):
    raw = make_input(seed, output)
    ref = reference(raw)
    arms = {}
    for cadence in CADENCES:
        arms[str(cadence)] = run_cadence(raw, cadence, output)
    # Route and malformed-snapshot controls are construction-only and run before publishing this seed result.
    controls = {
        "base_route": route("A", 0, {}) == "BASE",
        "skill_route": route("B", 1, {"B": object()}) == "LORA_B",
        "unknown_role_yield": route("C", 1, {"B": object()}) == "YIELD",
        "stale_version_yield": route("B", 0, {"B": object()}) == "YIELD",
        "missing_skill_yield": route("B", 1, {}) == "YIELD",
    }
    result = {"schema": "needle-snapshot-cadence-seed-v1", "allocation": ALLOCATION,
              "seed": seed, "input_sha256": raw["input_sha256"], "base_sha256": raw["base_sha256"],
              "schedule_sha256": raw["schedule_sha256"], "role_a_accuracy": raw["role_a_accuracy"],
              "role_a_predictions_b64": raw["role_a_predictions_b64"], "reference": ref,
              "arms": arms, "controls": controls,
              "environment": {"torch": torch.__version__, "device": "cpu", "threads": 1,
                              "deterministic": torch.are_deterministic_algorithms_enabled()}}
    result_path = Path(output) / f"seed-result-{seed}.json"
    write_new(result_path, result)
    return result_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--data")
    parser.add_argument("--state")
    parser.add_argument("--segment")
    parser.add_argument("--checkpoint")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker(args)
        return 0
    output = Path(args.out)
    if not output.is_dir() or any(output.iterdir()):
        raise SystemExit("dedicated_empty_training_directory_required")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    started = time.time_ns()
    result_paths = [run_seed(seed, output) for seed in SEEDS]
    run = {"schema": "needle-snapshot-cadence-run-v1", "allocation": ALLOCATION,
           "seeds": list(SEEDS), "cadences": list(CADENCES), "started_ns": started,
           "finished_ns": time.time_ns(), "formal_invocations": 1, "retry_count": 0,
           "seed_result_sha256": {path.name: sha_bytes(path.read_bytes()) for path in result_paths}}
    write_new(output / "RUN.json", run)
    print(json.dumps({"status": "COMPLETE", "seeds": len(SEEDS), "formal_invocations": 1}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

