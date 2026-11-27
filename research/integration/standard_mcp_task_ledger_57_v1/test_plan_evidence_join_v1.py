import unittest
from ledger import LedgerValidationError
from plan_evidence_join_v1 import canonical_plan_sha256, validate_plan_evidence_join


def plan(label):
    return {"schema": "agent-interface/calc-symbolic-plan-v1",
            "interface_id": label,
            "predicates": ["context_ok", "blank", "cells_match"],
            "symbols": {"entry": {"role": "entry"}, "save": {"role": "save"}},
            "actions": {"enter": {"operation": "enter_pair"},
                        "persist": {"operation": "request_save"}},
            "method": {"name": "bounded", "version": "1"}}


def row(task, mode, source, digest, *, attempt=None, provider_plan=None,
        source_plan=None):
    call = f"call-{task}"
    prepare_attempt = attempt or f"attempt-{task}"
    if mode in {"cold", "repair"}:
        raw = {"attempt_id": attempt, "provider_status": "completed",
               "plan": provider_plan}
    else:
        raw = {"provider_generation_count": 0}
    return {"task_id": task, "mode": mode, "source_task_id": source,
            "plan_sha256": digest, "raw_generation": raw,
            "prepare_receipt": {"call_id": call, "attempt_id": prepare_attempt,
                "status": "prepared", "submitted_plan": provider_plan or source_plan,
                "task_plan_sha256": digest, "artifact_id": f"artifact-{task}",
                "owner_id": f"owner-{task}"},
            "execution": {"call_id": call, "task_plan_sha256": digest,
                "outcome": "SAFE_YIELD", "release_confirmed": True,
                "task_success": True, "verifier_id": f"verifier-{task}",
                "independent_score": True}}


def fixture():
    cold, repair = plan("cold-plan"), plan("repaired-plan")
    cold_hash, repair_hash = canonical_plan_sha256(cold), canonical_plan_sha256(repair)
    return {"schema": "agent-interface/calc-plan-evidence-join-v1", "rows": [
        row("task-1", "cold", None, cold_hash, attempt="attempt-1", provider_plan=cold),
        row("task-2", "warm", "task-1", cold_hash, source_plan=cold),
        row("task-3", "repair", None, repair_hash, attempt="attempt-3", provider_plan=repair),
        row("task-4", "post_repair_warm", "task-3", repair_hash,
            source_plan=repair),
    ]}


class PlanEvidenceJoinTests(unittest.TestCase):
    def test_joins_cold_warm_repair_and_post_repair_warm_custody(self):
        result = validate_plan_evidence_join(fixture())
        self.assertEqual(result["task_count"], 4)
        self.assertEqual(result["generated_plan_count"], 2)
        self.assertEqual(set(result["provider_generation_attempt_ids"]),
                         {"attempt-1", "attempt-3"})

    def test_rejects_substituted_claimed_digest(self):
        value = fixture()
        value["rows"][0]["plan_sha256"] = "f" * 64
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)

    def test_rejects_wrong_provider_attempt_join(self):
        value = fixture()
        value["rows"][2]["prepare_receipt"]["attempt_id"] = "other-attempt"
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)

    def test_rejects_missing_independent_post_close_score(self):
        value = fixture()
        value["rows"][3]["execution"]["independent_score"] = False
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)

    def test_rejects_unknown_final_task_success(self):
        value = fixture()
        value["rows"][0]["execution"]["task_success"] = None
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)

    def test_rejects_cross_task_warm_source(self):
        value = fixture()
        value["rows"][3]["source_task_id"] = "task-1"
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)

    def test_rejects_stale_owner_or_artifact_reuse_on_warm_task(self):
        value = fixture()
        value["rows"][1]["prepare_receipt"]["owner_id"] = "owner-task-1"
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)
        value = fixture()
        value["rows"][1]["prepare_receipt"]["artifact_id"] = "artifact-task-1"
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)

    def test_rejects_duplicate_public_prepare_attempt(self):
        value = fixture()
        value["rows"][1]["prepare_receipt"]["attempt_id"] = "attempt-1"
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)

    def test_accepts_partial_cold_trace_without_claiming_full_horizon(self):
        value = fixture()
        value["rows"] = value["rows"][:1]
        result = validate_plan_evidence_join(value)
        self.assertEqual(result["generated_plan_count"], 1)
        self.assertEqual(result["task_count"], 1)

    def test_rejects_post_repair_warm_without_repair(self):
        value = fixture()
        value["rows"] = [value["rows"][0], value["rows"][3]]
        with self.assertRaises(LedgerValidationError):
            validate_plan_evidence_join(value)

if __name__ == "__main__":
    unittest.main()
