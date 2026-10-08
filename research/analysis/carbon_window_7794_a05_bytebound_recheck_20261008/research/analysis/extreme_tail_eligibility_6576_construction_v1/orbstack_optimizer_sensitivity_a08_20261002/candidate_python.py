"""One-shot frozen Python-port fit for the A07 optimizer-sensitivity run."""
import hashlib
import json
import sys
from pathlib import Path

from tailid_equivalent import fit_gpd_parameters, quantile_type7

input_dir, output_path, prereg_path = map(Path, sys.argv[1:4])
cfg = json.loads(prereg_path.read_text())
rows = []
for seed in cfg["seeds"]:
    raw = (input_dir / f"{seed}.txt").read_bytes()
    sample = [float(value) for value in raw.decode().splitlines()]
    threshold = quantile_type7(sample, cfg["threshold_probability"])
    candidates = sorted(range(len(sample)), key=lambda i: sample[i], reverse=True)[:cfg["candidate_count"]]
    excluded = set(candidates)
    excesses = [value - threshold for i, value in enumerate(sample)
                if i not in excluded and value > threshold]
    scale, shape = fit_gpd_parameters(excesses)
    rows.append({"seed": seed, "sample_sha256": hashlib.sha256(raw).hexdigest(),
                 "threshold": threshold, "candidate_indices": [i + 1 for i in candidates],
                 "exceedance_count": len(excesses), "scale": scale, "shape": shape})
Path(output_path).write_text(json.dumps({"rows": rows}, sort_keys=True,
                                        separators=(",", ":")) + "\n")
