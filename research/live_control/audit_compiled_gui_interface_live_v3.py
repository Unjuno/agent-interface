"""Independent audit of v3's preserved read-check status mismatch."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/compiled-gui-interface-live-03"


def read(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items(): assert sha(HERE / name) == digest, name
    report = read(ROOT / "report.json")
    assert report["passed"] is False
    assert report["actual_performed_model_usage_totals"] == {
        "input_tokens": 18792, "cached_input_tokens": 0,
        "cache_write_input_tokens": 0, "output_tokens": 343,
        "reasoning_output_tokens": 113}
    for case in report["cases"]:
        assert case["adaptive"]["accounting"]["attempted_calls"] == 1
        assert len(case["mint"]["programs"]) == len(case["mint"]["minted"]) == 2
        assert all(row["terminal"]["status"] == "completed" and
                   row["terminal"]["release"]["verified"] is True
                   for row in case["mint"]["programs"])
        check = case["raw_evidence"][0]["target_check"]
        assert check["eligible"] is True and check["status"] == "VALID"
        assert case["raw_evidence"][0]["normalized"]["predicates"][
            "field_target_present"] is False
        assert case["compiled_runtime"]["outcome"] == "SAFE_YIELD"
        assert case["compiled_runtime"]["reason"] == "unknown_state"
        assert case["compiled_runtime"]["completed_transitions"] == 0
        assert case["action_records"] == [] and case["intervention"] is None
        assert case["independent_evaluation"]["success"] is False
        assert case["actual"] == {} and case["bridge_exit_code"] == 0
        assert case["raw_evidence_retention_verified"] is True
    audit = {"passed": True, "formal_study_passed": False, "cases": 2,
        "grounded_handles": "4/4", "eligible_read_checks": "2/2",
        "compiled_target_actions": 0, "independent_task_success": "0/2",
        "fresh_model_calls": 2,
        "fresh_model_usage_totals": report["actual_performed_model_usage_totals"],
        "failure": "runner expected REVALIDATED from read-only check whose contract returns eligible VALID",
        "decision": "HOLD_V3_AND_FIX_READ_CHECK_STATUS_ONLY",
        "scope": "independent audit of frozen v3; no GUI/model rerun"}
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
