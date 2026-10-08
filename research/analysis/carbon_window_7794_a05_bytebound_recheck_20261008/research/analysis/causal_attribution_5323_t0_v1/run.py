import hashlib
import json
import pathlib
import sys
from policy import POLICIES, classify

root = pathlib.Path(__file__).resolve().parent
cases_bytes = (root / "cases.json").read_bytes()
cases_doc = json.loads(cases_bytes)
rows = []
for case in cases_doc["cases"]:
    for policy in POLICIES:
        status = classify(case, policy)
        rows.append({"case_id": case["id"], "policy": policy, "status": status,
                     "causal_claim": status == "CAUSAL_EFFECT_IDENTIFIED",
                     "ground_truth": case["ground_truth"],
                     "false_attribution": status == "CAUSAL_EFFECT_IDENTIFIED" and case["ground_truth"] != "action",
                     "missed_attribution": case["ground_truth"] == "action" and status != "CAUSAL_EFFECT_IDENTIFIED",
                     "unknown": status == "ATTRIBUTION_UNKNOWN"})
raw = {"schema":"causal_attribution_raw_v1", "cases_sha256":hashlib.sha256(cases_bytes).hexdigest(),
       "case_count":len(cases_doc["cases"]), "policies":list(POLICIES), "rows":rows}
out = pathlib.Path(sys.argv[1])
if out.exists():
    raise SystemExit(f"refusing overwrite: {out}")
out.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"rows":len(rows), "cases":len(cases_doc["cases"]), "output":str(out)}))
