import hashlib
import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent
cases_bytes = (base / "cases.json").read_bytes()
cases = json.loads(cases_bytes)["cases"]
raw_path = pathlib.Path(sys.argv[1])
raw_bytes = raw_path.read_bytes()
raw = json.loads(raw_bytes)
policies = ("POSTHOC_ASSOCIATION", "TEMPORAL_LINEAGE", "CONTROL_BASELINE", "CAUSAL_MODEL", "UNKNOWN_ON_CONFOUNDING")
errors = []
expected = {}
for c in cases:
    for p in policies:
        # Independent oracle, intentionally does not import policy.py or runner code.
        if not c["observed_effect"]:
            s = "NO_EFFECT"
        elif p == "POSTHOC_ASSOCIATION":
            s = "CAUSAL_EFFECT_IDENTIFIED" if c["attempted"] else "NO_EFFECT"
        elif p == "TEMPORAL_LINEAGE":
            s = "CAUSAL_EFFECT_IDENTIFIED" if c["attempted"] and c["receipt_before_observation"] and not c["competing_cause_known"] and not c["interference"] else "ATTRIBUTION_UNKNOWN"
        elif p == "CONTROL_BASELINE":
            s = "EFFECT_LINKED_UNDER_CONTROL_ASSUMPTIONS" if c["control_known"] and c["attempted"] and c["action_succeeded"] and not c["control_effect"] and not c["interference"] else "ATTRIBUTION_UNKNOWN"
        elif p == "CAUSAL_MODEL":
            s = ("CAUSAL_EFFECT_IDENTIFIED" if c["ground_truth"] == "action" else "ATTRIBUTION_UNKNOWN") if c["graph_complete"] else "ATTRIBUTION_UNKNOWN"
        else:
            s = "ATTRIBUTION_UNKNOWN" if (c["competing_cause_known"] or c["interference"] or not c["graph_complete"] or not c["control_known"]) else ("CAUSAL_EFFECT_IDENTIFIED" if c["attempted"] and c["action_succeeded"] and not c["control_effect"] else "ATTRIBUTION_UNKNOWN")
        expected[(c["id"],p)] = s
if raw.get("schema") != "causal_attribution_raw_v1": errors.append("schema")
if raw.get("cases_sha256") != hashlib.sha256(cases_bytes).hexdigest(): errors.append("case_hash")
if raw.get("case_count") != 8 or raw.get("policies") != list(policies): errors.append("matrix_header")
rows = raw.get("rows", [])
if len(rows) != 40: errors.append("row_count")
seen = set()
false_claims = {p:0 for p in policies}
missed = {p:0 for p in policies}
unknown = {p:0 for p in policies}
truth = {c["id"]:c["ground_truth"] for c in cases}
for row in rows:
    key=(row.get("case_id"),row.get("policy"))
    if key in seen: errors.append("duplicate_row")
    seen.add(key)
    if key not in expected or row.get("status") != expected[key]: errors.append("oracle_mismatch")
    p=row.get("policy"); y=truth.get(row.get("case_id"))
    claim=row.get("status")=="CAUSAL_EFFECT_IDENTIFIED"
    if row.get("causal_claim") != claim or row.get("false_attribution") != (claim and y!="action") or row.get("missed_attribution") != (y=="action" and not claim) or row.get("unknown") != (row.get("status")=="ATTRIBUTION_UNKNOWN"):
        errors.append("metric_mismatch")
    if p in policies:
        false_claims[p]+=int(claim and y!="action")
        missed[p]+=int(y=="action" and not claim)
        unknown[p]+=int(row.get("status")=="ATTRIBUTION_UNKNOWN")
if seen != set(expected): errors.append("coverage")
if false_claims["POSTHOC_ASSOCIATION"] == 0: errors.append("negative_control_not_discriminating")
if false_claims["UNKNOWN_ON_CONFOUNDING"] != 0: errors.append("conservative_false_claim")
if missed["UNKNOWN_ON_CONFOUNDING"] != 0: errors.append("clean_effect_hidden")
result={"status":"PASS_AUDIT" if not errors else "FAIL_AUDIT", "rows":len(rows), "errors":errors,
        "false_attributions":false_claims, "missed_attributions":missed, "unknown":unknown,
        "raw_sha256":hashlib.sha256(raw_bytes).hexdigest()}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not errors else 1)
