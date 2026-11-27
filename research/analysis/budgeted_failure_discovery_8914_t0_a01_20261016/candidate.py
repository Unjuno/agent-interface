#!/usr/bin/env python3
"""Allocation-only candidate. Accepts shallow data; never reads deep outcomes."""
import json, sys
from collections import defaultdict

src, dst = sys.argv[1:3]
with open(src, encoding="utf-8") as f:
    data = json.load(f)
if set(data) != {"worlds"}:
    raise SystemExit("candidate input schema violation")
result = {}
for world, payload in data["worlds"].items():
    if set(payload) != {"training", "eligible", "sentinel_ids", "budget"}:
        raise SystemExit("world schema violation")
    training, eligible = payload["training"], payload["eligible"]
    if not eligible or any(cell["shallow_failures"] != 0 or cell["shallow_trials"] != 2 for cell in eligible):
        raise SystemExit("eligible-cell contract violation")
    rates = defaultdict(lambda: [0, 0])
    for cell in training:
        for feature in ("risk", "texture"):
            row = rates[(feature, cell[feature])]
            row[0] += cell["shallow_failures"]
            row[1] += cell["shallow_trials"]
    scores = {}
    for c in eligible:
        # Metadata baseline uses only the prespecified risk bit.
        metadata = float(c["risk"])
        # Feature score is the mean smoothed training failure rate for risk and texture.
        learned = sum((rates[(feature, c[feature])][0] + 1) /
                      (rates[(feature, c[feature])][1] + 2)
                      for feature in ("risk", "texture")) / 2
        scores[c["cell_id"]] = {"metadata": metadata, "feature": learned}
    result[world] = {"scores": scores, "sentinel_ids": payload["sentinel_ids"],
                     "eligible_ids": sorted(c["cell_id"] for c in eligible),
                     "budget": payload["budget"]}
with open(dst, "w", encoding="utf-8") as f:
    json.dump(result, f, sort_keys=True, separators=(",", ":"))
    f.write("\n")
