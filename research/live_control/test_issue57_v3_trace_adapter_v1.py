"""Fail-closed projection tests for the frozen Issue #57 task evaluator."""
import copy
import json
from pathlib import Path
import unittest

from issue57_v3_trace_adapter_v1 import assemble_complete_trace, project_task
from integrated_efficiency_protocol_v1 import EXPECTED_MODEL_CALLS, TASKS


USAGE = {"input_tokens": 100, "cached_input_tokens": 20,
         "cache_write_input_tokens": 0, "output_tokens": 12,
         "reasoning_output_tokens": 3}


def caller(*, status="completed", usage=USAGE, outcome="TASK_SUCCEEDED"):
    effect = "succeeded" if outcome == "TASK_SUCCEEDED" else "failed"
    return {"outcome": outcome, "task_effect": effect,
        "attempt_ledger": [{"attempt_id": "attempt-1", "call_id": "call-1",
            "stage": "anchor_model", "status": status,
            "requested_model": "model-x", "requested_effort": "low",
            "usage": usage}],
        "accounting": {"attempted_calls": 1, "visible_images_submitted": 1}}


def telemetry(arm="plain", index=0):
    repair_required = arm == "persistent" and index == 3
    return {"local_observations": 4, "durable_calls": 7,
        "pointer_admissions": 2, "old_target_pointer_admissions": 0,
        "releases_verified": True, "elapsed_ns": 1000,
        "source_to_completion_ns": 900, "input_feedback_ns": [20, 30],
        "repair": ({"required": True, "old_reference_status": "missing",
            "old_reference_pointer_admissions": 0, "attempted": True,
            "succeeded": True} if repair_required else
            {"required": False, "old_reference_status": None,
             "old_reference_pointer_admissions": 0, "attempted": False,
             "succeeded": False})}


def score(exact=True):
    return {"submission_count": 1, "exact_submission": exact}


def scheduled_row(arm, index):
    count = EXPECTED_MODEL_CALLS[arm][index]
    public = caller()
    public["attempt_ledger"] *= count
    public["accounting"] = {"attempted_calls": count,
                            "visible_images_submitted": count}
    for attempt_index, attempt in enumerate(public["attempt_ledger"]):
        attempt.update(attempt_id=f"{arm}-{index}-{attempt_index}",
                       call_id=f"call-{arm}-{index}-{attempt_index}")
    return project_task(arm, index, public, score(), telemetry(arm, index))


class Issue57V3TraceAdapterTests(unittest.TestCase):
    def test_complete_v3_task_projects_to_exact_frozen_task_row(self):
        projected = project_task("plain", 0, caller(), score(), telemetry())
        self.assertEqual(projected["status"], "projected")
        row = projected["task_row"]
        self.assertEqual(row["model_calls"][0]["usage"], USAGE)
        self.assertEqual(row["route"], "cold")
        self.assertEqual(row["typed_outcome"], "completed")
        self.assertEqual(row["model_visible_images"], 1)

    def test_failed_attempt_is_held_with_full_record_not_dropped(self):
        public = caller(status="failed", usage=None, outcome="CALLER_FAILED")
        projected = project_task("plain", 0, public, score(False), telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"], "failed_attempt_not_representable_in_v1")
        self.assertIsNone(projected["task_row"])
        self.assertEqual(projected["caller_result"]["attempt_ledger"],
                         public["attempt_ledger"])

    def test_partial_usage_is_held_instead_of_zero_filled(self):
        partial = {"input_tokens": 100, "cached_input_tokens": 20,
                   "output_tokens": 12, "reasoning_output_tokens": 3}
        projected = project_task("plain", 0, caller(usage=partial), score(), telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"], "usage_incomplete_or_invalid")
        self.assertEqual(projected["caller_result"]["attempt_ledger"][0]["usage"], partial)

    def test_wrong_frozen_call_count_is_held_with_attempts(self):
        public = caller()
        public["attempt_ledger"].append({"attempt_id": "attempt-2", "call_id": "call-2",
            "stage": "expanded_model", "status": "completed",
            "requested_model": "model-x", "requested_effort": "low", "usage": USAGE})
        public["accounting"]["attempted_calls"] = 2
        projected = project_task("plain", 0, public, score(), telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"], "assigned_model_attempt_count_mismatch")
        self.assertEqual(len(projected["caller_result"]["attempt_ledger"]), 2)

    def test_independent_success_conflict_is_held_with_both_records(self):
        public = caller()
        independent = score(False)
        projected = project_task("plain", 0, public, independent, telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"],
                         "independent_score_caller_failure_disagreement")
        self.assertEqual(projected["caller_result"], public)
        self.assertEqual(projected["independent_score"], independent)

    def test_v3_attempt_count_disagreement_is_held_without_rewriting_ledger(self):
        public = caller()
        public["accounting"]["attempted_calls"] = 0
        projected = project_task("plain", 0, public, score(), telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"], "caller_attempt_count_mismatch")
        self.assertEqual(projected["caller_result"]["accounting"]["attempted_calls"], 0)
        self.assertEqual(len(projected["caller_result"]["attempt_ledger"]), 1)

    def test_assembler_never_omits_held_assigned_rows(self):
        projected = project_task("plain", 0, caller(status="failed", usage=None,
            outcome="CALLER_FAILED"), score(False), telemetry())
        rows = {arm: [scheduled_row(arm, index) for index in range(6)]
                for arm in ("plain", "ephemeral", "persistent")}
        rows["plain"][0] = projected
        result = assemble_complete_trace(rows, {}, [])
        self.assertEqual(result["status"], "HOLD")
        self.assertIsNone(result["trace"])
        self.assertEqual(len(result["all_rows"]["plain"]), 6)
        self.assertEqual(result["held_rows"][0]["caller_result"]["attempt_ledger"],
                         projected["caller_result"]["attempt_ledger"])

    def test_assembler_rejects_wrong_task_mapping_without_row_loss(self):
        rows = {arm: [scheduled_row(arm, index) for index in range(6)]
                for arm in ("plain", "ephemeral", "persistent")}
        wrong = copy.deepcopy(rows["plain"][0])
        wrong["task_index"] = 1
        rows["plain"][0] = wrong
        result = assemble_complete_trace(rows, {}, [])
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"], "assigned_row_identity_mismatch")
        self.assertEqual(result["all_rows"], rows)

    def test_frozen_historical_trace_round_trips_through_assembler(self):
        root = Path(__file__).resolve().parent
        source = root / "results" / "integrated-efficiency-live-01" / "trace.json"
        report = root / "results" / "integrated-efficiency-live-01" / "report.json"
        frozen_trace = json.loads(source.read_text(encoding="utf-8"))
        historical_report = json.loads(report.read_text(encoding="utf-8"))
        rows = {}
        for arm, task_rows in frozen_trace["arms"].items():
            rows[arm] = [{"schema": "issue57-v3-task-projection-v1",
                "status": "projected", "reason": None, "arm": arm,
                "task_index": index, "task_id": row["task_id"],
                "route": row["route"], "caller_result": {},
                "independent_score": {}, "telemetry": {},
                "task_row": copy.deepcopy(row)}
                for index, row in enumerate(task_rows)]
        assembled = assemble_complete_trace(rows, frozen_trace["preflight_calls"],
            frozen_trace["integration_discoveries"])
        self.assertEqual(assembled["status"], "ready_for_frozen_evaluator")
        self.assertEqual(assembled["trace"], frozen_trace)
        self.assertEqual(assembled["evaluation"]["disposition"],
                         historical_report["evaluation"]["disposition"])

    def test_complete_task_rows_with_missing_preflight_are_held(self):
        rows = {arm: [scheduled_row(arm, index) for index in range(6)]
                for arm in ("plain", "ephemeral", "persistent")}
        assembled = assemble_complete_trace(rows, {}, [])
        self.assertEqual(assembled["status"], "HOLD")
        self.assertTrue(assembled["reason"].startswith("frozen_evaluator_rejected_trace:"))
        self.assertIsNone(assembled["trace"])
        self.assertEqual(sum(len(values) for values in assembled["all_rows"].values()), 18)

    def test_non_mapping_preflight_and_discovery_are_preserved_on_hold(self):
        rows = {arm: [scheduled_row(arm, index) for index in range(6)]
                for arm in ("plain", "ephemeral", "persistent")}
        preflight = ["provider-preflight-not-accounted"]
        discoveries = ["integration-discovery-not-accounted"]
        assembled = assemble_complete_trace(rows, preflight, discoveries)
        self.assertEqual(assembled["status"], "HOLD")
        self.assertEqual(assembled["all_rows"], rows)
        self.assertIsNone(assembled["trace"])
        self.assertIn("provider-preflight-not-accounted", str(assembled))
        self.assertIn("integration-discovery-not-accounted", str(assembled))

    def test_arm_order_mismatch_is_rejected_before_projection(self):
        rows = {arm: [scheduled_row(arm, index) for index in range(6)]
                for arm in ("plain", "ephemeral", "persistent")}
        reversed_rows = {arm: rows[arm] for arm in ("ephemeral", "plain", "persistent")}
        with self.assertRaisesRegex(ValueError, "frozen arm order required"):
            assemble_complete_trace(reversed_rows, {}, [])


if __name__ == "__main__":
    unittest.main()
