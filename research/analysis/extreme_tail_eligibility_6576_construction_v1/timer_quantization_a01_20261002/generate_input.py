"""Pre-candidate deterministic input generator for the frozen A01 fixture."""
import json
import random
from pathlib import Path

SEED = 65761111
N_TRAIN = 4000
N_HOLDOUT = 10000
ARMS = (("continuous", 0.0), ("quantum_025", 0.25), ("quantum_100", 1.0))


def rounded(value, quantum):
    return value if quantum == 0 else round(value / quantum) * quantum


def main():
    arms = []
    for arm_index, (name, quantum) in enumerate(ARMS):
        rng = random.Random(SEED + arm_index * 1009)
        latent_train = [rng.expovariate(1.0) for _ in range(N_TRAIN)]
        latent_holdout = [rng.expovariate(1.0) for _ in range(N_HOLDOUT)]
        arms.append({
            "arm": name,
            "quantum": quantum,
            "train_latent": latent_train,
            "train_observed": [rounded(x, quantum) for x in latent_train],
            "holdout_latent": latent_holdout,
            "holdout_observed": [rounded(x, quantum) for x in latent_holdout],
        })
    Path("input.json").write_text(json.dumps({"seed": SEED, "arms": arms}, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
