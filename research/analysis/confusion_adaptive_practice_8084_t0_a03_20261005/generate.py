"""Deterministic synthetic diagnostics; latent rates are input only to fixture generation."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
spec = json.loads((ROOT / "SCORING.json").read_text(encoding="utf-8"))
rows = []
for si, stratum in enumerate(spec["strata"]):
    for n in spec["sample_sizes"]:
        for rep in range(spec["replicates"]):
            key = 808403 + si * 100000 + n * 1000 + rep
            counts = []
            for pair, p in enumerate(stratum["rates"]):
                rng = random.Random(key * 10 + pair)
                counts.append(sum(rng.random() < p for _ in range(n)))
            rows.append({"row_id": f"r{len(rows):04d}", "n": n, "successes": counts})
out = {"schema": "issue8084-a03-observations-v1", "pair_order": ["AB", "AC", "BC"],
       "minimum_span": spec["minimum_span"], "minimum_peak": spec["minimum_peak"], "rows": rows}
(ROOT / "candidate" / "observed_counts.json").write_text(
    json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"rows": len(rows), "strata": len(spec["strata"]), "sample_sizes": spec["sample_sizes"]}, sort_keys=True))
