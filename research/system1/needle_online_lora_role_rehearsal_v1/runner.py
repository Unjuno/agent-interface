"""Frozen role-conditioned online LoRA rehearsal study."""
import hashlib
import json
import os
import platform
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

ALLOCATION = "needle-online-lora-role-rehearsal-20260927-v1"
SEEDS = (735211, 735311, 735411)
ARMS = ("B_ONLY", "B_DUPLICATE_CONTROL", "A_REHEARSAL")
SCHEMA = "needle-role-rehearsal-raw-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(canonical(value))


def sample(rows, seed, salt, role):
    rng = random.Random(seed * 1009 + salt)
    factors = [0, 1] * (rows // 2)
    rng.shuffle(factors)
    return torch.tensor([[float(bit), *[rng.random() for _ in range(7)], float(role)]
                         for bit in factors], dtype=torch.float32)


def label_a(x):
    return x[:, 0].long()


def label_b(x):
    return 1 - x[:, 0].long()


def route(role, scope):
    if role not in ("A", "B") or scope != "synthetic-role-v1":
        return {"status": "YIELD", "selected_role": None, "proposal": None}
    return {"status": "READY", "selected_role": role, "proposal": None}


class Core(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = torch.nn.Linear(9, 16)
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
    x = sample(256, seed, 101, 0)
    y = label_a(x)
    index_rng = torch.Generator().manual_seed(seed + 102)
    indices = torch.randint(len(x), (400,), generator=index_rng).tolist()
    opt = torch.optim.AdamW(model.parameters(), lr=0.03, weight_decay=1e-4)
    for index in indices:
        opt.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(x[index:index + 1]), y[index:index + 1])
        loss.backward()
        opt.step()
    return model, x, y, indices


def tensor_map(module):
    return {key: value.detach().cpu().tolist() for key, value in module.state_dict().items()}


def optimizer_state(opt, adapter):
    out = {}
    for name, parameter in zip(("left", "right"), (adapter.left, adapter.right)):
        state = opt.state.get(parameter, {})
        out[name] = {"step": float(state["step"].item()) if "step" in state else 0.0,
                     "exp_avg": state["exp_avg"].tolist() if "exp_avg" in state else None,
                     "exp_avg_sq": state["exp_avg_sq"].tolist() if "exp_avg_sq" in state else None}
    return out


def predict(core, adapter, x):
    with torch.no_grad():
        return adapter(core, x).argmax(-1).tolist()


def batch_for(arm, b_x, b_y, a_x, a_y, a_ix):
    if arm == "B_ONLY":
        return b_x.reshape(1, -1), b_y.reshape(1)
    if arm == "B_DUPLICATE_CONTROL":
        return b_x.repeat(2, 1), b_y.repeat(2)
    if arm == "A_REHEARSAL":
        return torch.stack((b_x, a_x[a_ix])), torch.stack((b_y, a_y[a_ix]))
    raise ValueError("unknown_arm")


def fit_arm(seed, arm, core, support_x, support_y, memory_x, memory_y,
            test_a, test_b, init):
    adapter = Adapter()
    with torch.no_grad():
        adapter.left.copy_(torch.tensor(init["left"], dtype=torch.float32))
        adapter.right.copy_(torch.tensor(init["right"], dtype=torch.float32))
    opt = torch.optim.AdamW(adapter.parameters(), lr=0.04, weight_decay=1e-4)
    arrivals, update_ns = [], []
    for arrival in range(16):
        for step in range(8):
            ix = arrival * 8 + step
            x, y = batch_for(arm, support_x[arrival], support_y[arrival],
                             memory_x, memory_y, ix % 16)
            started = time.perf_counter_ns()
            opt.zero_grad(set_to_none=True)
            loss = F.cross_entropy(adapter(core, x), y)
            loss.backward()
            opt.step()
            update_ns.append(time.perf_counter_ns() - started)
        state = {"left": adapter.left.detach().tolist(), "right": adapter.right.detach().tolist()}
        arrivals.append({"arrival": arrival + 1, "adapter": state,
                         "adapter_sha256": digest(state), "optimizer": optimizer_state(opt, adapter),
                         "pred_a": predict(core, adapter, test_a),
                         "pred_b": predict(core, adapter, test_b)})
    return {"arm": arm, "optimizer_steps": len(update_ns), "update_ns": update_ns,
            "arrivals": arrivals, "final_optimizer": optimizer_state(opt, adapter)}


def run_seed(seed):
    core, train_x, train_y, indices = train_base(seed)
    for parameter in core.parameters():
        parameter.requires_grad_(False)
    base = tensor_map(core)
    base_sha = digest(base)
    memory_x = sample(16, seed, 202, 0)
    memory_y = label_a(memory_x)
    support_x = sample(16, seed, 303, 1)
    support_y = label_b(support_x)
    test_a, test_b = sample(256, seed, 404, 0), sample(256, seed, 505, 1)
    test_a_y, test_b_y = label_a(test_a), label_b(test_b)
    torch.manual_seed(seed + 500)
    init = {"left": (torch.randn(16, 2) * 0.1).tolist(),
            "right": torch.zeros(2, 4).tolist()}
    controls = [route("UNKNOWN", "synthetic-role-v1"), route("B", "stale-scope")]
    arms = [fit_arm(seed, arm, core, support_x, support_y, memory_x, memory_y,
                    test_a, test_b, init) for arm in ARMS]
    return {"seed": seed, "base": base, "base_sha256": base_sha,
            "base_after_sha256": digest(tensor_map(core)), "base_immutable": base == tensor_map(core),
            "base_train_x": train_x.tolist(), "base_train_y": train_y.tolist(),
            "base_row_indices": indices, "memory_x": memory_x.tolist(), "memory_y": memory_y.tolist(),
            "support_x": support_x.tolist(), "support_y": support_y.tolist(),
            "test_a_x": test_a.tolist(), "test_a_y": test_a_y.tolist(),
            "test_b_x": test_b.tolist(), "test_b_y": test_b_y.tolist(),
            "init_adapter": init, "invalid_controls": controls, "arms": arms}


def main():
    output = os.environ.get("NEEDLE_OUTPUT", "")
    seed_text = os.environ.get("NEEDLE_SEEDS", "")
    if not output or not seed_text:
        raise SystemExit("STOP_INVALID_TRAINING_ENV")
    try:
        seeds = tuple(int(value) for value in seed_text.split(","))
    except ValueError as exc:
        raise SystemExit("STOP_INVALID_TRAINING_ENV") from exc
    if seeds != SEEDS:
        raise SystemExit("STOP_SEED_ALLOCATION_MISMATCH")
    out = Path(output)
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    result = {"schema": SCHEMA, "allocation": ALLOCATION, "seeds": list(SEEDS),
              "arms": list(ARMS),
              "environment": {"platform": platform.platform(), "python": platform.python_version(),
                              "torch": torch.__version__, "device": "cpu",
                              "threads": torch.get_num_threads(),
                              "interop_threads": torch.get_num_interop_threads()},
              "runs": [run_seed(seed) for seed in SEEDS]}
    payload = canonical(result) + b"\n"
    with (out / "formal_result.json").open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"allocation": ALLOCATION, "seeds": list(SEEDS),
                      "formal_result_bytes": len(payload), "formal_result_sha256": sha(payload)},
                     sort_keys=True))


if __name__ == "__main__":
    main()
