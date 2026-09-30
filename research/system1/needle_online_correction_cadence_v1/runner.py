"""Frozen CPU-only online SINGLE vs true MICROBatch2 LoRA schedule study."""
import hashlib
import json
import os
import platform
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

ALLOCATION = "needle-online-correction-cadence-20260927-v1"
SEEDS = (734211, 734311, 734411)
ROLES = ("A", "B")
SCHEMA = "needle-online-cadence-raw-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def tensor_map(module):
    return {k: v.detach().cpu().tolist() for k, v in module.state_dict().items()}


def data(rows, seed, salt):
    rng = random.Random(seed * 1009 + salt)
    factors = [0, 1] * (rows // 2)
    rng.shuffle(factors)
    values = [[float(bit), *[rng.random() for _ in range(7)]] for bit in factors]
    return torch.tensor(values, dtype=torch.float32)


def labels_b(x):
    return 1 - x[:, 0].long()


def labels_a(x):
    return x[:, 0].long()


def balanced_support(seed):
    x = data(16, seed, 202)
    return x, labels_b(x)


def update_batch(arm, arrival):
    if arm == "SINGLE":
        return [arrival]
    if arm == "MICROBATCH2":
        return [arrival - 1, arrival] if arrival % 2 == 1 else []
    raise ValueError("unknown_arm")


def steps_per_arrival(arm, arrival):
    if arm == "SINGLE":
        return 8
    if arm == "MICROBATCH2":
        return 16 if arrival % 2 == 1 else 0
    raise ValueError("unknown_arm")


def route(role, scope):
    if role not in ROLES or scope != "synthetic-role-v1":
        return {"status": "YIELD", "selected_role": None, "proposal": None}
    return {"status": "READY", "selected_role": role, "proposal": None}


class Core(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = torch.nn.Linear(8, 16)
        self.head = torch.nn.Linear(16, 4)

    def forward(self, x):
        return self.head(torch.tanh(self.enc(x)))


class Adapter(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.left = torch.nn.Parameter(torch.randn(16, 2) * 0.1)
        self.right = torch.nn.Parameter(torch.zeros(2, 4))

    def forward(self, core, x):
        h = torch.tanh(core.enc(x))
        return core.head(h) + (h @ self.left @ self.right) / 2


def train_base(seed):
    torch.manual_seed(seed)
    model = Core()
    x = data(256, seed, 101)
    y = labels_a(x)
    indices_rng = torch.Generator().manual_seed(seed + 102)
    indices = torch.randint(len(x), (400,), generator=indices_rng).tolist()
    opt = torch.optim.AdamW(model.parameters(), lr=0.03, weight_decay=1e-4)
    for _ in range(400):
        index = indices[_]
        opt.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(x[index:index + 1]), y[index:index + 1])
        loss.backward()
        opt.step()
    return model, x, y, indices


def optimizer_state(opt, adapter):
    names = ("left", "right")
    out = {}
    for name, parameter in zip(names, (adapter.left, adapter.right)):
        state = opt.state.get(parameter, {})
        out[name] = {
            "step": float(state["step"].item()) if "step" in state else 0.0,
            "exp_avg": state["exp_avg"].tolist() if "exp_avg" in state else None,
            "exp_avg_sq": state["exp_avg_sq"].tolist() if "exp_avg_sq" in state else None,
        }
    return out


def score(core, adapter, x):
    with torch.no_grad():
        return adapter(core, x).argmax(-1).tolist()


def fit_arm(seed, arm, core, support, support_y, test_a, test_b, init):
    adapter = Adapter()
    with torch.no_grad():
        adapter.left.copy_(torch.tensor(init["left"], dtype=torch.float32))
        adapter.right.copy_(torch.tensor(init["right"], dtype=torch.float32))
    opt = torch.optim.AdamW(adapter.parameters(), lr=0.04, weight_decay=1e-4)
    arrivals = []
    update_ns = []
    burst_ns = []
    for ix in range(16):
        rows = update_batch(arm, ix)
        updated = bool(rows)
        event_started = time.perf_counter_ns()
        if updated:
            index = torch.tensor(rows, dtype=torch.long)
            for _ in range(steps_per_arrival(arm, ix)):
                started = time.perf_counter_ns()
                opt.zero_grad(set_to_none=True)
                logits = adapter(core, support[index])
                loss = F.cross_entropy(logits, support_y[index])
                loss.backward()
                opt.step()
                update_ns.append(time.perf_counter_ns() - started)
        burst_ns.append(time.perf_counter_ns() - event_started if updated else 0)
        state = {"left": adapter.left.detach().tolist(), "right": adapter.right.detach().tolist()}
        arrivals.append({
            "arrival": ix + 1,
            "updated": updated,
            "adapter": state,
            "optimizer": optimizer_state(opt, adapter),
            "pred_a": score(core, adapter, test_a),
            "pred_b": score(core, adapter, test_b),
            "adapter_sha256": digest(state),
        })
    return {"arm": arm, "optimizer_steps": len(update_ns), "update_ns": update_ns,
            "burst_ns": burst_ns,
            "arrivals": arrivals, "final_optimizer": optimizer_state(opt, adapter)}


def run_seed(seed):
    core, base_train_x, base_train_y, base_indices = train_base(seed)
    for parameter in core.parameters():
        parameter.requires_grad_(False)
    base_before = tensor_map(core)
    base_sha = digest(base_before)
    support, support_y = balanced_support(seed)
    test_a = data(256, seed, 303)
    test_b = data(256, seed, 404)
    y_a = labels_a(test_a)
    y_b = labels_b(test_b)
    torch.manual_seed(seed + 500)
    init = {"left": (torch.randn(16, 2) * 0.1).tolist(), "right": torch.zeros(2, 4).tolist()}
    invalid_controls = [route("UNKNOWN", "synthetic-role-v1"), route("B", "stale-scope")]
    arms = [fit_arm(seed, arm, core, support, support_y, test_a, test_b, init)
            for arm in ("SINGLE", "MICROBATCH2")]
    base_after = tensor_map(core)
    return {
        "seed": seed,
        "base": base_before,
        "base_train_x": base_train_x.tolist(), "base_train_y": base_train_y.tolist(),
        "base_row_indices": base_indices,
        "base_sha256": base_sha,
        "base_after_sha256": digest(base_after),
        "base_immutable": base_before == base_after,
        "init_adapter": init,
        "invalid_controls": invalid_controls,
        "support_x": support.tolist(), "support_y": support_y.tolist(),
        "test_a_x": test_a.tolist(), "test_a_y": y_a.tolist(),
        "test_b_x": test_b.tolist(), "test_b_y": y_b.tolist(),
        "arms": arms,
    }


def main():
    out_value = os.environ.get("NEEDLE_OUTPUT", "")
    seed_value = os.environ.get("NEEDLE_SEEDS", "")
    if not out_value or not seed_value:
        raise SystemExit("STOP_INVALID_TRAINING_ENV")
    try:
        requested = tuple(int(x) for x in seed_value.split(","))
    except ValueError:
        raise SystemExit("STOP_INVALID_TRAINING_ENV")
    if requested != SEEDS:
        raise SystemExit("STOP_SEED_ALLOCATION_MISMATCH")
    out = Path(out_value)
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    results = {"schema": SCHEMA, "allocation": ALLOCATION, "seeds": list(SEEDS),
               "environment": {"platform": platform.platform(), "python": platform.python_version(),
                               "torch": torch.__version__, "device": "cpu",
                               "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads()},
               "runs": [run_seed(seed) for seed in SEEDS]}
    payload = canonical(results) + b"\n"
    target = out / "formal_result.json"
    with target.open("xb") as f:
        f.write(payload)
    print(json.dumps({"allocation": ALLOCATION, "seeds": list(SEEDS),
                      "formal_result_bytes": len(payload),
                      "formal_result_sha256": hashlib.sha256(payload).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
