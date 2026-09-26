"""Paired rank-1/rank-2 online LoRA skill update allocation (CPU only)."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import random
import time

import torch
from torch import nn

ALLOCATION = "needle-lora-rank1-online-skill-v2"
ISSUE = 4519
DOCKER_IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
SEEDS = (75111, 75222, 75333)
D, H, C = 8, 16, 4
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 4096
BASE_STEPS, UPDATES_PER_ARRIVAL, BATCH = 400, 8, 32
LR_BASE, LR_ADAPTER = 0.025, 0.04
RANKS = (1, 2)
SEED_OFFSETS = (1, 2, 3, 4, 10, 20, 21, 30)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_json(value):
    return sha_bytes(canonical(value))


def pack_ids(values):
    return base64.b64encode(bytes(int(x) for x in values)).decode("ascii")


def unpack_ids(value):
    return list(base64.b64decode(value, validate=True))


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
    def __init__(self, core, rank):
        super().__init__()
        self.core = core
        self.rank = rank
        for parameter in self.core.parameters():
            parameter.requires_grad_(False)
        self.a = nn.Parameter(torch.zeros(H, rank))
        self.b = nn.Parameter(torch.zeros(rank, C))

    def forward(self, x):
        hidden = self.core.enc(x)
        return self.core.head(hidden) + (hidden @ self.a @ self.b) / self.rank


def tensor_state(model):
    return {key: value.detach().cpu().tolist() for key, value in model.state_dict().items()}


def forward_ids(model, x):
    model.eval()
    with torch.no_grad():
        return model(x).argmax(-1).tolist()


def route(role, version, adapters):
    if role == "A" and version == 0:
        return "BASE"
    if role == "B" and version == 1 and "B" in adapters:
        return "LORA_B"
    return "YIELD"


def make_schedule(seed):
    order = torch.randperm(N_SUPPORT, generator=torch.Generator(device="cpu").manual_seed(seed + 20)).tolist()
    rng = torch.Generator(device="cpu").manual_seed(seed + 21)
    seen = []
    schedule = []
    for row in order:
        seen.append(row)
        batches = []
        for _ in range(UPDATES_PER_ARRIVAL):
            batch_ids = torch.randint(len(seen), (BATCH,), generator=rng).tolist()
            batches.append([seen[index] for index in batch_ids])
        schedule.append({"row": row, "seen": list(seen), "batches": batches})
    return order, schedule


def apply_arrival(model, optimizer, xb, yb, batches):
    model.train()
    started = time.perf_counter_ns()
    for ids in batches:
        index = torch.tensor(ids, dtype=torch.long)
        loss = nn.functional.cross_entropy(model(xb[index]), yb[index])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    return (time.perf_counter_ns() - started) / 1e6


def initialize_paired_adapters(base, seed):
    generator = torch.Generator(device="cpu").manual_seed(seed + 30)
    a_full = torch.randn((H, 2), generator=generator) * 0.04
    b_full = torch.zeros((2, C))
    arms = {}
    for rank in RANKS:
        model = LoRA(copy.deepcopy(base), rank)
        with torch.no_grad():
            model.a.copy_(a_full[:, :rank])
            model.b.copy_(b_full[:rank, :])
        optimizer = torch.optim.AdamW([model.a, model.b], lr=LR_ADAPTER)
        arms[rank] = (model, optimizer)
    return arms


def evaluate_route(role, version, base, adapters, x):
    selected = route(role, version, adapters)
    if selected == "BASE":
        return forward_ids(base, x)
    if selected == "LORA_B":
        return forward_ids(adapters["B"], x)
    raise ValueError("route_yield")


def run_seed(seed, out):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    xb_base = data(N_BASE, seed + 1)
    yb_base = labels(xb_base)
    core = Core()
    optimizer_base = torch.optim.AdamW(core.parameters(), lr=LR_BASE)
    rng_base = torch.Generator(device="cpu").manual_seed(seed + 10)
    core.train()
    for _ in range(BASE_STEPS):
        ids = torch.randint(len(xb_base), (BATCH,), generator=rng_base)
        loss = nn.functional.cross_entropy(core(xb_base[ids]), yb_base[ids])
        optimizer_base.zero_grad(set_to_none=True)
        loss.backward()
        optimizer_base.step()
    base_before = tensor_state(core)
    base_digest = sha_json(base_before)

    x_a_eval, y_a_eval = data(N_HELDOUT, seed + 3), None
    y_a_eval = labels(x_a_eval)
    x_b, y_b = data(N_SUPPORT, seed + 2), None
    y_b = labels(x_b, flip=True)
    x_b_eval = data(N_HELDOUT, seed + 4)
    y_b_eval = labels(x_b_eval, flip=True)
    a_predictions = evaluate_route("A", 0, core, {}, x_a_eval)
    order, schedule = make_schedule(seed)
    arms = initialize_paired_adapters(core, seed)
    frozen_core_before = {rank: sha_json(tensor_state(model.core)) for rank, (model, _) in arms.items()}
    expected = {
        "role_a": pack_ids(y_a_eval.tolist()),
        "role_b": pack_ids(y_b_eval.tolist()),
    }
    result_arms = {}
    for rank in RANKS:
        model, optimizer = arms[rank]
        snapshots, times_ms, seen = [], [], []
        adapters = {"B": model}
        for arrival, entry in enumerate(schedule, 1):
            seen.append(entry["row"])
            times_ms.append(apply_arrival(model, optimizer, x_b, y_b, entry["batches"]))
            predictions = evaluate_route("B", 1, core, adapters, x_b_eval)
            adapter_state = {"a": model.a.detach().cpu().tolist(), "b": model.b.detach().cpu().tolist()}
            snapshots.append({
                "arrival": arrival,
                "seen_rows": list(seen),
                "adapter": adapter_state,
                "predictions_b64": pack_ids(predictions),
                "accuracy": sum(int(p == y) for p, y in zip(predictions, y_b_eval.tolist())) / N_HELDOUT,
            })
        result_arms[str(rank)] = {
            "rank": rank,
            "initial_adapter": {"a": (torch.randn((H, 2), generator=torch.Generator(device="cpu").manual_seed(seed + 30)) * 0.04)[:, :rank].tolist(),
                                "b": torch.zeros((2, C))[:rank, :].tolist()},
            "update_ms": times_ms,
            "snapshots": snapshots,
            "base_copy_sha256_before": frozen_core_before[rank],
            "base_copy_sha256_after": sha_json(tensor_state(model.core)),
        }
    order_digest = sha_json({"order": order, "schedule": schedule})
    after_base = sha_json(tensor_state(core))
    controls = {
        "valid_base_route": route("A", 0, {}) == "BASE",
        "valid_skill_route": route("B", 1, {"B": object()}) == "LORA_B",
        "unknown_role_yields": route("C", 1, {"B": object()}) == "YIELD",
        "stale_skill_version_yields": route("B", 0, {"B": object()}) == "YIELD",
        "future_skill_version_yields": route("B", 2, {"B": object()}) == "YIELD",
        "missing_skill_yields": route("B", 1, {}) == "YIELD",
    }
    seed_result = {
        "schema": "needle-rank1-online-seed.v1",
        "allocation": ALLOCATION,
        "seed": seed,
        "base_sha256": base_digest,
        "base_sha256_after": after_base,
        "base_state": base_before,
        "role_a_predictions_b64": pack_ids(a_predictions),
        "expected_b64": expected,
        "role_a_accuracy": sum(int(p == y) for p, y in zip(a_predictions, y_a_eval.tolist())) / N_HELDOUT,
        "role_b_order": order,
        "schedule_sha256": order_digest,
        "arms": result_arms,
        "controls": controls,
        "environment": {"torch": torch.__version__, "device": "cpu", "threads": torch.get_num_threads(),
                        "deterministic": torch.are_deterministic_algorithms_enabled()},
    }
    target = Path(out) / f"seed-{seed}.json"
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(seed_result, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")
    return seed_result


def output_directory_ready(out):
    out = Path(out)
    if not out.is_dir():
        return False
    entries = list(out.iterdir())
    if not entries:
        return True
    if len(entries) != 1 or entries[0].name != "FORMAL_INVOCATION.json":
        return False
    try:
        marker = json.loads(entries[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (marker.get("schema") == "needle-rank1-formal-invocation.v1"
            and marker.get("allocation") == ALLOCATION
            and marker.get("issue") == ISSUE
            and marker.get("formal_invocations") == 1
            and marker.get("retry_count") == 0
            and marker.get("docker_image_id") == DOCKER_IMAGE_ID)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if not output_directory_ready(out):
        raise SystemExit("output_directory_must_be_empty_or_contain_exact_frozen_invocation")
    started = time.time_ns()
    seeds = [run_seed(seed, out) for seed in SEEDS]
    report = {"schema": "needle-rank1-online-run.v1", "allocation": ALLOCATION,
              "seeds": list(SEEDS), "seed_files": [f"seed-{seed}.json" for seed in SEEDS],
              "started_ns": started, "finished_ns": time.time_ns(),
              "formal_invocations": 1, "retry_count": 0,
              "result_sha256": {f"seed-{row['seed']}.json": sha_bytes((out / f"seed-{row['seed']}.json").read_bytes())
                                for row in seeds}}
    with (out / "RUN.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": "COMPLETE", "seeds": len(seeds), "formal_invocations": 1}, sort_keys=True))


if __name__ == "__main__":
    main()
