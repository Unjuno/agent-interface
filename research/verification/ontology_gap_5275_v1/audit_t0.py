"""Independent literal raw-only auditor; does not import the candidate."""
import base64
import json
import sys

EXPECTED = [
    ("iid-current-save", False, "PLAN_COVERED", "iid_supported"),
    ("iid-reversible-toggle", False, "PLAN_COVERED", "iid_supported"),
    ("iid-permission", False, "PLAN_COVERED", "iid_supported"),
    ("compositional-target-semantic-effect", False, "PLAN_COVERED", "compositional_supported"),
    ("ood-unknown-primitive", True, "UNKNOWN_CHECK_REQUIRED", "explicit_ontology_gap"),
    ("ood-unknown-evidence-role", True, "UNKNOWN_CHECK_REQUIRED", "explicit_ontology_gap"),
    ("ood-malformed-check", True, "UNKNOWN_CHECK_REQUIRED", "malformed_unmappable"),
    ("ood-unmodeled-external-recipient", True, "PLAN_COVERED", "novel_external_side_effect"),
    ("ood-adversarial-familiar-legal-hold", True, "PLAN_COVERED", "adversarial_superficially_familiar"),
]
EXPECTED_REGISTRY_BLOB = "d7e35205daf8b7385a189ef5d1a78bd07ded3cbd"
EXPECTED_CORPUS_BLOB = "81e15afc954eac6687269ff5971d690bb1170208"

def audit(raw):
    errors = []
    if raw.get("schema") != "ontology-gap-5275-raw-v1": errors.append("schema")
    if raw.get("allocation") != "ontology-gap-5275-deterministic-t0-20260930-01": errors.append("allocation")
    source = raw.get("source_identity", {})
    if source.get("registry_git_blob_sha") != EXPECTED_REGISTRY_BLOB: errors.append("registry_source_identity")
    if source.get("corpus_git_blob_sha") != EXPECTED_CORPUS_BLOB: errors.append("corpus_source_identity")
    actual = raw.get("rows", [])
    projected = [(r.get("case_id"), r.get("expected_unknown"), r.get("predicted"), r.get("family")) for r in actual]
    if projected != EXPECTED: errors.append("rows_vs_independent_literal_oracle")
    false_pass = [case_id for case_id, unknown, predicted, _ in EXPECTED if unknown and predicted != "UNKNOWN_CHECK_REQUIRED"]
    false_abstain = [case_id for case_id, unknown, predicted, _ in EXPECTED if not unknown and predicted == "UNKNOWN_CHECK_REQUIRED"]
    counts = raw.get("counts", {})
    expected_counts = {"cases":9,"oracle_unknown":5,"false_pass_ood":2,"false_abstain_iid":0,"mismatches":2}
    if counts != expected_counts: errors.append("counts")
    if raw.get("false_pass_ood") != false_pass: errors.append("false_pass_list")
    if raw.get("false_abstain_iid") != false_abstain: errors.append("false_abstain_list")
    if raw.get("disposition") != "FAIL_DETERMINISTIC_GAP_FALSE_PASS": errors.append("disposition")
    side = raw.get("side_effects", {})
    if side != {"dispatches":0,"model_calls":0,"gpu_calls":0,"network_calls":0,"authority_grants":0}: errors.append("side_effects")
    result = {"schema":"ontology-gap-5275-audit-v1","errors":errors,"integrity_pass":not errors,
              "independent_expected_false_pass_ood":false_pass,
              "interpretation":"scientific FAIL is confirmed when integrity passes and false OOD passes remain"}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1

if __name__ == "__main__":
    raw = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
    raise SystemExit(audit(raw))
