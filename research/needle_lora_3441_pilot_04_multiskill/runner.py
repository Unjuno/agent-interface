"""Frozen synthetic multi-skill LoRA routing allocation for Issue #3701."""
from __future__ import annotations

import hashlib
import io
import json
import random
import statistics
import time

import torch
from torch import nn


SEED = 3443
FEATURES, HIDDEN, CLASSES = 8, 16, 4
SUPPORT_ROWS, HELDOUT_ROWS = 16, 4096
PRETRAIN_ROWS, UPDATE_STEPS, BATCH = 512, 120, 32
BASE_LR, ADAPTER_LR, RANK = 0.025, 0.04, 2
CURRENT_EPOCH = 7
INTERFERENCE_DELTA = 0.10


def make_x(rows: int, seed: int, device: torch.device) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    return torch.randn(rows, FEATURES, generator=generator).to(device)


def labels(x: torch.Tensor, skill: str) -> torch.Tensor:
    bit0 = (x[:, 0] > 0).long()
    bit1 = (x[:, 1] > 0).long()
    if skill in ("skill_b", "shared_b"):
        bit0 = 1 - bit0
    elif skill in ("skill_c", "shared_c"):
        bit1 = 1 - bit1
    elif skill != "skill_a":
        raise ValueError(f"unknown synthetic label skill: {skill}")
    return bit0 * 2 + bit1


class BasePolicy(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(FEATURES, HIDDEN), nn.Tanh())
        self.head = nn.Linear(HIDDEN, CLASSES)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(x))


class RankTwoAdapter(nn.Module):
    def __init__(self, base: BasePolicy) -> None:
        super().__init__()
        self.base = base
        for parameter in self.base.parameters():
            parameter.requires_grad_(False)
        self.lora_a = nn.Parameter(torch.randn(HIDDEN, RANK) * 0.04)
        self.lora_b = nn.Parameter(torch.zeros(RANK, CLASSES))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        hidden = self.base.encoder(x)
        return self.base.head(hidden) + (hidden @ self.lora_a @ self.lora_b) / RANK


def state_copy(model: nn.Module) -> dict[str, torch.Tensor]:
    return {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}


def tensor_state_equal(left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]) -> bool:
    return left.keys() == right.keys() and all(torch.equal(left[key], right[key]) for key in left)


def snapshot_bytes(state: dict[str, torch.Tensor]) -> bytes:
    stream = io.BytesIO()
    torch.save(state, stream)
    return stream.getvalue()


def train_steps(
    model: nn.Module,
    x: torch.Tensor,
    y: torch.Tensor,
    optimizer: torch.optim.Optimizer,
    steps: int,
    seed: int,
    device: torch.device,
) -> float:
    generator = torch.Generator().manual_seed(seed)
    model.train()
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    start = time.perf_counter_ns()
    for _ in range(steps):
        indices = torch.randint(len(x), (BATCH,), generator=generator).to(device)
        loss = nn.functional.cross_entropy(model(x[indices]), y[indices])
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    return (time.perf_counter_ns() - start) / 1e6


def make_optimizer(model: nn.Module, lr: float) -> torch.optim.Optimizer:
    return torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr)


def accuracy(model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> float:
    model.eval()
    with torch.no_grad():
        return float((model(x).argmax(-1) == y).float().mean().item())


def route(skill: str, receipt: object, base: BasePolicy,
          adapters: dict[str, RankTwoAdapter]) -> tuple[str, nn.Module | None]:
    if type(receipt) is not dict or type(receipt.get("epoch")) is not int:
        return "YIELD", None
    if receipt["epoch"] != CURRENT_EPOCH:
        return "YIELD", None
    expected = {
        "skill_a": ("base", 0, base),
        "skill_b": ("adapter-b", 1, adapters.get("adapter-b")),
        "skill_c": ("adapter-c", 1, adapters.get("adapter-c")),
    }.get(skill)
    if expected is None:
        return "YIELD", None
    adapter_id, version, model = expected
    if model is None or receipt.get("adapter_id") != adapter_id:
        return "YIELD", None
    if type(receipt.get("adapter_version")) is not int or receipt["adapter_version"] != version:
        return "YIELD", None
    return "PROPOSE", model


def main() -> None:
    random.seed(SEED)
    torch.manual_seed(SEED)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.cuda.manual_seed_all(SEED)

    # Fixed, disjoint deterministic data streams: A pretrain, B/C supports, A/B/C held-out.
    x_pre = make_x(PRETRAIN_ROWS, SEED + 1, device)
    x_support = {
        "skill_b": make_x(SUPPORT_ROWS, SEED + 2, device),
        "skill_c": make_x(SUPPORT_ROWS, SEED + 3, device),
    }
    x_eval = {
        "skill_a": make_x(HELDOUT_ROWS, SEED + 4, device),
        "skill_b": make_x(HELDOUT_ROWS, SEED + 5, device),
        "skill_c": make_x(HELDOUT_ROWS, SEED + 6, device),
    }
    y_pre = labels(x_pre, "skill_a")
    y_support = {name: labels(x, name) for name, x in x_support.items()}
    y_eval = {name: labels(x, name) for name, x in x_eval.items()}

    base = BasePolicy().to(device)
    base_optimizer = make_optimizer(base, BASE_LR)
    pretrain_ms = train_steps(base, x_pre, y_pre, base_optimizer, 400, SEED + 10, device)
    base_before = state_copy(base)

    # Dedicated adapters are initialized in the preregistered B-then-C order.
    dedicated: dict[str, RankTwoAdapter] = {}
    initial: dict[str, dict[str, torch.Tensor]] = {}
    update_ms: dict[str, float] = {}
    learned_payloads: dict[str, bytes] = {}
    for index, (skill, adapter_id) in enumerate((("skill_b", "adapter-b"), ("skill_c", "adapter-c"))):
        torch.manual_seed(SEED + 20 + index)
        if device.type == "cuda":
            torch.cuda.manual_seed_all(SEED + 20 + index)
        model = RankTwoAdapter(base).to(device)
        dedicated[adapter_id] = model
        initial[adapter_id] = state_copy(model)
        update_ms[skill] = train_steps(
            model, x_support[skill], y_support[skill], make_optimizer(model, ADAPTER_LR),
            UPDATE_STEPS, SEED + 30 + index, device,
        )
        learned = state_copy(model)
        learned_payloads[adapter_id] = snapshot_bytes(learned)

    # One adapter receives B then C sequentially with a single retained optimizer state.
    # Match adapter-B initialization exactly so the shared arm differs by only the C update.
    torch.manual_seed(SEED + 20)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(SEED + 20)
    shared = RankTwoAdapter(base).to(device)
    shared_optimizer = make_optimizer(shared, ADAPTER_LR)
    shared_b_ms = train_steps(shared, x_support["skill_b"], y_support["skill_b"],
                              shared_optimizer, UPDATE_STEPS, SEED + 30, device)
    shared_c_ms = train_steps(shared, x_support["skill_c"], y_support["skill_c"],
                              shared_optimizer, UPDATE_STEPS, SEED + 31, device)

    routed: dict[str, float] = {}
    global_shared: dict[str, float] = {}
    valid_receipts = {
        "skill_a": {"epoch": CURRENT_EPOCH, "adapter_id": "base", "adapter_version": 0},
        "skill_b": {"epoch": CURRENT_EPOCH, "adapter_id": "adapter-b", "adapter_version": 1},
        "skill_c": {"epoch": CURRENT_EPOCH, "adapter_id": "adapter-c", "adapter_version": 1},
    }
    for skill in ("skill_a", "skill_b", "skill_c"):
        decision, selected = route(skill, valid_receipts[skill], base, dedicated)
        assert decision == "PROPOSE" and selected is not None
        routed[skill] = accuracy(selected, x_eval[skill], y_eval[skill])
        global_shared[skill] = accuracy(shared, x_eval[skill], y_eval[skill])

    # Exact CPU tensor comparison after independently loading each learned snapshot.
    roundtrip_exact: dict[str, bool] = {}
    rollback_exact: dict[str, bool] = {}
    snapshot_sha256: dict[str, str] = {}
    snapshot_bytes_count: dict[str, int] = {}
    for adapter_id, model in dedicated.items():
        payload = learned_payloads[adapter_id]
        learned_state = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
        expected = state_copy(model)
        restored_model = RankTwoAdapter(base).to(device)
        restored_model.load_state_dict(learned_state)
        roundtrip_exact[adapter_id] = tensor_state_equal(state_copy(restored_model), expected)
        snapshot_sha256[adapter_id] = hashlib.sha256(payload).hexdigest()
        snapshot_bytes_count[adapter_id] = len(payload)
        model.load_state_dict(initial[adapter_id])
        rollback_exact[adapter_id] = tensor_state_equal(state_copy(model), initial[adapter_id])

    base_immutable = tensor_state_equal(state_copy(base), base_before)
    invalid_receipts = {
        "unknown_skill": route("unknown", valid_receipts["skill_b"], base, dedicated)[0],
        "stale_epoch": route("skill_b", {**valid_receipts["skill_b"], "epoch": CURRENT_EPOCH - 1}, base, dedicated)[0],
        "wrong_adapter_identity": route("skill_b", {**valid_receipts["skill_b"], "adapter_id": "adapter-c"}, base, dedicated)[0],
        "missing_adapter_identity": route("skill_c", {"epoch": CURRENT_EPOCH, "adapter_version": 1}, base, dedicated)[0],
        "wrong_adapter_version": route("skill_c", {**valid_receipts["skill_c"], "adapter_version": 2}, base, dedicated)[0],
        "missing_adapter_version": route("skill_b", {"epoch": CURRENT_EPOCH, "adapter_id": "adapter-b"}, base, dedicated)[0],
    }

    # Keep timing limited to deterministic dispatch; no inference is included.
    dispatch_block_means_ms: list[float] = []
    for _ in range(5):
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        start = time.perf_counter_ns()
        for _ in range(200):
            route("skill_c", valid_receipts["skill_c"], base, dedicated)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        dispatch_block_means_ms.append((time.perf_counter_ns() - start) / 200e6)

    drops = {skill: routed[skill] - global_shared[skill] for skill in routed}
    measurable_global_interference = any(delta >= INTERFERENCE_DELTA for delta in drops.values())
    thresholds_pass = all(value >= 0.90 for value in routed.values())
    invalid_routes_fail_closed = all(value == "YIELD" for value in invalid_receipts.values())
    roundtrip_pass = all(roundtrip_exact.values())
    rollback_pass = all(rollback_exact.values())
    routing_pass = thresholds_pass and invalid_routes_fail_closed and roundtrip_pass and rollback_pass and base_immutable
    outcome = (
        "FAIL_SNAPSHOT_INTEGRITY" if not roundtrip_pass or not rollback_pass else
        "PASS_MULTI_SKILL_ROUTING_SCOPED" if routing_pass else
        "FAIL_MULTI_SKILL_INTERFERENCE"
    )

    output = {
        "allocation": "needle-lora-3441-pilot-04-multiskill",
        "outcome": outcome,
        "hypothesis_assessment": "SHARED_ADAPTER_INTERFERENCE_OBSERVED" if measurable_global_interference else "SHARED_ADAPTER_INTERFERENCE_NOT_OBSERVED_AT_0_10_THRESHOLD",
        "seed": SEED,
        "device": {
            "name": torch.cuda.get_device_name(device) if device.type == "cuda" else "CPU fallback",
            "type": str(device),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "execution": "Windows host; Docker Desktop Linux engine unavailable",
            "cuda_peak_memory": "unavailable/not measured (WDDM-safe preregistration)",
        },
        "parameters": {
            "features": FEATURES, "hidden": HIDDEN, "classes": CLASSES,
            "pretrain_rows": PRETRAIN_ROWS, "support_rows_per_new_skill": SUPPORT_ROWS,
            "heldout_rows_per_skill": HELDOUT_ROWS, "rank": RANK,
            "steps_per_adapter_skill": UPDATE_STEPS, "optimizer": "AdamW",
            "base_learning_rate": BASE_LR, "adapter_learning_rate": ADAPTER_LR,
            "global_update_order": ["skill_b", "skill_c"],
            "global_update_steps_per_skill": UPDATE_STEPS,
        },
        "measurements": {
            "pretrain_ms": pretrain_ms,
            "dedicated_update_ms": update_ms,
            "shared_update_ms": {"skill_b": shared_b_ms, "skill_c": shared_c_ms},
            "routed_accuracy": routed,
            "shared_adapter_accuracy_after_b_then_c": global_shared,
            "routed_minus_shared_accuracy": drops,
            "measurable_shared_interference_threshold": INTERFERENCE_DELTA,
            "snapshot_sha256": snapshot_sha256,
            "snapshot_bytes": snapshot_bytes_count,
            "dispatcher_200_call_block_means_ms": dispatch_block_means_ms,
            "dispatcher_block_mean_p50_ms": statistics.median(dispatch_block_means_ms),
        },
        "checks": {
            "routed_thresholds_ge_0_90": thresholds_pass,
            "invalid_routes": invalid_receipts,
            "invalid_routes_fail_closed": invalid_routes_fail_closed,
            "base_immutable": base_immutable,
            "snapshot_roundtrip_tensor_exact": roundtrip_exact,
            "rollback_tensor_exact": rollback_exact,
        },
        "scope": "single synthetic seed/task; proposal dispatch only; no GUI, vision, or action authority",
        "limits": [
            "No realistic task/role transfer, concurrent adapter writes, crash-safe persistence, vision/GUI, or action safety claim.",
            "Dispatcher-only timing excludes inference and model-loading latency.",
            "Host-GPU outcome is not a Docker/container pass.",
        ],
    }
    print(json.dumps(output, sort_keys=True, indent=2) + "\n", end="")


if __name__ == "__main__":
    main()
