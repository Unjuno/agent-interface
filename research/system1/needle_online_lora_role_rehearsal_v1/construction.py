"""Excluded full-pipeline construction run; formal seeds are never used."""
import os
from pathlib import Path

import torch

import runner


def main():
    seed = 735014
    destination = os.environ.get("NEEDLE_CONSTRUCTION_OUTPUT", "")
    if not destination:
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_MISSING")
    out = Path(destination)
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    run = runner.run_seed(seed)
    payload = runner.canonical({"formal": False, "seed": seed, "run": run}) + b"\n"
    with (out / "construction_raw.json").open("xb") as stream:
        stream.write(payload)
    print(__import__("json").dumps({"formal": False, "seed": seed,
                                     "optimizer_updates": 400 + 3 * 128,
                                     "bytes": len(payload),
                                     "sha256": runner.sha(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
