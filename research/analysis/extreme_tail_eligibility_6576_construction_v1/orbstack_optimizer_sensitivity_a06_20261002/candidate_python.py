"""One-shot application of the frozen pre-A06 Python GPD optimizer."""
import hashlib
import json
import sys
from pathlib import Path

from tailid_equivalent import fit_gpd_parameters, quantile_type7

input_dir = Path(sys.argv[1])
output_path = Path(sys.argv[2])
rows = []
for seed in (65769931, 65769932, 65769933, 65769934, 65769935, 65769936):
    raw = (input_dir / f"{seed}.txt").read_bytes()
    sample = [float(value) for value in raw.decode().splitlines()]
    threshold = quantile_type7(sample, 0.90)
    candidates = sorted(range(len(sample)), key=lambda i: sample[i], reverse=True)[:2]
    excluded = set(candidates)
    base = [value for i, value in enumerate(sample) if i not in excluded]
    excesses = [value - threshold for value in base if value > threshold]
    scale, shape = fit_gpd_parameters(excesses)
    rows.append({"seed": seed, "sample_sha256": hashlib.sha256(raw).hexdigest(),
                 "threshold": threshold, "candidate_indices": [i + 1 for i in candidates],
                 "exceedance_count": len(excesses), "scale": scale, "shape": shape})
output_path.write_text(json.dumps({"rows": rows}, sort_keys=True,
                                  separators=(",", ":")) + "\n")
