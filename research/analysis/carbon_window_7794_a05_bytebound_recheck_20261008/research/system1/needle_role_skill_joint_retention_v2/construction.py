"""Excluded-seed full-pipeline smoke run; never uses a formal seed."""
import json
import os
from pathlib import Path

import torch

import runner


def main():
    seed = 736514
    target = os.environ.get("NEEDLE_CONSTRUCTION_OUTPUT", "")
    if not target:
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_MISSING")
    out = Path(target)
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    result = {"formal": False, "seed": seed, "run": runner.run_seed(seed)}
    payload = runner.canonical(result) + b"\n"
    (out / "construction_raw.json").write_bytes(payload)
    print(json.dumps({"formal": False, "seed": seed, "bytes": len(payload),
                      "sha256": runner.sha(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()

