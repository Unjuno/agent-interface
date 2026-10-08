"""Single-shot CUDA candidate for explicit-role online LoRA adaptation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import torch
from torch import nn
from torch.nn import functional as F


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest_object(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


class Base(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.fc1 = nn.Linear(9, 16)
        self.fc2 = nn.Linear(16, 4)

    def hidden(self, x: torch.Tensor) -> torch.Tensor:
        return F.relu(self.fc1(x))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(self.hidden(x))


def state_list(module: Base) -> dict:
    return {key: value.detach().cpu().tolist() for key, value in module.state_dict().items()}


def accuracy(preds: list[int], rows: list[dict]) -> dict:
    return {"correct": sum(int(p == row["label"]) for p, row in zip(preds, rows, strict=True)),
            "total": len(rows)}


def scope_decision(scope: str, fresh: bool, intent_match: bool = True) -> str:
    return "PROPOSE" if scope == "known" and fresh and intent_match else "YIELD"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, default=Path("/src"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit("STOP_CANDIDATE_OUTPUT_ALREADY_EXISTS")
    if args.freeze.parent.resolve() != args.source_dir.resolve():
        raise SystemExit("STOP_FREEZE_SOURCE_DIRECTORY_MISMATCH")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    for name, expected_sha in freeze["sha256"].items():
        if digest(args.source_dir / name) != expected_sha:
            raise SystemExit(f"STOP_FROZEN_SHA256_MISMATCH:{name}")
    if digest(args.dataset) != freeze["dataset_sha256"]:
        raise SystemExit("STOP_DATASET_SHA256_MISMATCH")
    if not torch.cuda.is_available():
        raise SystemExit("STOP_CUDA_UNAVAILABLE")
    device = torch.device("cuda:0")
    gpu = torch.cuda.get_device_name(device)
    if "RTX 3080" not in gpu:
        raise SystemExit(f"STOP_UNEXPECTED_GPU:{gpu}")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(1)

    deck = json.loads(args.dataset.read_text(encoding="utf-8"))
    result = {"schema": "unjuno.needle.role-context-candidate.v1",
              "dataset_sha256": digest(args.dataset), "gpu_name": gpu,
              "torch_version": torch.__version__, "cuda_version": torch.version.cuda,
              "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
              "seeds": []}

    for seed_data in deck["seeds"]:
        seed = seed_data["seed"]
        torch.manual_seed(seed + 11)
        torch.cuda.manual_seed_all(seed + 11)
        base = Base().to(device)
        if any(param.device.type != "cuda" for param in base.parameters()):
            raise SystemExit(f"STOP_BASE_NOT_ON_CUDA:{seed}")
        support = seed_data["splits"]["a_support"]
        x = torch.tensor([[0, *row["features"]] for row in support], dtype=torch.float32, device=device)
        y = torch.tensor([row["label"] for row in support], dtype=torch.long, device=device)
        base_optimizer = torch.optim.AdamW(base.parameters(), lr=0.04)
        for _ in range(400):
            base_optimizer.zero_grad(set_to_none=True)
            F.cross_entropy(base(x), y).backward()
            base_optimizer.step()
        for parameter in base.parameters():
            parameter.requires_grad_(False)
        base_initial = state_list(base)
        base_sha = digest_object(base_initial)

        arms = {}
        for arm in ("unconditioned", "role_gated"):
            torch.manual_seed(seed + (101 if arm == "unconditioned" else 202))
            torch.cuda.manual_seed_all(seed + (101 if arm == "unconditioned" else 202))
            adapter_a = nn.Parameter(torch.randn(2, 16, device=device) * 0.01)
            adapter_b = nn.Parameter(torch.zeros(4, 2, device=device))
            optimizer = torch.optim.AdamW([adapter_a, adapter_b], lr=0.04)
            gated = arm == "role_gated"

            def infer(rows: list[dict], role: int) -> list[int]:
                actual_role = role if gated else 0
                batch = torch.tensor([[actual_role, *row["features"]] for row in rows],
                                     dtype=torch.float32, device=device)
                with torch.no_grad():
                    hidden = base.hidden(batch)
                    logits = base.fc2(hidden)
                    if not gated or role == 1:
                        logits = logits + (hidden @ adapter_a.T) @ adapter_b.T
                    return logits.argmax(dim=1).detach().cpu().tolist()

            checkpoints = []
            arrivals = seed_data["splits"]["b_arrival"]
            for update_index in range(9):
                torch.cuda.synchronize()
                started = time.perf_counter()
                predictions_a = infer(seed_data["splits"]["a_heldout"], 0)
                predictions_b = infer(seed_data["splits"]["b_heldout"], 1)
                torch.cuda.synchronize()
                if digest_object(state_list(base)) != base_sha:
                    raise SystemExit(f"STOP_BASE_CHANGED:{seed}:{arm}")
                checkpoints.append({
                    "update_index": update_index,
                    "adapter_a": adapter_a.detach().cpu().tolist(),
                    "adapter_b": adapter_b.detach().cpu().tolist(),
                    "base_sha256": base_sha,
                    "predictions_a": predictions_a,
                    "predictions_b": predictions_b,
                    "accuracy_a": accuracy(predictions_a, seed_data["splits"]["a_heldout"]),
                    "accuracy_b": accuracy(predictions_b, seed_data["splits"]["b_heldout"]),
                    "evaluation_ms": (time.perf_counter() - started) * 1000.0,
                })
                if update_index == 8:
                    break
                arrival = arrivals[update_index]
                role = int(gated)
                one = torch.tensor([[role, *arrival["features"]]], dtype=torch.float32, device=device)
                label = torch.tensor([arrival["label"]], dtype=torch.long, device=device)
                optimizer.zero_grad(set_to_none=True)
                hidden = base.hidden(one)
                logits = base.fc2(hidden) + (hidden @ adapter_a.T) @ adapter_b.T
                F.cross_entropy(logits, label).backward()
                optimizer.step()
            arms[arm] = {"checkpoints": checkpoints}

        scope_inputs = {
            "fresh_known": {"scope": "known", "fresh": True, "intent_match": True},
            "stale_known": {"scope": "known", "fresh": False, "intent_match": True},
            "unknown_scope": {"scope": "unknown", "fresh": True, "intent_match": True},
            "intent_mismatch": {"scope": "known", "fresh": True, "intent_match": False},
        }
        scope_cases = {name: {**inputs, "decision": scope_decision(**inputs)}
                       for name, inputs in scope_inputs.items()}
        scope_cases["dispatch_count"] = 0
        result["seeds"].append({"seed": seed, "base_initial": base_initial,
                                "arms": arms, "scope_cases": scope_cases})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical(result))
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "seed_count": len(result["seeds"]),
                      "gpu": gpu, "dataset_sha256": result["dataset_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
