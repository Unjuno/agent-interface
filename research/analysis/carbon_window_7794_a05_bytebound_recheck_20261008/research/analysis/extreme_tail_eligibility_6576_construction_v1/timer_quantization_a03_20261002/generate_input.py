"""Generate frozen A03 quantization-cutoff fixtures before candidate execution."""
import json
import random
from pathlib import Path

SEEDS = list(range(65761301, 65761351))
ARMS = (("continuous", 0.0), ("quantum_025", 0.25), ("quantum_050", 0.5), ("quantum_100", 1.0))
N = 4000


def main():
    cases = []
    for arm_index, (arm, quantum) in enumerate(ARMS):
        for seed in SEEDS:
            rng = random.Random(seed + arm_index * 10000)
            latent = [rng.expovariate(1.0) for _ in range(N)]
            observed = latent if quantum == 0 else [round(value / quantum) * quantum for value in latent]
            cases.append({"arm": arm, "quantum": quantum, "seed": seed, "observed": observed})
    Path("input.json").write_text(json.dumps({"schema": "unjuno.6576.timer-quantization-a03.v1", "n": N, "cutoffs": [8, 12, 16, 20, 24], "cases": cases}, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
