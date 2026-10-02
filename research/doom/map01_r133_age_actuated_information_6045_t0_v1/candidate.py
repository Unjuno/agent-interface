#!/usr/bin/env python3
"""One-shot synthetic T0 candidate. Writes deterministic raw rows."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
fixture_bytes = (ROOT / "FIXTURE.json").read_bytes()
fixture = json.loads(fixture_bytes)
rows = []
for c in fixture["cases"]:
    valid_lineage = (c.get("lineage") != "ambiguous" and c["clock"] == "A"
                     and len(c["consumed"]) == 1 and c["effect_obs"] == c["consumed"])
    age = (c["effect_ms"] - c["capture_ms"][0]
           if c["independent_effect"] and c["effect_relevant"] is True and valid_lineage
           else "UNKNOWN")
    if not c["intervention_needed"]:
        status = "NOT_APPLICABLE"
    elif c["effect_ms"] is None and c["cue"][1] is not None and c["dispatch_ms"] is None:
        status = "MISS"
    elif c["effect_ms"] is None or not c["independent_effect"] or c["effect_relevant"] is not True:
        status = "UNKNOWN"
    elif not valid_lineage:
        status = "UNKNOWN"
    else:
        status = "RELEVANT_EFFECT"
    cycle = c["effect_ms"] - c["dispatch_ms"] if c["effect_ms"] is not None and c["dispatch_ms"] is not None else "UNKNOWN"
    obs_age = c["delivery_ms"] - min(c["capture_ms"]) if c["capture_ms"] and c["delivery_ms"] is not None else "UNKNOWN"
    rows.append({"id":c["id"],"delivery_aoi_ms":obs_age,"cycle_latency_ms":cycle,
                 "effect_age_ms":age,"opportunity_status":status,
                 "credited_relevant_effect": status == "RELEVANT_EFFECT",
                 "credited_pulses": 0,"intervention_needed":c["intervention_needed"]})
out = {"schema":"opportunity-conditioned-age-raw-v1","fixture_sha256":hashlib.sha256(fixture_bytes).hexdigest(),"rows":rows}
path = ROOT / "results/t0/RAW.json"
if path.exists(): raise SystemExit("STOP_OUTPUT_EXISTS_NO_RETRY")
path.parent.mkdir(parents=True, exist_ok=False)
path.write_text(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n")
print(json.dumps({"status":"CANDIDATE_RAW_WRITTEN","rows":len(rows),"raw_sha256":hashlib.sha256(path.read_bytes()).hexdigest()},sort_keys=True))
