"""One-shot finite deterministic ontology-gap discriminator; emits one JSON line."""
import hashlib
import json
import platform
import sys
from registry import classify

CORPUS_TEXT = "[\n  {\n    \"case_id\": \"iid-current-save\",\n    \"family\": \"iid_supported\",\n    \"oracle_unknown\": false,\n    \"task_summary\": \"Save the currently selected draft and verify the resulting saved state.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"TARGET.IDENTITY_CURRENT\",\"subject_ref\":\"target:save\",\"evidence_role\":\"OBSERVATION_CURRENT\",\"verifier_class\":\"deterministic_rule\",\"version\":\"1.0\"},{\"primitive\":\"EFFECT.POSTCONDITION\",\"subject_ref\":\"draft:7\",\"evidence_role\":\"INDEPENDENT_EFFECT\",\"verifier_class\":\"local_cpu\",\"version\":\"1.0\"}]}\n  },\n  {\n    \"case_id\": \"iid-reversible-toggle\",\n    \"family\": \"iid_supported\",\n    \"oracle_unknown\": false,\n    \"task_summary\": \"Toggle the selected preference and verify it can be reversed.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"TARGET.IDENTITY_CURRENT\",\"subject_ref\":\"target:preference\",\"evidence_role\":\"OBSERVATION_CURRENT\",\"verifier_class\":\"deterministic_rule\",\"version\":\"1.0\"},{\"primitive\":\"EFFECT.REVERSIBILITY\",\"subject_ref\":\"preference:compact\",\"evidence_role\":\"INDEPENDENT_EFFECT\",\"verifier_class\":\"local_cpu\",\"version\":\"1.0\"}]}\n  },\n  {\n    \"case_id\": \"iid-permission\",\n    \"family\": \"iid_supported\",\n    \"oracle_unknown\": false,\n    \"task_summary\": \"Confirm the current permission before changing a local setting.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"AUTHORITY.SCOPE_CURRENT\",\"subject_ref\":\"setting:notifications\",\"evidence_role\":\"POLICY_RECORD\",\"verifier_class\":\"deterministic_rule\",\"version\":\"1.0\"},{\"primitive\":\"EFFECT.POSTCONDITION\",\"subject_ref\":\"setting:notifications\",\"evidence_role\":\"INDEPENDENT_EFFECT\",\"verifier_class\":\"local_cpu\",\"version\":\"1.0\"}]}\n  },\n  {\n    \"case_id\": \"compositional-target-semantic-effect\",\n    \"family\": \"compositional_supported\",\n    \"oracle_unknown\": false,\n    \"task_summary\": \"Find the intended row, confirm the requested edit matches intent, and verify the resulting state.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"TARGET.IDENTITY_CURRENT\",\"subject_ref\":\"row:invoice-7\",\"evidence_role\":\"OBSERVATION_CURRENT\",\"verifier_class\":\"local_multimodal_placeholder\",\"version\":\"0.1\"},{\"primitive\":\"SEMANTIC.INTENT_MATCH\",\"subject_ref\":\"edit:due-date\",\"evidence_role\":\"OBSERVATION_CURRENT\",\"verifier_class\":\"rich_model\",\"version\":\"1.0\"},{\"primitive\":\"EFFECT.POSTCONDITION\",\"subject_ref\":\"invoice:7\",\"evidence_role\":\"INDEPENDENT_EFFECT\",\"verifier_class\":\"local_cpu\",\"version\":\"1.0\"}]}\n  },\n  {\n    \"case_id\": \"ood-unknown-primitive\",\n    \"family\": \"explicit_ontology_gap\",\n    \"oracle_unknown\": true,\n    \"task_summary\": \"Check an unfamiliar retention obligation before archiving.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"LEGAL.RETENTION_CURRENT\",\"subject_ref\":\"record:12\",\"evidence_role\":\"POLICY_RECORD\",\"verifier_class\":\"external_tool\",\"version\":\"1.0\"}]}\n  },\n  {\n    \"case_id\": \"ood-unknown-evidence-role\",\n    \"family\": \"explicit_ontology_gap\",\n    \"oracle_unknown\": true,\n    \"task_summary\": \"A model assertion is the only evidence for the current target identity.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"TARGET.IDENTITY_CURRENT\",\"subject_ref\":\"target:primary\",\"evidence_role\":\"MODEL_ASSERTION_ONLY\",\"verifier_class\":\"rich_model\",\"version\":\"1.0\"}]}\n  },\n  {\n    \"case_id\": \"ood-malformed-check\",\n    \"family\": \"malformed_unmappable\",\n    \"oracle_unknown\": true,\n    \"task_summary\": \"A target check has no subject reference or evidence role.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"TARGET.IDENTITY_CURRENT\",\"verifier_class\":\"deterministic_rule\",\"version\":\"1.0\"}]}\n  },\n  {\n    \"case_id\": \"ood-unmodeled-external-recipient\",\n    \"family\": \"novel_external_side_effect\",\n    \"oracle_unknown\": true,\n    \"task_summary\": \"Send a customer export to an external recipient; verify recipient authorization and irreversible disclosure risk.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"TARGET.IDENTITY_CURRENT\",\"subject_ref\":\"target:export\",\"evidence_role\":\"OBSERVATION_CURRENT\",\"verifier_class\":\"deterministic_rule\",\"version\":\"1.0\"},{\"primitive\":\"EFFECT.POSTCONDITION\",\"subject_ref\":\"export:batch-4\",\"evidence_role\":\"INDEPENDENT_EFFECT\",\"verifier_class\":\"local_cpu\",\"version\":\"1.0\"}]}\n  },\n  {\n    \"case_id\": \"ood-adversarial-familiar-legal-hold\",\n    \"family\": \"adversarial_superficially_familiar\",\n    \"oracle_unknown\": true,\n    \"task_summary\": \"Archive the selected customer record, which is under a legal hold; a hold-status check is mandatory before the irreversible action.\",\n    \"plan\": {\"plan_version\":\"v0.1\",\"checks\":[{\"primitive\":\"TARGET.IDENTITY_CURRENT\",\"subject_ref\":\"record:customer-19\",\"evidence_role\":\"OBSERVATION_CURRENT\",\"verifier_class\":\"deterministic_rule\",\"version\":\"1.0\"},{\"primitive\":\"EFFECT.REVERSIBILITY\",\"subject_ref\":\"record:customer-19\",\"evidence_role\":\"INDEPENDENT_EFFECT\",\"verifier_class\":\"local_cpu\",\"version\":\"1.0\"}]}\n  }\n]\n"
CORPUS_GIT_BLOB_SHA = "81e15afc954eac6687269ff5971d690bb1170208"
REGISTRY_GIT_BLOB_SHA = "d7e35205daf8b7385a189ef5d1a78bd07ded3cbd"

def main():
    corpus = json.loads(CORPUS_TEXT)
    rows = []
    for item in corpus:
        # The oracle annotation is deliberately not passed into the candidate.
        predicted = classify(item["plan"])
        rows.append({
            "case_id": item["case_id"],
            "family": item["family"],
            "expected_unknown": item["oracle_unknown"],
            "predicted": predicted,
            "mismatch": (predicted == "UNKNOWN_CHECK_REQUIRED") != item["oracle_unknown"],
        })
    unknowns = [r["case_id"] for r in rows if r["expected_unknown"]]
    false_pass = [r["case_id"] for r in rows if r["expected_unknown"] and r["predicted"] != "UNKNOWN_CHECK_REQUIRED"]
    false_abstain = [r["case_id"] for r in rows if not r["expected_unknown"] and r["predicted"] == "UNKNOWN_CHECK_REQUIRED"]
    mismatch_count = sum(r["mismatch"] for r in rows)
    raw = {
        "schema": "ontology-gap-5275-raw-v1",
        "allocation": "ontology-gap-5275-deterministic-t0-20260930-01",
        "runtime": {"python": platform.python_version(), "platform": sys.platform, "container": False},
        "source_identity": {
            "registry_git_blob_sha": REGISTRY_GIT_BLOB_SHA,
            "corpus_git_blob_sha": CORPUS_GIT_BLOB_SHA,
        },
        "counts": {
            "cases": len(rows),
            "oracle_unknown": len(unknowns),
            "false_pass_ood": len(false_pass),
            "false_abstain_iid": len(false_abstain),
            "mismatches": mismatch_count,
        },
        "false_pass_ood": false_pass,
        "false_abstain_iid": false_abstain,
        "rows": rows,
        "side_effects": {"dispatches": 0, "model_calls": 0, "gpu_calls": 0, "network_calls": 0, "authority_grants": 0},
        "disposition": "PASS_DETERMINISTIC_GAP_T0_SCOPED" if mismatch_count == 0 else "FAIL_DETERMINISTIC_GAP_FALSE_PASS",
    }
    print(json.dumps(raw, sort_keys=True, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
