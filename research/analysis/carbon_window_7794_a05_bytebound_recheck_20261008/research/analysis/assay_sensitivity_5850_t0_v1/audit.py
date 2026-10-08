"""Independent raw-fixture auditor; intentionally does not import candidate."""
import hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).parent
fixture_bytes = (ROOT / "fixture.json").read_bytes()
fixture = json.loads(fixture_bytes)

def oracle(c):
    d = fixture["meaningful_delta"]
    if c["primary_defect"]: return "OUT_OF_SCOPE_UNDETECTED"
    if c["missing"]: return "HOLD_MISSING_OUTCOME"
    if c["target_events"] < 1: return "HOLD_NO_TARGET_EVENTS"
    if c["pipeline_shared"] is not True: return "HOLD_COMMON_PIPELINE_FAILURE"
    if c["control_delta"] < d: return "HOLD_CONTROL_BELOW_DELTA"
    if c["resolution"] > d: return "HOLD_INADEQUATE_RESOLUTION"
    if c["observed_effect"] == 0: return "NULL_INTERPRETABLE_NOT_EQUIVALENCE"
    return "DETECTED_CONTROL_AND_EFFECT"

got = {c["id"]: oracle(c) for c in fixture["cases"]}
expected = fixture["expected"]
candidate_raw = json.loads(pathlib.Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {"results": got, "allocation": fixture["allocation"], "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest()}
raw_matches = candidate_raw.get("results") == got and candidate_raw.get("allocation") == fixture["allocation"] and candidate_raw.get("fixture_sha256") == hashlib.sha256(fixture_bytes).hexdigest()
mutations = []
for mutation in ["drop_missing", "promote_gross", "accept_no_events", "ignore_pipeline",
                 "call_null_equivalence", "hide_primary_defect", "lower_threshold", "drop_subresolution"]:
    bad = dict(got)
    if mutation == "drop_missing": bad.pop("missing_terminal")
    elif mutation == "promote_gross": bad["gross_only"] = "DETECTED_CONTROL_AND_EFFECT"
    elif mutation == "accept_no_events": bad["no_target_events"] = "NULL_INTERPRETABLE_NOT_EQUIVALENCE"
    elif mutation == "ignore_pipeline": bad["broken_common_pipeline"] = "NULL_INTERPRETABLE_NOT_EQUIVALENCE"
    elif mutation == "call_null_equivalence": bad["sensitive_null"] = "EQUIVALENT"
    elif mutation == "hide_primary_defect": bad["primary_only_defect"] = "PASS"
    elif mutation == "lower_threshold": bad["subresolution"] = "NULL_INTERPRETABLE_NOT_EQUIVALENCE"
    elif mutation == "drop_subresolution": bad.pop("subresolution")
    mutations.append({"id": mutation, "rejected": bad != expected})

report = {"status": "PASS_METHOD_SCOPED" if got == expected and raw_matches and all(x["rejected"] for x in mutations) else "FAIL",
          "allocation": fixture["allocation"], "cases": len(got), "mutation_controls": len(mutations),
          "rejected_mutations": sum(x["rejected"] for x in mutations), "candidate_matches_oracle": raw_matches, "results": got,
          "input_sha256": hashlib.sha256(fixture_bytes).hexdigest()}
print(json.dumps(report, sort_keys=True, separators=(",", ":")))
