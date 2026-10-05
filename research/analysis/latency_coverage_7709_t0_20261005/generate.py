#!/usr/bin/env python3
"""Generate the frozen, held-out synthetic series exactly once."""
import json
import random
import sys


def generate(config, destination):
    total = 0
    with open(destination, "w", encoding="utf-8", newline="\n") as out:
        for ci, case in enumerate(config["scenarios"]):
            for n in config["session_counts"]:
                for rep in range(config["replicates"]):
                    rng = random.Random(config["base_seed"] + ci * 1_000_000 + n * 10_000 + rep)
                    sessions = []
                    censored_count = 0
                    for si in range(n):
                        common_level = rng.gauss(0.0, 120.0)
                        route_slope = rng.gauss(0.0, 60.0)
                        common_ar = 0.0
                        difference_ar = 0.0
                        windows = []
                        for t in range(config["windows_per_session"]):
                            common_ar = case["rho_common"] * common_ar + rng.gauss(0.0, 78.0)
                            difference_ar = case["rho_difference"] * difference_ar + rng.gauss(0.0, 22.0)
                            level = 600.0 + common_level + common_ar
                            if t < case["warmup_windows"]:
                                level += case["warmup_ms"]
                            if t >= case["step_at"]:
                                level += case["step_ms"]
                            if config["windows_per_session"] > 1:
                                level += case["drift_ms"] * t / (config["windows_per_session"] - 1)
                            difference = case["beta_ms"] + route_slope + difference_ar + rng.gauss(0.0, 18.0)
                            a = max(1.0, level - difference / 2.0)
                            b = max(1.0, level + difference / 2.0)
                            censored = rng.random() < config["censor_probability"]
                            if censored:
                                a = b = float(config["censor_cap_ms"])
                                censored_count += 1
                            windows.append([round(a, 6), round(b, 6), int(censored)])
                        sessions.append(windows)
                    row = {
                        "case": case["name"], "n": n, "rep": rep,
                        "truth_ms": round(case["beta_ms"] * (1.0 - config["censor_probability"]), 9),
                        "sessions": sessions,
                    }
                    out.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
                    total += n * config["windows_per_session"]
    return total


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        cfg = json.load(f)
    print(json.dumps({"paired_windows": generate(cfg, sys.argv[2])}, sort_keys=True))
