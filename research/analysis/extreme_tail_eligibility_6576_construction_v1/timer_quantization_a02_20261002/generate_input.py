"""Generate the frozen 90-fixture input before candidate execution."""
import json
import random
from pathlib import Path

SEEDS = list(range(65761201, 65761231))
ARMS = (("continuous", 0.0), ("quantum_025", 0.25), ("quantum_100", 1.0))
N = 4000


def main():
    cases = []
    for arm_index, (arm, quantum) in enumerate(ARMS):
        for seed in SEEDS:
            rng = random.Random(seed + arm_index * 1000)
            latent = [rng.expovariate(1.0) for _ in range(N)]
            observed = latent if quantum == 0 else [round(x / quantum) * quantum for x in latent]
            cases.append({"arm": arm, "quantum": quantum, "seed": seed, "observed": observed})
    Path("input.json").write_text(json.dumps({"schema": "unjuno.6576.timer-quantization-a02.v1", "n": N, "cases": cases}, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
