"""Generate fresh held-out synthetic diagnostic counts from hidden scoring rates."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
spec = json.loads((ROOT / "SCORING.json").read_text(encoding="utf-8"))
rows = []
for pi, profile in enumerate(spec["profiles"]):
    for n in spec["sample_sizes"]:
        for ai, arm in enumerate(spec["arms"]):
            for replicate in range(spec["replicates"]):
                key = 88100000 + pi * 20000000 + n * 100000 + ai * 10000 + replicate
                counts = []
                for pair, mean in enumerate(profile["rates"]):
                    rng = random.Random(key * 10 + pair)
                    if arm["concentration"] is None:
                        probability = mean
                    else:
                        k = arm["concentration"]
                        probability = rng.betavariate(mean * k, (1 - mean) * k)
                    counts.append(rng.binomialvariate(n, probability))
                rows.append({"row_id": f"r{len(rows):06d}", "profile_id": profile["id"],
                             "n": n, "arm_id": arm["id"], "successes": counts})
out = {"schema": "issue8084-a10-observations-v1",
       "span_grid": spec["span_grid"], "peak_grid": spec["peak_grid"], "rows": rows}
(ROOT / "candidate" / "observed_counts.json").write_text(
    json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"rows": len(rows), "profiles": len(spec["profiles"]),
                  "sample_sizes": spec["sample_sizes"], "arms": len(spec["arms"]),
                  "replicates": spec["replicates"]}, sort_keys=True))
