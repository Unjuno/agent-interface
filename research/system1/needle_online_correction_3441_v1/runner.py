"""Frozen CPU-only online correction/retention experiment for Issue #4824."""
from __future__ import annotations

import hashlib
import json
import random
import time
from pathlib import Path

import torch

ALLOCATION = "needle-online-correction-forgetting-3441-v1"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
SEEDS = (68117, 68229, 68341)
OUT = Path("/out/formal")
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)


def data(seed: int, salt: int, n: int) -> tuple[torch.Tensor, torch.Tensor]:
    rng = random.Random(seed * 1009 + salt)
    first = [0, 1] * (n // 2)
    if salt != 101:
        rng.shuffle(first)
    rows = [[bit, *[rng.randrange(2) for _ in range(7)]] for bit in first]
    targets = [int(row[0] == 1) for row in rows]
    return torch.tensor(rows, dtype=torch.float32), torch.tensor(targets, dtype=torch.long)


def digest(tensors: list[torch.Tensor]) -> str:
    h = hashlib.sha256()
    for tensor in tensors:
        byte_values = tensor.detach().contiguous().cpu().view(torch.uint8).flatten().tolist()
        h.update(bytes(byte_values))
    return h.hexdigest()


def metrics(logits: torch.Tensor, labels: torch.Tensor) -> dict:
    loss = torch.nn.functional.cross_entropy(logits, labels).item()
    accuracy = (logits.argmax(dim=1) == labels).float().mean().item()
    return {"accuracy": accuracy, "cross_entropy": loss, "n": int(labels.numel())}


def route(scope: str, epoch: int, current_epoch: int, calls: list[int]) -> dict:
    if scope not in ("A", "B") or epoch != current_epoch:
        return {"decision": "YIELD", "authority": False, "model_calls": 0}
    calls[0] += 1
    return {"decision": "PROPOSAL", "authority": False, "model_calls": 1}


def train_seed(seed: int) -> dict:
    torch.manual_seed(seed)
    support_x, _ = data(seed, 101, 16)
    support_a = torch.zeros(16, dtype=torch.long)
    held_a_x, held_a_y = data(seed, 211, 256)
    held_b_x, held_b_y = data(seed, 307, 256)

    w1 = torch.nn.Parameter(torch.randn(8, 16) * 0.15)
    b1 = torch.nn.Parameter(torch.zeros(16))
    w2 = torch.nn.Parameter(torch.randn(16, 4) * 0.15)
    b2 = torch.nn.Parameter(torch.zeros(4))
    base_params = [w1, b1, w2, b2]
    base_optimizer = torch.optim.AdamW(base_params, lr=0.03, weight_decay=1e-4)
    start = time.perf_counter_ns()
    for _ in range(400):
        base_optimizer.zero_grad(set_to_none=True)
        hidden = torch.tanh(support_x @ w1 + b1)
        loss = torch.nn.functional.cross_entropy(hidden @ w2 + b2, support_a)
        loss.backward()
        base_optimizer.step()
    base_train_ns = time.perf_counter_ns() - start
    for parameter in base_params:
        parameter.requires_grad_(False)

    adapter_a = torch.nn.Parameter(torch.randn(16, 2) * 0.1)
    adapter_b = torch.nn.Parameter(torch.zeros(2, 4))
    adapter_optimizer = torch.optim.AdamW([adapter_a, adapter_b], lr=0.04, weight_decay=1e-4)

    def base_logits(x: torch.Tensor) -> torch.Tensor:
        return torch.tanh(x @ w1 + b1) @ w2 + b2

    def candidate_logits(x: torch.Tensor) -> torch.Tensor:
        hidden = torch.tanh(x @ w1 + b1)
        return hidden @ w2 + b2 + (hidden @ adapter_a @ adapter_b) / 2.0

    base_digest = digest(base_params)
    snapshots = []
    curves = []
    controls = []
    correction_rows = []
    total_update_ns = []
    for step in range(9):
        with torch.no_grad():
            a_logits = candidate_logits(held_a_x)
            b_logits = candidate_logits(held_b_x)
            inference_start = time.perf_counter_ns()
            _ = candidate_logits(held_b_x)
            inference_ns = time.perf_counter_ns() - inference_start
        curves.append({
            "step": step,
            "A": metrics(a_logits, held_a_y),
            "B": metrics(b_logits, held_b_y),
            "update_ns": total_update_ns[-1] if step else 0,
            "inference_batch_ns": inference_ns,
            "inference_per_example_ns": inference_ns / 256,
            "A_logits": a_logits.tolist(),
            "B_logits": b_logits.tolist(),
        })
        snapshots.append({"A": adapter_a.detach().tolist(), "B": adapter_b.detach().tolist()})
        calls = [0]
        controls.append({
            "step": step,
            "base_route_A": route("A", step, step, calls),
            "online_route_B": route("B", step, step, calls),
            "unknown_scope": route("unknown", step, step, calls),
            "stale_epoch": route("B", step - 1, step, calls),
            "model_calls_total": calls[0],
        })
        if step == 8:
            break
        # Eight precommitted, class-balanced B corrections: support indices 0..7.
        x = support_x[step:step + 1]
        y = torch.tensor([int(support_x[step, 0].item())], dtype=torch.long)
        update_start = time.perf_counter_ns()
        adapter_optimizer.zero_grad(set_to_none=True)
        update_loss = torch.nn.functional.cross_entropy(candidate_logits(x), y)
        update_loss.backward()
        adapter_optimizer.step()
        total_update_ns.append(time.perf_counter_ns() - update_start)
        correction_rows.append({"arrival": step + 1, "features": x[0].tolist(), "target": int(y.item()),
                                "loss_before_update": float(update_loss.item())})

    base_after = digest(base_params)
    return {
        "seed": seed,
        "support_features": support_x.tolist(),
        "heldout_A_features": held_a_x.tolist(),
        "heldout_A_targets": held_a_y.tolist(),
        "heldout_B_features": held_b_x.tolist(),
        "heldout_B_targets": held_b_y.tolist(),
        "base_parameters": [p.detach().tolist() for p in base_params],
        "base_sha256_before": base_digest,
        "base_sha256_after": base_after,
        "base_train_steps": 400,
        "base_train_ns": base_train_ns,
        "correction_rows": correction_rows,
        "adapter_snapshots": snapshots,
        "curves": curves,
        "scope_controls": controls,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=False)
    result = {
        "schema": "needle-online-correction-raw-v1",
        "allocation": ALLOCATION,
        "image_id": IMAGE_ID,
        "platform": "linux/amd64",
        "torch": torch.__version__,
        "threads": torch.get_num_threads(),
        "device": "cpu",
        "seeds": [train_seed(seed) for seed in SEEDS],
        "authority": False,
        "input_emissions": 0,
        "scope": "three synthetic seeds; hidden-16 tanh classifier; one rank-2 output adapter; proposal-only",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    (OUT / "raw.json").write_text(payload, encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "seeds": len(result["seeds"]),
                      "curves_per_seed": [len(s["curves"]) for s in result["seeds"]],
                      "base_hashes_equal": [s["base_sha256_before"] == s["base_sha256_after"] for s in result["seeds"]],
                      "device": result["device"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
