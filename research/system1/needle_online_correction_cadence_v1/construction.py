"""One non-formal, distinct-seed smoke; never part of the three-seed result."""
import hashlib
import json
import os
from pathlib import Path

import torch

import runner

SEED = 734014  # Auditor-only construction seed; excluded from the formal block.


def main():
    if not os.environ.get("NEEDLE_OUTPUT"):
        raise SystemExit("STOP_INVALID_CONSTRUCTION_ENV")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    result = runner.run_seed(SEED)
    summary = {"seed": SEED, "formal_seed": False, "base_immutable": result["base_immutable"],
               "arms": []}
    for arm in result["arms"]:
        final = arm["arrivals"][-1]
        summary["arms"].append({
            "arm": arm["arm"], "optimizer_steps": arm["optimizer_steps"],
            "final_A_accuracy": sum(x == y for x, y in zip(final["pred_a"], result["test_a_y"])) / 256,
            "final_B_accuracy": sum(x == y for x, y in zip(final["pred_b"], result["test_b_y"])) / 256,
            "max_update_ms": max(arm["update_ns"]) / 1_000_000,
            "max_burst_ms": max(arm["burst_ns"]) / 1_000_000,
        })
    data = json.dumps(summary, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    target = Path(os.environ["NEEDLE_OUTPUT"]) / "construction.json"
    with target.open("xb") as f:
        f.write(data)
    raw = json.dumps({"seed": SEED, "run": result}, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode() + b"\n"
    raw_target = Path(os.environ["NEEDLE_OUTPUT"]) / "construction_raw.json"
    with raw_target.open("xb") as f:
        f.write(raw)
    print(json.dumps({"construction_sha256": hashlib.sha256(data).hexdigest(),
                      "construction_bytes": len(data), "raw_sha256": hashlib.sha256(raw).hexdigest(),
                      "raw_bytes": len(raw), "seed": SEED}, sort_keys=True))


if __name__ == "__main__":
    main()
