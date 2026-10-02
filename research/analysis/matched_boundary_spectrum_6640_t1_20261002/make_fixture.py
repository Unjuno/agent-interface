"""Generate the fixed finite synthetic fixture and a separate hidden truth file."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = range(32)
STRATA = (("easy", "direct"), ("easy", "guarded"), ("hard", "direct"), ("hard", "guarded"))
REPS = 64
BASE = {("easy", "direct"): 0.08, ("easy", "guarded"): 0.12,
        ("hard", "direct"): 0.35, ("hard", "guarded"): 0.45}


def active_faults(seed):
    return {0: ["admission"], 1: ["policy"], 2: ["admission", "policy"], 3: ["admission"]}[seed % 4]


def build():
    rows, oracle = [], {"schema": 1, "seeds": {}}
    for seed in SEEDS:
        rng = random.Random(880_000 + seed)
        active = active_faults(seed)
        oracle["seeds"][str(seed)] = {"active_faults": active}
        for difficulty, route in STRATA:
            stratum = f"{difficulty}/{route}"
            for i in range(REPS):
                admission = rng.random() < 0.5
                policy = rng.random() < 0.5
                gateway = rng.random() < (0.1 if difficulty == "easy" else 0.9)
                # Exactly no within-stratum overlap; globally this boundary varies.
                cache = stratum == "hard/guarded"
                instrumented = None if rng.random() < 0.1 else rng.random() < 0.5
                p = BASE[(difficulty, route)]
                if "admission" in active and admission:
                    p += 0.38
                if "policy" in active and policy:
                    p += 0.30
                failed = rng.random() < min(p, 0.98)
                symptom = None
                if failed:
                    symptom = "render" if rng.random() < 0.8 else "gateway"
                rows.append({
                    "attempt_id": f"s{seed:02d}-{difficulty}-{route}-{i:02d}",
                    "seed": seed,
                    "stratum": stratum,
                    "failed": failed,
                    "exposure": {"admission": admission, "policy": policy,
                                 "gateway": gateway, "cache": cache,
                                 "instrumentation": instrumented},
                    "first_symptom": symptom,
                })
    return {"schema": 1, "rows": rows}, oracle


def main():
    fixture, oracle = build()
    (ROOT / "fixture.json").write_text(json.dumps(fixture, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    (ROOT / "oracle.json").write_text(json.dumps(oracle, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
