"""Role-network routing between an immutable A skill and online LoRA skill B."""
import hashlib
import json
import os
import platform
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

ALLOCATION = "needle-role-skill-joint-retention-20260928-v4"
SEEDS = (9944211, 9944311, 9944411)
ARMS = ("SHARED_B_ONLY", "SHARED_A_REPLAY", "ROUTED_SHARED_ADAPTER", "ROUTED_SEPARATE_SKILLS")
SCHEMA = "needle-role-skill-joint-retention-raw-v2"
ROLES = ("A", "B")
SCOPE = "synthetic-role-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(canonical(value))


DATASET_FIELDS = ("base_train_x", "base_train_y", "base_row_indices", "memory_x", "memory_y",
                  "support_x", "support_y", "test_a_x", "test_a_y", "test_b_x", "test_b_y")


def dataset_hashes(fields):
    if set(fields) != set(DATASET_FIELDS):
        raise ValueError("dataset_hash_key_set_mismatch")
    return {key: sha(canonical(fields[key])) for key in DATASET_FIELDS}


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


def route(role, scope, generation, expected_generation, separate_skills=True):
    if role not in ROLES or scope != SCOPE or generation != expected_generation:
        return {"status": "YIELD", "selected_role": None, "adapter_id": None,
                "generation": generation, "proposal": None}
    if separate_skills:
        adapter = {"A": "skill-A-immutable-v1", "B": "skill-B-online-v1"}[role]
    else:
        adapter = "role-shared-online-v1"
    return {"status": "READY", "selected_role": role, "adapter_id": adapter,
            "generation": generation, "proposal": None}


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
        F.cross_entropy(model(x[index:index + 1]), y[index:index + 1]).backward()
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


def batch_for(arm, bx, by, a_x, a_y, a_ix):
    if arm in ("SHARED_B_ONLY", "ROUTED_SHARED_ADAPTER", "ROUTED_SEPARATE_SKILLS"):
        return bx.reshape(1, -1), by.reshape(1)
    if arm == "SHARED_A_REPLAY":
        return torch.stack((bx, a_x[a_ix])), torch.stack((by, a_y[a_ix]))
    raise ValueError("unknown_arm")


def fit_arm(arm, core, support_x, support_y, memory_x, memory_y, test_a, test_b, init):
    shared = arm != "ROUTED_SEPARATE_SKILLS"
    a_adapter, b_adapter = Adapter(), Adapter()
    with torch.no_grad():
        for adapter in (a_adapter, b_adapter):
            adapter.left.copy_(torch.tensor(init["left"], dtype=torch.float32))
            adapter.right.copy_(torch.tensor(init["right"], dtype=torch.float32))
    # Separate skills keep A immutable; only B's adapter owns an optimizer.
    if shared:
        optimizer = torch.optim.AdamW(a_adapter.parameters(), lr=0.04, weight_decay=1e-4)
        b_adapter = a_adapter
    else:
        optimizer = torch.optim.AdamW(b_adapter.parameters(), lr=0.04, weight_decay=1e-4)
    immutable_a = ({key: value.detach().clone() for key, value in a_adapter.state_dict().items()}
                   if not shared else None)
    arrivals, update_ns, routes, yield_controls = [], [], [], []
    for arrival in range(16):
        for step in range(8):
            index = arrival * 8 + step
            x, y = batch_for(arm, support_x[arrival], support_y[arrival], memory_x, memory_y, index % 16)
            if arm.startswith("ROUTED_"):
                receipt = route("B", SCOPE, 3, 3, separate_skills=not shared)
            else:
                receipt = {"status": "READY", "selected_role": "B", "adapter_id":
                           "shared-online-v1",
                           "generation": 3, "proposal": None}
            routes.append(receipt)
            selected = b_adapter if receipt["status"] == "READY" and receipt["adapter_id"] in (
                "skill-B-online-v1", "role-shared-online-v1", "shared-online-v1") else None
            if selected is None:
                raise RuntimeError("STOP_VALID_B_ROUTE_YIELDED")
            started = time.perf_counter_ns()
            optimizer.zero_grad(set_to_none=True)
            F.cross_entropy(selected(core, x), y).backward()
            optimizer.step()
            update_ns.append(time.perf_counter_ns() - started)
        controls = [route("UNKNOWN", SCOPE, 3, 3, not shared), route("B", SCOPE, 2, 3, not shared),
                    route("A", "wrong-scope", 3, 3, not shared)]
        yield_controls.append(controls)
        if any(item["status"] != "YIELD" or item["proposal"] is not None for item in controls):
            raise RuntimeError("STOP_INVALID_ROUTE_NOT_YIELDED")
        if (immutable_a is not None and
                any(not torch.equal(value, a_adapter.state_dict()[key]) for key, value in immutable_a.items())):
            raise RuntimeError("STOP_A_SKILL_MUTATED")
        state = {"A": {"left": a_adapter.left.detach().tolist(), "right": a_adapter.right.detach().tolist()},
                 "B": {"left": b_adapter.left.detach().tolist(), "right": b_adapter.right.detach().tolist()}}
        role_routes = ([route("A", SCOPE, 3, 3, not shared),
                        route("B", SCOPE, 3, 3, not shared)] if arm.startswith("ROUTED_") else [])
        arrivals.append({"arrival": arrival + 1, "skills": state, "skills_sha256": digest(state),
                         "yield_controls": controls,
                         "role_routes": role_routes,
                         "optimizer": optimizer_state(optimizer, b_adapter),
                         "pred_a": predict(core, a_adapter, test_a),
                         "pred_b": predict(core, b_adapter, test_b)})
    return {"arm": arm, "optimizer_steps": len(update_ns), "update_ns": update_ns,
            "routes": routes, "yield_controls": yield_controls, "arrivals": arrivals,
            "final_optimizer": optimizer_state(optimizer, b_adapter),
            "a_adapter_immutable": immutable_a is None or all(
                torch.equal(value, a_adapter.state_dict()[key]) for key, value in immutable_a.items()),
            "a_adapter_identity": id(a_adapter) != id(b_adapter) if not shared else id(a_adapter) == id(b_adapter)}


def run_seed(seed):
    core, train_x, train_y, indices = train_base(seed)
    for parameter in core.parameters():
        parameter.requires_grad_(False)
    base = tensor_map(core)
    memory_x, support_x = sample(16, seed, 202, 0), sample(16, seed, 303, 1)
    memory_y, support_y = label_a(memory_x), label_b(support_x)
    test_a, test_b = sample(256, seed, 404, 0), sample(256, seed, 505, 1)
    torch.manual_seed(seed + 500)
    init = {"left": (torch.randn(16, 2) * 0.1).tolist(), "right": torch.zeros(2, 4).tolist()}
    arms = [fit_arm(arm, core, support_x, support_y, memory_x, memory_y, test_a, test_b, init)
            for arm in ARMS]
    data = {"base_train_x": train_x.tolist(), "base_train_y": train_y.tolist(), "base_row_indices": indices,
            "memory_x": memory_x.tolist(), "memory_y": memory_y.tolist(),
            "support_x": support_x.tolist(), "support_y": support_y.tolist(),
            "test_a_x": test_a.tolist(), "test_a_y": label_a(test_a).tolist(),
            "test_b_x": test_b.tolist(), "test_b_y": label_b(test_b).tolist()}
    return {"seed": seed, "base": base, "base_sha256": digest(base),
            "base_after_sha256": digest(tensor_map(core)), "base_immutable": base == tensor_map(core),
            "base_train_x": train_x.tolist(), "base_train_y": train_y.tolist(), "base_row_indices": indices,
            "memory_x": memory_x.tolist(), "memory_y": memory_y.tolist(),
            "support_x": support_x.tolist(), "support_y": support_y.tolist(),
            "test_a_x": test_a.tolist(), "test_a_y": label_a(test_a).tolist(),
            "test_b_x": test_b.tolist(), "test_b_y": label_b(test_b).tolist(),
            "dataset_sha256": dataset_hashes(data),
            "init_adapter": init, "arms": arms}


def main():
    output, seed_text = os.environ.get("NEEDLE_OUTPUT", ""), os.environ.get("NEEDLE_SEEDS", "")
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
    result = {"schema": SCHEMA, "allocation": ALLOCATION, "seeds": list(SEEDS), "arms": list(ARMS),
              "environment": {"platform": platform.platform(), "python": platform.python_version(),
                              "torch": torch.__version__, "device": "cpu", "threads": 1,
                              "interop_threads": 1}, "runs": [run_seed(seed) for seed in SEEDS]}
    payload = canonical(result) + b"\n"
    with (out / "formal_result.json").open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"allocation": ALLOCATION, "seeds": list(SEEDS),
                      "formal_result_bytes": len(payload), "formal_result_sha256": sha(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()

