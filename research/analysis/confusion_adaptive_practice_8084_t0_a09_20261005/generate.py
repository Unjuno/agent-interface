"""Generate fresh held-out synthetic diagnostic counts from hidden scoring rates."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
spec = json.loads((ROOT / "SCORING.json").read_text(encoding="utf-8"))
rows = []
for pi, profile in enumerate(spec["profiles"]):
    for n in spec["sample_sizes"]:
        for replicate in range(spec["replicates"]):
            key = 8709000 + pi * 100000 + n * 1000 + replicate
            counts = []
            for pair, mean in enumerate(profile["rates"]):
                rng = random.Random(key * 10 + pair)
                latent_rate = rng.betavariate(mean * spec["concentration"],
                                              (1 - mean) * spec["concentration"])
                counts.append(rng.binomialvariate(n, latent_rate))
            rows.append({"row_id": f"r{len(rows):06d}", "profile_id": profile["id"],
                         "n": n, "successes": counts})
out = {"schema": "issue8084-a09-observations-v1",
       "span_grid": spec["span_grid"], "peak_grid": spec["peak_grid"], "rows": rows}
(ROOT / "candidate" / "observed_counts.json").write_text(
    json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"rows": len(rows), "profiles": len(spec["profiles"]),
                  "sample_sizes": spec["sample_sizes"], "replicates": spec["replicates"]}, sort_keys=True))
