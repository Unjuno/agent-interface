#!/usr/bin/env python3
"""Frozen #6155 T0f candidate; standard library only."""
import json
import math
import random
import sys
from pathlib import Path


def main(fixture_path: str, output_path: str) -> int:
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=False)
    looks = set(fixture["looks"])
    zcrit = fixture["naive_two_sided_z"]
    alpha = fixture["family_alpha"]
    lo, hi = fixture["corrected_bound"]
    width = hi - lo
    counts = {name: {"streams": 0, "naive_stop": 0, "cs_stop": 0,
                     "leak_stop": 0, "naive_stop_times": [], "cs_stop_times": []}
              for name in fixture["deltas"]}
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        for case_index, (case, delta) in enumerate(fixture["deltas"].items()):
            summary = counts[case]
            for stream_id in range(fixture["streams_per_case"]):
                rng = random.Random(fixture["seed"] + case_index * 1_000_003 + stream_id)
                n = 0
                total = 0.0
                total_sq = 0.0
                naive_time = None
                cs_time = None
                leak_total = 0.0
                for t in range(1, fixture["max_time"] + 1):
                    x = fixture["x_magnitude"] if rng.getrandbits(1) else -fixture["x_magnitude"]
                    eps = fixture["epsilon_magnitude"] if rng.getrandbits(1) else -fixture["epsilon_magnitude"]
                    y = delta + x + eps
                    z = y - fixture["fixed_beta"] * x
                    # Deliberately invalid: coefficient depends on this same high-fidelity row.
                    beta_leak = y / x
                    z_leak = y - beta_leak * x
                    n += 1
                    total += z
                    total_sq += z * z
                    leak_total += z_leak
                    if t not in looks:
                        continue
                    mean = total / n
                    variance = max(0.0, (total_sq - total * total / n) / (n - 1))
                    lower_naive = mean - zcrit * math.sqrt(variance / n)
                    alpha_t = alpha / (t * (t + 1))
                    radius_cs = math.sqrt((width * width / (2 * n)) * math.log(2 / alpha_t))
                    lower_cs = mean - radius_cs
                    if naive_time is None and lower_naive > 0:
                        naive_time = t
                    if cs_time is None and lower_cs > 0:
                        cs_time = t
                leak_mean = leak_total / fixture["max_time"]
                row = {
                    "case": case,
                    "stream": stream_id,
                    "delta": delta,
                    "naive_stop_time": naive_time,
                    "cs_stop_time": cs_time,
                    "fixed_beta_final_mean": total / fixture["max_time"],
                    "leaky_final_mean": leak_mean,
                    "leaky_stop_time": None
                }
                stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                summary["streams"] += 1
                summary["naive_stop"] += naive_time is not None
                summary["cs_stop"] += cs_time is not None
                summary["leak_stop"] += False
                if naive_time is not None:
                    summary["naive_stop_times"].append(naive_time)
                if cs_time is not None:
                    summary["cs_stop_times"].append(cs_time)
    # Summary is derived from the just-written raw and is still audited independently.
    result = {}
    for case, values in counts.items():
        n = values["streams"]
        result[case] = {
            "streams": n,
            "naive_false_or_true_stops": values["naive_stop"],
            "naive_stop_rate": values["naive_stop"] / n,
            "cs_stops": values["cs_stop"],
            "cs_stop_rate": values["cs_stop"] / n,
            "leak_stops": values["leak_stop"],
            "naive_median_stop": sorted(values["naive_stop_times"])[len(values["naive_stop_times"]) // 2] if values["naive_stop_times"] else None,
            "cs_median_stop": sorted(values["cs_stop_times"])[len(values["cs_stop_times"]) // 2] if values["cs_stop_times"] else None
        }
    Path(str(out) + ".summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": fixture["allocation"], "rows": sum(v["streams"] for v in counts.values()), "summary": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE.json RAW.jsonl")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))

