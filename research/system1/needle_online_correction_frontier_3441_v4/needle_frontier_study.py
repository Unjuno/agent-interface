"""Frozen, CPU-only synthetic online-correction frontier study."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import torch
from torch import nn

SEEDS = (65117, 65229, 65341)
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
N = 256
ARRIVALS = 32
WIDTH = 16
STREAMS = {"train_A": 41017, "heldout_A": 42043, "heldout_B": 43051, "support_B": 44059}


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.l1 = nn.Linear(8, WIDTH)
        self.l2 = nn.Linear(WIDTH, 4)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.l2(torch.tanh(self.l1(x)))


class Candidate(nn.Module):
    def __init__(self, base: Net, seed: int):
        super().__init__()
        self.base = base
        self.a = nn.Parameter(torch.empty(4, 2))
        self.b = nn.Parameter(torch.zeros(2, WIDTH))
        gen = torch.Generator(device="cpu").manual_seed(seed)
        with torch.no_grad():
            self.a.copy_(torch.randn((4, 2), generator=gen) * 0.02)
        for parameter in self.base.parameters():
            parameter.requires_grad_(False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        hidden = torch.tanh(self.base.l1(x))
        return self.base.l2(hidden) + (hidden @ self.b.T @ self.a.T) * 0.25


def split(seed: int, name: str) -> tuple[torch.Tensor, torch.Tensor]:
    """Create one independently seeded balanced split; coordinate 0 is the task bit."""
    if name not in STREAMS:
        raise ValueError(f"unknown split: {name}")
    gen = torch.Generator(device="cpu").manual_seed(seed * 1009 + STREAMS[name])
    if name == "support_B":
        batches = []
        for _ in range(ARRIVALS):
            batch = torch.rand((8, 8), generator=gen)
            batch[:4, 0] = 0.0
            batch[4:, 0] = 1.0
            batches.append(batch[torch.randperm(8, generator=gen)])
        features = torch.stack(batches).reshape(N, 8)
    else:
        features = torch.rand((N, 8), generator=gen)
        features[: N // 2, 0] = 0.0
        features[N // 2 :, 0] = 1.0
        features = features[torch.randperm(N, generator=gen)]
    if name == "heldout_B":
        targets = 1 - features[:, 0].long()
    elif name == "support_B":
        targets = 1 - features[:, 0].long()
    else:
        targets = features[:, 0].long()
    return features, targets


def support_batches(seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    x, y = split(seed, "support_B")
    # Each contiguous eight rows becomes a fixed balanced correction minibatch.
    return x.reshape(ARRIVALS, 8, 8), y.reshape(ARRIVALS, 8)


def row_key(row: torch.Tensor | list[float]) -> tuple[float, ...]:
    return tuple(float(v) for v in (row.tolist() if isinstance(row, torch.Tensor) else row))


def assert_splits_disjoint(seed: int) -> None:
    named = {name: split(seed, name)[0] for name in ("train_A", "heldout_A", "heldout_B")}
    named["support_B"] = support_batches(seed)[0].reshape(-1, 8)
    keys = {name: {row_key(row) for row in rows} for name, rows in named.items()}
    for left_i, left in enumerate(keys):
        for right in list(keys)[left_i + 1 :]:
            if keys[left] & keys[right]:
                raise ValueError(f"row overlap between {left} and {right} for seed {seed}")
    if any(len(v) != N for v in keys.values()):
        raise ValueError(f"duplicate row within a split for seed {seed}")


def guard(model: Candidate, x: torch.Tensor, scope: str, epoch: int) -> dict:
    if scope != "B" or epoch != ARRIVALS:
        return {"decision": "YIELD", "authority": False, "model_calls": 0, "logits": None}
    with torch.no_grad():
        logits = model(x)
    return {"decision": "PROPOSAL", "authority": False, "model_calls": 1, "logits": logits.tolist()}


def tensor_digest(state: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        digest.update(name.encode("utf-8") + b"\0")
        raw = state[name].detach().cpu().contiguous().view(torch.uint8).flatten().tolist()
        digest.update(bytes(raw))
    return digest.hexdigest()


def state_lists(state: dict[str, torch.Tensor]) -> dict[str, list]:
    return {key: value.detach().cpu().tolist() for key, value in state.items()}


def run_seed(seed: int) -> dict:
    assert_splits_disjoint(seed)
    train_x, train_y = split(seed, "train_A")
    xa, ya = split(seed, "heldout_A")
    xb, yb = split(seed, "heldout_B")
    sx, sy = support_batches(seed)

    torch.manual_seed(seed + 1)
    base = Net()
    optimizer = torch.optim.AdamW(base.parameters(), lr=0.03)
    train_indices = [(step * 17 + seed) % N for step in range(400)]
    base_start = time.perf_counter_ns()
    for index in train_indices:
        optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(base(train_x[index : index + 1]), train_y[index : index + 1])
        loss.backward()
        optimizer.step()
    base_train_ms = (time.perf_counter_ns() - base_start) / 1e6

    frozen_state = {key: value.detach().clone() for key, value in base.state_dict().items()}
    model = Candidate(base, seed + 2)
    adapter_optimizer = torch.optim.AdamW([model.a, model.b], lr=0.04)
    curve, snapshots, update_ms, inference_ms = [], [], [], []

    def evaluate(step: int) -> None:
        started = time.perf_counter_ns()
        with torch.no_grad():
            logits_a = model(xa)
            logits_b = model(xb)
            base_logits = base(xa)
        inference_ms.append((time.perf_counter_ns() - started) / 1e6)
        curve.append({
            "step": step,
            "a_correct": int((logits_a.argmax(-1) == ya).sum()),
            "b_correct": int((logits_b.argmax(-1) == yb).sum()),
            "pred_a": logits_a.argmax(-1).tolist(),
            "pred_b": logits_b.argmax(-1).tolist(),
            "ce_a": float(nn.functional.cross_entropy(logits_a, ya)),
            "ce_b": float(nn.functional.cross_entropy(logits_b, yb)),
            "base_a_correct": int((base_logits.argmax(-1) == ya).sum()),
            "n": N,
            "logits_a": logits_a.tolist(),
            "logits_b": logits_b.tolist(),
        })
        snapshots.append({"a": model.a.detach().tolist(), "b": model.b.detach().tolist()})

    evaluate(0)
    for arrival in range(ARRIVALS):
        start = time.perf_counter_ns()
        adapter_optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(model(sx[arrival]), sy[arrival])
        loss.backward()
        adapter_optimizer.step()
        update_ms.append((time.perf_counter_ns() - start) / 1e6)
        evaluate(arrival + 1)

    controls = [
        guard(model, xb[0:1], "B", ARRIVALS),
        guard(model, xb[0:1], "unknown", ARRIVALS),
        guard(model, xb[0:1], "B", ARRIVALS - 1),
    ]
    return {
        "seed": seed,
        "base_train_steps": 400,
        "base_train_indices": train_indices,
        "base_train_ms": base_train_ms,
        "train_x": train_x.tolist(),
        "train_y": train_y.tolist(),
        "x_a": xa.tolist(),
        "y_a": ya.tolist(),
        "x_b": xb.tolist(),
        "y_b": yb.tolist(),
        "support_x": sx.tolist(),
        "support_y": sy.tolist(),
        "base_state": state_lists(frozen_state),
        "base_state_sha256": tensor_digest(frozen_state),
        "base_after_sha256": tensor_digest(base.state_dict()),
        "curve": curve,
        "snapshots": snapshots,
        "update_ms": update_ms,
        "inference_ms": inference_ms,
        "controls": controls,
    }


def run() -> dict:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.__version__ != "2.5.1+cpu" or platform.python_version() != "3.12.14":
        raise RuntimeError("pinned Python/PyTorch runtime mismatch")
    return {
        "schema": "needle-online-correction-frontier-v4",
        "runtime": {
            "image_id": IMAGE_ID,
            "platform": "linux/amd64",
            "python": platform.python_version(),
            "torch": torch.__version__,
            "device": "cpu",
            "threads": torch.get_num_threads(),
            "network": "none",
        },
        "stream_salts": STREAMS,
        "runs": [run_seed(seed) for seed in SEEDS],
        "authority": False,
        "input_emissions": 0,
    }


def write_raw(document: dict, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"formal output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, separators=(",", ":"), allow_nan=False) + "\n"
    output.write_text(payload, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = run()
    write_raw(document, args.output)
    print(json.dumps({
        "schema": document["schema"],
        "seeds": [row["seed"] for row in document["runs"]],
        "curves_per_seed": [len(row["curve"]) for row in document["runs"]],
        "base_immutable": [row["base_state_sha256"] == row["base_after_sha256"] for row in document["runs"]],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
