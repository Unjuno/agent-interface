"""Offline integrity checks for the v3 Issue #57 all-attempt row."""
import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from issue57_v3_attempt_ledger_v1 import AppendOnlyAttemptLedger, make_row
from test_compiled_native_caller_composition import CompiledNativeCallerTests
from adaptive_acquisition_caller_v3 import ModelFailure, run as run_v3


def result(*, outcome="TASK_SUCCEEDED", task_effect="succeeded", attempts=None,
           receipt=None, execution=None):
    attempts = attempts if attempts is not None else [{
        "attempt_id": "a1", "call_id": "call-1", "status": "completed",
        "usage": {"input_tokens": 10}}]
    return {"outcome": outcome, "reason": "test", "task_effect": task_effect,
            "delivery": "confirmed", "attempt_ledger": attempts,
            "accounting": {"attempted_calls": len(attempts),
                           "usage_totals": None, "visible_image_coverage": 0,
                           "model_wait_coverage": 0},
            "compiled_execution_receipt": receipt,
            "execution_progress": execution}


def release(status="succeeded", *, verified=True, keys=None, buttons=None):
    keys = [] if keys is None else keys
    buttons = [] if buttons is None else buttons
    return {"status": status, "verified": verified,
            "keys_down": keys, "buttons_down": buttons,
            "evidence_ref": "release://one", "evidence_digest": "sha256:release"}


def effect(status="succeeded"):
    return {"status": status, "evidence_ref": "effect://one" if status == "succeeded" else None,
            "evidence_digest": "sha256:effect" if status == "succeeded" else None}


class Issue57V3LedgerTests(unittest.TestCase):
    def test_real_v3_provider_failure_keeps_unknown_usage_and_unattempted_effect(self):
        spec = {"target": "form", "route": "cold",
            "coarse_origin": "caller_provided", "provided_coarse": {"source": "frame-1"},
            "cached_target": None, "local_repair_on": [], "repair_on": [],
            "session_id": "offline-provider-failure"}
        def fail(_payload):
            raise ModelFailure("transport timeout", call_id="turn-call-1",
                thread_id="thread-1", requested_model="model-x",
                requested_effort="low", usage=None,
                visible_images_submitted=1, wait_ns=500)
        caller = run_v3(spec, {
            "observe_source": lambda _: {"frame": "frame-1"},
            "acquire_anchor": lambda _: {"frame": "frame-1"},
            "anchor_model": fail,
        }, id_factory=lambda: "attempt-1")
        self.assertEqual(caller["outcome"], "CALLER_FAILED")
        self.assertIsNone(caller["task_effect"])
        self.assertEqual(caller["attempt_ledger"][0]["call_id"], "turn-call-1")
        self.assertIsNone(caller["attempt_ledger"][0]["usage"])
        self.assertEqual(caller["accounting"]["attempted_calls"], 1)
        row = make_row("provider-failure-01", caller,
            release("unavailable", verified=False), effect("unavailable"))
        self.assertIsNone(row["task_effect"])
        self.assertEqual(row["effect_receipt"]["status"], "unavailable")

    def test_actual_v3_compiled_fake_transport_result_enters_attempt_ledger(self):
        native = CompiledNativeCallerTests("runTest").cell()
        caller = native["result"]
        receipts = native["terminals"]
        self.assertTrue(receipts)
        self.assertTrue(all(item["release"]["verified"] is True and
                            item["release"]["keys_down"] == [] and
                            item["release"]["buttons_down"] == []
                            for item in receipts if item["status"] == "completed"))
        release_digest = hashlib.sha256(json.dumps(receipts, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        release_receipt = {"status": "succeeded", "verified": True,
            "keys_down": [], "buttons_down": [],
            "evidence_ref": "fake-x-terminal-set://one",
            "evidence_digest": "sha256:" + release_digest}
        effect_receipt = {"status": caller["task_effect"],
            "evidence_ref": None, "evidence_digest": None}
        with tempfile.TemporaryDirectory() as td:
            ledger = AppendOnlyAttemptLedger(Path(td) / "ledger.jsonl",
                                               ["candidate-compiled-fakex-01"])
            row = make_row("candidate-compiled-fakex-01", caller,
                           release_receipt, effect_receipt)
            ledger.append(row)
            audit = ledger.audit()
        self.assertEqual(audit["rows"], 1)
        self.assertEqual(row["compiled_execution_receipt"],
                         caller["compiled_execution_receipt"])
        self.assertEqual(row["attempt_ledger"], caller["attempt_ledger"])
        self.assertEqual(row["release_receipt"]["status"], "succeeded")
        self.assertEqual(row["effect_receipt"]["status"], "unavailable")

    def test_row_joins_public_result_core_receipts_and_raw_hash(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.json"
            raw.write_text('{"retained":true}\n', encoding="utf-8")
            core = {"outcome": "SAFE_YIELD", "completed_transitions": 1,
                    "critical_events": [{"event": "action_terminal",
                                         "input_dispatched": True}]}
            row = make_row("pair-1-A", result(outcome="TASK_NOT_VERIFIED",
                task_effect="succeeded", receipt=core,
                execution={"status": "completed"}),
                release(), effect(), [raw])
            self.assertEqual(row["compiled_execution_receipt"], core)
            self.assertEqual(row["release_receipt"]["keys_down"], [])
            self.assertEqual(row["raw_evidence"][0]["size_bytes"], raw.stat().st_size)
            self.assertEqual(len(row["raw_evidence"][0]["sha256"]), 64)

    def test_failed_unknown_usage_attempt_is_retained_without_zero_imputation(self):
        attempts = [
            {"attempt_id": "a1", "call_id": "call-1", "status": "completed",
             "usage": {"input_tokens": 10}},
            {"attempt_id": "a2", "call_id": None, "status": "failed",
             "usage": None},
        ]
        public = result(outcome="CALLER_FAILED", task_effect="unavailable",
                        attempts=attempts, execution={"status": "delivery_uncertain"})
        row = make_row("pair-1-B", public,
                       release("unavailable", verified=False), effect("unavailable"))
        self.assertEqual(len(row["attempt_ledger"]), 2)
        self.assertIsNone(row["attempt_ledger"][1]["usage"])
        self.assertIsNone(row["accounting"]["usage_totals"])

    def test_successful_release_with_down_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty key/button"):
            make_row("pair-1", result(), release(keys=["CTRL"]), effect())

    def test_effect_status_must_match_public_caller_verdict(self):
        with self.assertRaisesRegex(ValueError, "disagree"):
            make_row("pair-1", result(task_effect="unavailable"), release(), effect())

    def test_assignment_duplicates_and_missing_rows_fail_audit(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = AppendOnlyAttemptLedger(Path(td) / "ledger.jsonl", ["A", "B"])
            a = make_row("A", result(), release(), effect())
            ledger.append(a)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                ledger.append(a)
            with self.assertRaisesRegex(ValueError, "missing"):
                ledger.audit()
            b = make_row("B", result(outcome="TASK_NOT_VERIFIED",
                          task_effect="unavailable"),
                         release("unavailable", verified=False), effect("unavailable"))
            ledger.append(b)
            audit = ledger.audit()
            self.assertEqual(audit["rows"], 2)
            self.assertEqual(audit["attempts"], 2)
            persisted = [json.loads(line) for line in
                         (Path(td) / "ledger.jsonl").read_text().splitlines()]
            self.assertEqual([row["assignment_id"] for row in persisted], ["A", "B"])

    def test_unassigned_ids_and_duplicate_attempt_ids_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = AppendOnlyAttemptLedger(Path(td) / "ledger.jsonl", ["A"])
            row = make_row("B", result(), release(), effect())
            with self.assertRaisesRegex(ValueError, "unassigned"):
                ledger.append(row)
        duplicate = [{"attempt_id": "same"}, {"attempt_id": "same"}]
        with self.assertRaisesRegex(ValueError, "duplicate attempt"):
            make_row("A", result(attempts=duplicate), release(), effect())

    def test_post_write_receipt_tampering_is_detected_by_audit(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            ledger = AppendOnlyAttemptLedger(path, ["A"])
            ledger.append(make_row("A", result(), release(), effect()))
            value = json.loads(path.read_text())
            value["release_receipt"]["keys_down"] = ["CTRL"]
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty key/button"):
                ledger.audit()

    def test_post_write_row_field_deletion_is_rejected_cleanly(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            ledger = AppendOnlyAttemptLedger(path, ["A"])
            ledger.append(make_row("A", result(), release(), effect()))
            value = json.loads(path.read_text())
            del value["attempt_ledger"]
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "fields are incomplete"):
                ledger.audit()


if __name__ == "__main__":
    unittest.main()
