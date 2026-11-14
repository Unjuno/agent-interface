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
    attempt = {"attempt_id": "attempt-1", "call_id": "call-1" if status == "completed" else None,
            "stage": "anchor_model", "status": status,
            "requested_model": "model-x", "requested_effort": "low",
            "usage": usage if status == "completed" else None,
            "cost": None, "visible_images_submitted": 1 if status == "completed" else None,
            "wait_ns": 100 if status == "completed" else None}
    attempts = [attempt]
    return {"outcome": outcome, "task_effect": effect,
        "attempt_ledger": attempts,
        "model_call_ledger": ([{"attempt_id": attempt["attempt_id"],
            **{key: attempt[key] for key in ("call_id", "stage", "requested_model",
               "requested_effort", "usage", "cost", "visible_images_submitted", "wait_ns")}}]
            if status == "completed" else []),
        "accounting": accounting_for(attempts)}


def accounting_for(attempts):
    coverage = {field: sum(type(row.get("usage")) is dict and field in row["usage"]
                           for row in attempts)
                for field in ("input_tokens", "cached_input_tokens",
                    "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")}
    totals = {field: (sum(row["usage"][field] for row in attempts
                          if type(row.get("usage")) is dict and field in row["usage"])
                      if coverage[field] == len(attempts) else None)
              for field in coverage}
    image_coverage = sum(row.get("visible_images_submitted") is not None for row in attempts)
    wait_coverage = sum(row.get("wait_ns") is not None for row in attempts)
    costs = [row["cost"] for row in attempts if row.get("cost") is not None]
    return {"attempted_calls": len(attempts),
        "completed_calls": sum(row.get("status") == "completed" for row in attempts),
        "duplicate_call_ids": [], "usage_totals": totals,
        "usage_coverage": coverage,
        "visible_images_submitted": (sum(row["visible_images_submitted"] for row in attempts)
            if image_coverage == len(attempts) else None),
        "visible_image_coverage": image_coverage,
        "model_wait_ns": (sum(row["wait_ns"] for row in attempts)
            if wait_coverage == len(attempts) else None),
        "model_wait_coverage": wait_coverage,
        "cost_coverage": len(costs),
        "cost": (sum(costs) if len(costs) == len(attempts) else None),
        "cached_input_semantics": "subset of input_tokens; never added to input total"}


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
    for attempt_index, attempt in enumerate(public["attempt_ledger"]):
        attempt.update(attempt_id=f"{arm}-{index}-{attempt_index}",
                       call_id=f"call-{arm}-{index}-{attempt_index}")
    public["model_call_ledger"] = [
        {"attempt_id": attempt["attempt_id"],
         **{key: attempt[key] for key in ("call_id", "stage", "requested_model",
            "requested_effort", "usage", "cost", "visible_images_submitted", "wait_ns")}}
        for attempt in public["attempt_ledger"]]
    public["accounting"] = accounting_for(public["attempt_ledger"])
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
            "requested_model": "model-x", "requested_effort": "low", "usage": USAGE,
            "cost": None, "visible_images_submitted": 1, "wait_ns": 100})
        public["model_call_ledger"].append({"attempt_id": "attempt-2", "call_id": "call-2",
            "stage": "expanded_model", "requested_model": "model-x",
            "requested_effort": "low", "usage": USAGE, "cost": None,
            "visible_images_submitted": 1, "wait_ns": 100})
        public["accounting"] = accounting_for(public["attempt_ledger"])
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

    def test_aggregate_usage_mismatch_is_held_with_source_attempt(self):
        public = caller()
        public["accounting"]["usage_totals"]["input_tokens"] += 1
        projected = project_task("plain", 0, public, score(), telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"],
                         "caller_accounting_mismatch:usage_totals")
        self.assertEqual(projected["caller_result"], public)

    def test_model_call_ledger_mismatch_is_held_with_both_rows(self):
        public = caller()
        public["model_call_ledger"][0]["requested_effort"] = "high"
        projected = project_task("plain", 0, public, score(), telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"],
                         "caller_accounting_mismatch:model_call_attempt_disagreement:requested_effort")
        self.assertEqual(projected["caller_result"], public)

    def test_boolean_is_not_accepted_as_numeric_accounting_count(self):
        public = caller()
        public["accounting"]["completed_calls"] = True
        projected = project_task("plain", 0, public, score(), telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"],
                         "caller_accounting_mismatch:accounting_invalid:completed_calls")

    def test_missing_attempt_id_is_held_with_source_result(self):
        public = caller()
        del public["attempt_ledger"][0]["attempt_id"]
        projected = project_task("plain", 0, public, score(), telemetry())
        self.assertEqual(projected["status"], "HOLD")
        self.assertEqual(projected["reason"], "attempt_identity_incomplete")
        self.assertEqual(projected["caller_result"], public)

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
