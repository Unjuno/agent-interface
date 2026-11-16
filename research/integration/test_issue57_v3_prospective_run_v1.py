"""Custody checks for the prospective Issue #57 v3 run journal."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.live_control.issue57_v3_prospective_run_v1 import (
    REQUIRED_ALLOCATION, ProspectiveRun,
)
from research.live_control.integrated_efficiency_protocol_v1 import ARMS, TASKS
from research.live_control.integrated_efficiency_protocol_v1 import EXPECTED_MODEL_CALLS


USAGE = {"input_tokens": 100, "cached_input_tokens": 20,
         "cache_write_input_tokens": 0, "output_tokens": 12,
         "reasoning_output_tokens": 3}
USAGE_FIELDS = tuple(USAGE)


def synthetic_caller(arm, index):
    attempts = []
    for number in range(EXPECTED_MODEL_CALLS[arm][index]):
        attempts.append({"attempt_id": f"attempt-{arm}-{index}-{number}",
            "call_id": f"call-{arm}-{index}-{number}", "stage": "anchor_model",
            "status": "completed", "requested_model": "test-model",
            "requested_effort": "low", "usage": dict(USAGE), "cost": None,
            "visible_images_submitted": 1, "wait_ns": 100 + number})
    model_calls = [{"attempt_id": row["attempt_id"], **{
        field: row[field] for field in ("call_id", "stage", "requested_model",
            "requested_effort", "usage", "cost", "visible_images_submitted", "wait_ns")}}
        for row in attempts]
    count = len(attempts)
    totals = {field: sum(row["usage"][field] for row in attempts)
              for field in USAGE_FIELDS}
    usage_coverage = {field: count for field in USAGE_FIELDS}
    wait = sum(row["wait_ns"] for row in attempts)
    return {"outcome": "TASK_SUCCEEDED", "task_effect": "succeeded",
        "attempt_ledger": attempts, "model_call_ledger": model_calls,
        "accounting": {"attempted_calls": count, "completed_calls": count,
            "duplicate_call_ids": [], "usage_totals": totals,
            "usage_coverage": usage_coverage,
            "visible_images_submitted": count,
            "visible_image_coverage": count,
            "model_wait_ns": wait, "model_wait_coverage": count,
            "cost_coverage": 0, "cost": (0 if count == 0 else None),
            "cached_input_semantics":
                "subset of input_tokens; never added to input total"}}


def synthetic_telemetry(arm, index):
    repair = arm == "persistent" and index == 3
    return {"local_observations": 4, "durable_calls": 7,
        "pointer_admissions": 2, "old_target_pointer_admissions": 0,
        "releases_verified": True, "elapsed_ns": 1000,
        "source_to_completion_ns": 900, "input_feedback_ns": [20, 30],
        "repair": ({"required": True, "old_reference_status": "missing",
            "old_reference_pointer_admissions": 0, "attempted": True,
            "succeeded": True} if repair else {"required": False,
            "old_reference_status": None, "old_reference_pointer_admissions": 0,
            "attempted": False, "succeeded": False})}


class ProspectiveRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="issue57-prospective-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = Path(__file__).resolve().parents[2]
        self.allocation = self.root / "allocation.json"
        self.evidence = self.root / "new-evidence"
        self.value = {
            "allocation_id": "allocation-new-001", "host_id": "host-exclusive-001",
            "owner": "test-owner", "exclusive": True,
            "expires_at_utc": "2099-01-01T00:00:00Z", "task_ids": list(TASKS),
            "arms": list(ARMS), "model": "test-model",
            "settings": {"effort": "low", "timeout_s": 90}, "order_seed": 7,
        }

    def save_allocation(self):
        self.allocation.write_text(json.dumps(self.value), encoding="utf-8")

    def create(self):
        self.save_allocation()
        return ProspectiveRun(self.allocation, self.evidence, source_root=self.repo,
                              allocation_verifier=lambda _path, _data: True)

    def test_new_root_pins_sources_and_fsyncs_lifecycle_rows(self):
        run = self.create()
        manifest = json.loads(run.manifest_path.read_text(encoding="utf-8"))
        self.assertFalse(manifest["dispatch_enabled"])
        self.assertEqual(manifest["allocation_sha256"],
                         hashlib.sha256(self.allocation.read_bytes()).hexdigest())
        self.assertIn("research/live_control/issue57_v3_trace_adapter_v1.py",
                      manifest["source_files"])
        rows = [json.loads(line) for line in
                (self.evidence / "lifecycle.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([row["event"] for row in rows], ["run_created"])
        self.assertEqual(rows[0]["sequence"], 1)

    def test_rejects_nonexclusive_incomplete_or_reused_allocation(self):
        self.value["exclusive"] = False
        self.save_allocation()
        with self.assertRaisesRegex(ValueError, "exclusive"):
            ProspectiveRun(self.allocation, self.evidence, source_root=self.repo,
                           allocation_verifier=lambda _path, _data: True)
        self.assertFalse(self.evidence.exists())

        self.value["exclusive"] = True
        self.value["arms"] = ["plain"]
        self.save_allocation()
        with self.assertRaisesRegex(ValueError, "frozen six tasks"):
            ProspectiveRun(self.allocation, self.evidence, source_root=self.repo,
                           allocation_verifier=lambda _path, _data: True)

        self.value["arms"] = list(ARMS)
        self.save_allocation()
        self.evidence.mkdir()
        with self.assertRaises(FileExistsError):
            ProspectiveRun(self.allocation, self.evidence, source_root=self.repo,
                           allocation_verifier=lambda _path, _data: True)

    def test_rejects_expired_or_timezone_naive_allocation(self):
        self.value["expires_at_utc"] = "2000-01-01T00:00:00Z"
        self.save_allocation()
        with self.assertRaisesRegex(ValueError, "future"):
            ProspectiveRun(self.allocation, self.evidence, source_root=self.repo,
                           allocation_verifier=lambda _path, _data: True)
        self.value["expires_at_utc"] = "2099-01-01T00:00:00"
        self.save_allocation()
        with self.assertRaisesRegex(ValueError, "future timezone-aware"):
            ProspectiveRun(self.allocation, self.evidence, source_root=self.repo,
                           allocation_verifier=lambda _path, _data: True)

    def test_requires_external_allocation_attestation_before_root_creation(self):
        self.save_allocation()
        with self.assertRaisesRegex(ValueError, "trusted allocation verifier"):
            ProspectiveRun(self.allocation, self.evidence, source_root=self.repo,
                           allocation_verifier=None)
        with self.assertRaisesRegex(ValueError, "did not attest"):
            ProspectiveRun(self.allocation, self.evidence, source_root=self.repo,
                           allocation_verifier=lambda _path, _data: False)
        self.assertFalse(self.evidence.exists())

    def test_retains_all_assignments_and_holds_when_any_are_missing(self):
        run = self.create()
        run.record_preflight("plain", {"status": "synthetic-only"})
        projected = run.record_task("plain", 0, {"outcome": "UNKNOWN"}, None, None)
        self.assertEqual(projected["status"], "HOLD")
        with self.assertRaisesRegex(ValueError, "already recorded"):
            run.record_task("plain", 0, {"outcome": "UNKNOWN"}, None, None)
        result = run.finish({})
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(len(result["missing_assignments"]), 17)
        rows = [json.loads(line) for line in
                (self.evidence / "lifecycle.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([row["sequence"] for row in rows], [1, 2, 3, 4])
        self.assertEqual(rows[2]["payload"]["projection"], projected)
        saved = json.loads((self.evidence / "adjudication.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["reason"], "assigned_task_missing")
        self.assertIsNone(saved["adjudication"]["trace"])
        self.assertEqual(rows[-1]["payload"]["preflight_calls"],
                         {"plain": {"status": "synthetic-only"},
                          "ephemeral": None, "persistent": None})

    def test_complete_assignment_set_still_holds_without_comparable_evidence(self):
        run = self.create()
        for arm in ARMS:
            run.record_preflight(arm, {"status": "synthetic-only"})
            for index, task_id in enumerate(TASKS):
                projected = run.record_task(arm, index,
                    {"outcome": "UNKNOWN"}, None, None)
                self.assertEqual(projected["status"], "HOLD")
        result = run.finish({})
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["missing_assignments"], [])
        self.assertIsNone(result["adjudication"]["trace"])
        self.assertEqual(len(result["adjudication"]["held_rows"]), 18)

    def test_rejects_wrong_task_identity_without_consuming_assignment(self):
        run = self.create()
        projection = run.record_task("plain", 0, {"outcome": "UNKNOWN"}, None, None)
        self.assertEqual(projection["task_id"], TASKS[0])

    def test_finalized_run_rejects_mutation_and_second_adjudication(self):
        run = self.create()
        result = run.finish([])
        self.assertEqual(result["status"], "HOLD")
        with self.assertRaisesRegex(ValueError, "finalized"):
            run.record_preflight("plain", {})
        with self.assertRaisesRegex(ValueError, "finalized"):
            run.finish([])

    def test_all_synthetic_v3_rows_reach_frozen_evaluator(self):
        run = self.create()
        for arm_index, arm in enumerate(ARMS):
            run.record_preflight(arm, {"call_id": f"preflight-{arm}",
                "stage": "schema_preflight", "requested_model": "test-model",
                "requested_effort": "low", "usage": dict(USAGE),
                "model_visible_images": 0})
            for index, task_id in enumerate(TASKS):
                run.record_task(arm, index, synthetic_caller(arm, index),
                    {"submission_count": 1, "exact_submission": True},
                    synthetic_telemetry(arm, index))
        discoveries = json.loads((self.repo /
            "research/live_control/integrated_efficiency_discoveries_v1.json")
            .read_text(encoding="utf-8"))
        result = run.finish(discoveries)
        self.assertEqual(result["status"], "ready_for_frozen_evaluator",
            str([(row.get("arm"), row.get("task_index"), row.get("reason"))
                 for row in result["adjudication"].get("held_rows", [])]))
        self.assertEqual(result["missing_assignments"], [])
        self.assertIsNotNone(result["adjudication"]["trace"])
        self.assertEqual({arm: len(rows) for arm, rows in
            result["adjudication"]["trace"]["arms"].items()},
            {arm: 6 for arm in ARMS})
        saved = json.loads((self.evidence / "adjudication.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "ready_for_frozen_evaluator")


if __name__ == "__main__":
    unittest.main()
