"""One-shot deterministic public corpus and auditor-only oracle generator."""
import hashlib
import json
import math
import random
from pathlib import Path

SEED = 8157
PROFILES = (
    "approach", "passby", "stationary", "iid", "correlated",
    "irregular_dropout", "acceleration", "occlusion", "identity_swap",
    "understated_bound",
)
BOUND = 0.5
DT = 1.0 / 30.0


def _id(profile: str, ordinal: int) -> str:
    return hashlib.sha256(f"8157:{profile}:{ordinal}".encode()).hexdigest()[:16]


def build():
    rng = random.Random(SEED)
    public, oracle = [], []
    for profile in PROFILES:
        for ordinal in range(20):
            hazard = ordinal % 2 == 0
            # Even/odd ordinals are hidden calibration/evaluation split.
            split = "calibration" if ordinal % 4 < 2 else "evaluation"
            seq_id = _id(profile, ordinal)
            start_r = 48.0 + rng.randrange(0, 50)
            target_ttc = rng.uniform(0.65, 2.4)
            growth = start_r * DT / target_ttc if hazard else 0.0
            times, observations, truth = [], [], []
            last_error = 0.0
            base_t = 0.0
            for i in range(12):
                if profile == "irregular_dropout":
                    base_t += DT * rng.choice((0.60, 0.85, 1.15, 1.50))
                    observed = i not in (3, 8)
                else:
                    base_t = i * DT
                    observed = True
                times.append(round(base_t, 9))
                if profile == "passby":
                    # Radial expansion peaks and then reverses: no valid TTC cue.
                    passby_rate = growth if hazard else 0.75
                    radial = passby_rate * i if i <= 6 else passby_rate * (12 - i)
                elif profile == "stationary" or not hazard:
                    radial = 0.0
                elif profile == "acceleration":
                    sign = 0.75 if ordinal % 4 == 0 else -0.18
                    radial = growth * i + (sign * max(0, i - 5) ** 2 if i >= 5 else 0.0)
                elif profile == "irregular_dropout":
                    radial = growth * (base_t / DT)
                else:
                    radial = growth * i
                actual = start_r + radial
                if profile == "iid":
                    error = rng.uniform(-BOUND, BOUND)
                elif profile == "correlated":
                    last_error = max(-BOUND, min(BOUND, last_error * 0.72 + rng.uniform(-0.14, 0.14)))
                    error = last_error
                elif profile == "understated_bound":
                    error = rng.choice((-1.2, 1.2))
                else:
                    error = rng.uniform(-BOUND, BOUND)
                radius = round(actual + error, 8) if observed else None
                track = "track-A"
                if profile == "identity_swap" and i >= 6:
                    track = "track-B"
                if profile == "occlusion" and i in (5, 6):
                    observed, radius = False, None
                observations.append({"t_s": times[-1], "radius_px": radius,
                                     "bound_px": BOUND, "track_id": track})
                slope = growth / DT
                truth.append({"t_s": times[-1], "radius_px": round(actual, 8),
                              "observed": observed,
                              "true_ttc_s": (actual / slope if slope > 0 and profile in
                                             {"approach", "iid", "correlated", "irregular_dropout", "understated_bound"}
                                             else None)})
            valid = [x for x in truth if x["observed"]]
            true_ttc = valid[-1]["true_ttc_s"] if valid else None
            public.append({"id": seq_id, "history": observations})
            oracle.append({"id": seq_id, "profile": profile, "ordinal": ordinal,
                           "split": split, "hazard": hazard,
                           "eligible_in_model": profile in {"approach", "iid", "correlated", "irregular_dropout"} and hazard,
                           "true_ttc_s": true_ttc, "truth": truth,
                           "actual_error_bound_px": 1.2 if profile == "understated_bound" else BOUND})
    return public, oracle


def write(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))


if __name__ == "__main__":
    out = Path(__import__("sys").argv[1])
    pub, truth = build()
    write(out / "public.jsonl", pub)
    write(out / "oracle.jsonl", truth)
