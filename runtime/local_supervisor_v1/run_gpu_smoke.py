"""Tiny deterministic GPU construction/inference smoke; no GUI authority."""
from __future__ import annotations

import json
import time
import torch

from .supervisor import FEATURES, SupervisorNet


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("CUDA_UNAVAILABLE")
    torch.manual_seed(2508)
    device = torch.device("cuda")
    model = SupervisorNet().to(device).eval()
    x = torch.zeros((1, FEATURES), device=device)
    for _ in range(20):
        model(x)
    torch.cuda.synchronize()
    started = time.perf_counter_ns()
    with torch.inference_mode():
        for _ in range(1000):
            model(x)
    torch.cuda.synchronize()
    elapsed_ms = (time.perf_counter_ns() - started) / 1e6
    print(json.dumps({
        "schema": "local-supervisor-gpu-smoke-v1",
        "status": "PASS_GPU_OPTIONAL_SUPERVISOR_SMOKE",
        "device": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
        "parameters": sum(p.numel() for p in model.parameters()),
        "inferences": 1000,
        "elapsed_ms": elapsed_ms,
        "authority_grants": 0,
        "output_space": ["CONTINUE", "YIELD"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
