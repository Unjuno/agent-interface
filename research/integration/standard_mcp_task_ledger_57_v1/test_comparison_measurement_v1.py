import unittest

from comparison_measurement_v1 import (
    validate_matched_block,
    validate_measured_run,
    validate_reuse_horizon,
)
from ledger import LedgerValidationError


def run(arm, order, *, block=1, task_index=1, model_tokens=(8, 2), success=True,
        elapsed_ns=30):
    request_image = "1" * 64
    local_image = "2" * 64
    record = {
        "schema": "agent-interface/standard-mcp-task-ledger-v1",
        "run_id": f"run-{arm}",
        "comparison": {"arm": arm, "block": block, "order": order,
                       "task_seed": f"seed-{task_index:02d}"},
        "task": {"task_id": f"task-{task_index:02d}", "fixture_sha256": "a" * 64,
                 "scorer_sha256": "b" * 64},
        "source": {"commit": "c" * 40, "route_sha256": ("d" if arm == "A"
                    else "e" if arm == "B" else "f") * 64},
        "environment_sha256": "9" * 64,
        "model": {"id": "model-x", "effort": "low",
                  "request_config_sha256": "8" * 64},
        "raw_refs": [
            {"path": "raw/request-image.png", "sha256": request_image},
            {"path": "raw/local-observation.png", "sha256": local_image},
            {"path": "raw/events.jsonl", "sha256": "7" * 64},
        ],
        "events": ([
            {"seq": 1, "kind": "model_attempt", "attempt_id": f"model-{arm}-{task_index}",
             "status": "completed", "started_ns": 10, "ended_ns": 20,
             "usage": {"status": "reported", "input_tokens": model_tokens[0],
                       "output_tokens": model_tokens[1]}},
            {"seq": 2, "kind": "tool_call", "call_id": f"observe-{arm}-{task_index}",
             "model_attempt_id": f"model-{arm}-{task_index}",
             "method": "interface_guarded_observe", "started_ns": 20,
             "ended_ns": 25,
             "result": {"source": {"sequence": 4}}},
        ] if model_tokens is not None else [
            {"seq": 1, "kind": "tool_call", "call_id": f"observe-{arm}-{task_index}",
             "model_attempt_id": None, "method": "interface_guarded_observe",
             "started_ns": 20, "ended_ns": 25,
             "result": {"source": {"sequence": 4}}},
        ]) + [
            {"seq": 3 if model_tokens is not None else 2,
             "kind": "task_score", "scorer_id": "oracle-v1",
             "independent": True, "task_success": success,
             "state_sha256": "6" * 64, "started_ns": 30, "ended_ns": 31}],
    }
    measurement = {
        "started_ns": 5, "ended_ns": 5 + elapsed_ns, "elapsed_ns": elapsed_ns,
        "phases": ([
            {"name": "setup_acquisition", "started_ns": 5, "ended_ns": 10},
            {"name": "provider_wait", "started_ns": 10, "ended_ns": 20},
        ] if model_tokens is not None else [
            {"name": "setup_acquisition", "started_ns": 5, "ended_ns": 20},
        ]) + [
            {"name": "observation_grounding", "started_ns": 20, "ended_ns": 25},
            {"name": "local_execution", "started_ns": 25, "ended_ns": 30},
            {"name": "effect_verification", "started_ns": 30, "ended_ns": 31},
            {"name": "cleanup", "started_ns": 31, "ended_ns": 5 + elapsed_ns},
        ],
        "model_delivered_images": ([] if model_tokens is None else [
            {"attempt_id": f"model-{arm}-{task_index}", "sha256": request_image}]),
        "local_observations": [{"tool_call_id": f"observe-{arm}-{task_index}",
                                "source_sequence": 4, "captured_ns": 23,
                                "image_sha256": local_image}],
    }
    return {"task_ledger": record, "measurement": measurement}


class ComparisonMeasurementTests(unittest.TestCase):
    @staticmethod
    def horizon():
        blocks = []
        trace = []
        plan_hashes = {1: "3" * 64, 2: "3" * 64,
                       3: "5" * 64, 4: "5" * 64}
        dependency_hashes = {1: "4" * 64, 2: "4" * 64,
                             3: "6" * 64, 4: "6" * 64}
        baseline_tokens = {1: (8, 2), 2: (16, 4),
                           3: (24, 6), 4: (32, 8)}
        for index in range(1, 5):
            c_tokens = (8, 2) if index in (1, 3) else None
            declared_order = [["A", "B", "C"], ["B", "C", "A"],
                              ["C", "A", "B"], ["A", "B", "C"]][index - 1]
            order_by_arm = {arm: position for position, arm in
                            enumerate(declared_order, start=1)}
            blocks.append({"task_index": index, "runs": [
                run("A", order_by_arm["A"], block=index, task_index=index,
                    model_tokens=baseline_tokens[index], elapsed_ns=40),
                run("B", order_by_arm["B"], block=index, task_index=index,
                    model_tokens=baseline_tokens[index], elapsed_ns=40),
                run("C", order_by_arm["C"], block=index, task_index=index,
                    model_tokens=c_tokens),
            ], "predeclared_order": declared_order})
            mode = {1: "cold", 2: "warm", 3: "repair",
                    4: "post_repair_warm"}[index]
            trace.append({
                "task_index": index,
                "mode": mode,
                "plan_sha256": plan_hashes[index],
                "source_task_index": {1: None, 2: 1, 3: 3, 4: 3}[index],
                "dependency_sha256": dependency_hashes[index],
                "plan_generation_attempt_ids": (
                    [f"model-C-{index}"] if index in (1, 3) else []),
                "attempt_dispositions": ([{
                    "attempt_id": f"model-C-{index}",
                    "disposition": "plan_generation",
                }] if index in (1, 3) else []),
            })
        return {
            "schema": "agent-interface/reuse-horizon-comparison-v2",
            "comparison_id": "synthetic-reuse-horizon",
            "predeclared_horizon": 4,
            "invalidation_after_task_index": 2,
            "blocks": blocks,
            "c_plan_trace": trace,
        }

    def test_matched_block_reports_time_phases_and_image_classes_separately(self):
        result = validate_matched_block([run("A", 1), run("B", 2), run("C", 3)])
        self.assertEqual(result["block"], 1)
        self.assertEqual(set(result["arms"]), {"A", "B", "C"})
        for arm in result["arms"].values():
            self.assertEqual(arm["elapsed_ns"], 30)
            self.assertEqual(arm["model_delivered_image_count"], 1)
            self.assertEqual(arm["local_observation_count"], 1)
            self.assertEqual(arm["task_success"], True)

    def test_phase_gap_or_overlap_is_rejected(self):
        value = run("A", 1)
        value["measurement"]["phases"][2]["started_ns"] = 24
        with self.assertRaises(LedgerValidationError):
            validate_measured_run(value)

    def test_image_digest_must_be_retained_and_tied_to_an_attempt(self):
        value = run("A", 1)
        value["measurement"]["model_delivered_images"][0]["sha256"] = "5" * 64
        with self.assertRaises(LedgerValidationError):
            validate_measured_run(value)
        value = run("A", 1)
        value["measurement"]["model_delivered_images"][0]["attempt_id"] = "unknown"
        with self.assertRaises(LedgerValidationError):
            validate_measured_run(value)

    def test_local_observation_must_match_observation_tool_receipt(self):
        value = run("A", 1)
        value["measurement"]["local_observations"][0]["source_sequence"] = 5
        with self.assertRaises(LedgerValidationError):
            validate_measured_run(value)

    def test_matched_block_rejects_model_or_task_condition_mismatch(self):
        values = [run("A", 1), run("B", 2), run("C", 3)]
        values[2]["task_ledger"]["model"]["effort"] = "high"
        with self.assertRaises(LedgerValidationError):
            validate_matched_block(values)
        values = [run("A", 1), run("B", 2), run("C", 3)]
        values[1]["task_ledger"]["task"]["fixture_sha256"] = "5" * 64
        with self.assertRaises(LedgerValidationError):
            validate_matched_block(values)

    def test_reuse_horizon_separates_tokens_latency_and_correctness_qualified_break_even(self):
        result = validate_reuse_horizon(self.horizon())
        self.assertEqual(result["token_break_even_task_index"], {"A": 2, "B": 2})
        self.assertEqual(result["correctness_qualified_token_break_even_task_index"],
                         {"A": 2, "B": 2})
        self.assertEqual(result["elapsed_break_even_task_index"], {"A": 1, "B": 1})
        self.assertEqual(result["correctness_qualified_elapsed_break_even_task_index"],
                         {"A": 1, "B": 1})
        self.assertEqual(result["cumulative"]["C"]["total_tokens"],
                         [10, 10, 20, 20])
        self.assertEqual(result["cumulative"]["A"]["total_tokens"],
                         [10, 30, 60, 100])
        self.assertEqual(result["cumulative"]["A"]["elapsed_ns"],
                         [40, 80, 120, 160])
        self.assertEqual(result["cumulative"]["C"]["elapsed_ns"],
                         [30, 60, 90, 120])

    def test_break_even_is_not_correctness_qualified_after_any_failed_task(self):
        value = self.horizon()
        value["blocks"][0]["runs"][0]["task_ledger"]["events"][-1][
            "task_success"] = False
        result = validate_reuse_horizon(value)
        self.assertEqual(result["token_break_even_task_index"], {"A": 2, "B": 2})
        self.assertEqual(
            result["correctness_qualified_token_break_even_task_index"],
            {"A": None, "B": None})
        self.assertEqual(result["elapsed_break_even_task_index"], {"A": 1, "B": 1})
        self.assertEqual(
            result["correctness_qualified_elapsed_break_even_task_index"],
            {"A": None, "B": None})

    def test_reuse_horizon_rejects_unscored_cold_plan_and_wrong_repair_lineage(self):
        value = self.horizon()
        value["blocks"][0]["runs"][2]["task_ledger"]["events"][-1][
            "task_success"] = False
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)

    def test_reuse_horizon_accounts_for_non_generation_warm_attempt(self):
        value = self.horizon()
        value["blocks"][1]["runs"][2] = run(
            "C", 2, block=2, task_index=2, model_tokens=(1, 1), elapsed_ns=40)
        events = value["blocks"][1]["runs"][2]["task_ledger"]["events"]
        events[0]["ended_ns"] = 30
        events[1]["started_ns"], events[1]["ended_ns"] = 30, 35
        events[2]["started_ns"], events[2]["ended_ns"] = 40, 41
        value["blocks"][1]["runs"][2]["measurement"][
            "local_observations"][0]["captured_ns"] = 33
        phases = value["blocks"][1]["runs"][2]["measurement"]["phases"]
        phases[1]["ended_ns"] = 30
        phases[2]["started_ns"], phases[2]["ended_ns"] = 30, 35
        phases[3]["started_ns"], phases[3]["ended_ns"] = 35, 40
        phases[4]["started_ns"], phases[4]["ended_ns"] = 40, 41
        phases[5]["started_ns"] = 41
        value["c_plan_trace"][1]["attempt_dispositions"] = [{
            "attempt_id": "model-C-2", "disposition": "stale_response"}]
        result = validate_reuse_horizon(value)
        self.assertEqual(result["cumulative"]["C"]["total_tokens"],
                         [10, 12, 22, 22])
        self.assertEqual(result["cumulative"]["C"]["elapsed_ns"],
                         [30, 70, 100, 130])
        self.assertEqual(result["plan_trace"][1]["attempt_dispositions"],
                         [{"attempt_id": "model-C-2",
                           "disposition": "stale_response"}])

        value["c_plan_trace"][1]["attempt_dispositions"] = []
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)
        value["c_plan_trace"][1]["attempt_dispositions"] = [{
            "attempt_id": "model-C-2", "disposition": "plan_generation"}]
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)

        value = self.horizon()
        value["blocks"][1]["runs"][2] = run(
            "C", 2, block=2, task_index=2, model_tokens=(1, 1))
        value["c_plan_trace"][1]["attempt_dispositions"] = [{
            "attempt_id": "model-C-2", "disposition": "timeout"}]
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)

    def test_reuse_horizon_marks_token_total_unknown_for_unavailable_warm_attempt(self):
        value = self.horizon()
        value["blocks"][1]["runs"][2] = run(
            "C", 2, block=2, task_index=2, model_tokens=(1, 1))
        attempt = value["blocks"][1]["runs"][2]["task_ledger"]["events"][0]
        attempt["status"] = "failed"
        attempt["usage"] = {"status": "unavailable", "input_tokens": None,
                            "output_tokens": None}
        value["c_plan_trace"][1]["attempt_dispositions"] = [{
            "attempt_id": "model-C-2", "disposition": "failure"}]
        result = validate_reuse_horizon(value)
        self.assertEqual(result["cumulative"]["C"]["total_tokens"],
                         [10, None, None, None])
        self.assertEqual(result["cumulative"]["C"]["elapsed_ns"],
                         [30, 60, 90, 120])
        self.assertEqual(result["token_break_even_task_index"],
                         {"A": None, "B": None})

    def test_reuse_horizon_rejects_route_drift_and_invalid_attempt_lineage(self):
        value = self.horizon()
        value["blocks"][3]["runs"][1]["task_ledger"]["source"][
            "route_sha256"] = "0" * 64
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)
        value = self.horizon()
        value["blocks"][0]["predeclared_order"] = ["B", "A", "C"]
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)
        value = self.horizon()
        value["c_plan_trace"][2]["source_task_index"] = 1
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)

    def test_reuse_horizon_does_not_report_break_even_when_usage_is_incomplete(self):
        value = self.horizon()
        value["blocks"][0]["runs"][0]["task_ledger"]["events"][0]["usage"] = {
            "status": "unavailable", "input_tokens": None, "output_tokens": None}
        value["blocks"][0]["runs"][0]["task_ledger"]["events"][0]["status"] = "failed"
        result = validate_reuse_horizon(value)
        self.assertEqual(result["token_break_even_task_index"], {"A": None, "B": 2})

    def test_reuse_horizon_requires_model_pin_and_successful_repair(self):
        value = self.horizon()
        for arm_run in value["blocks"][0]["runs"]:
            arm_run["task_ledger"]["model"] = None
            arm_run["task_ledger"]["events"] = [event for event in
                arm_run["task_ledger"]["events"] if event["kind"] != "model_attempt"]
            for event in arm_run["task_ledger"]["events"]:
                if event["kind"] == "tool_call":
                    event["model_attempt_id"] = None
            arm_run["measurement"]["model_delivered_images"] = []
            arm_run["measurement"]["phases"] = [
                {"name": "setup_acquisition", "started_ns": 5, "ended_ns": 20},
                {"name": "observation_grounding", "started_ns": 20, "ended_ns": 25},
                {"name": "local_execution", "started_ns": 25, "ended_ns": 30},
                {"name": "effect_verification", "started_ns": 30, "ended_ns": 31},
                {"name": "cleanup", "started_ns": 31, "ended_ns": 35},
            ]
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)
        value = self.horizon()
        value["blocks"][2]["runs"][2]["task_ledger"]["events"][-1][
            "task_success"] = False
        with self.assertRaises(LedgerValidationError):
            validate_reuse_horizon(value)

    def test_other_phase_requires_reason_and_all_ledger_events_fit_lifecycle(self):
        value = run("A", 1)
        phase = value["measurement"]["phases"][0]
        phase["name"] = "other"
        with self.assertRaises(LedgerValidationError):
            validate_measured_run(value)
        phase["reason"] = "unclassified host work"
        value["task_ledger"]["events"][0]["ended_ns"] = 36
        with self.assertRaises(LedgerValidationError):
            validate_measured_run(value)


if __name__ == "__main__":
    unittest.main()
