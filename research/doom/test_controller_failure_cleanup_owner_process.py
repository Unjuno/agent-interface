"""Contracts for the opt-in outer process-owner recovery gate."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from doom_controller_failure_cleanup_v1 import (
    ControllerFailureCleanup, read_owner_state_ledger, verify_or_recover_owner_process,
    verify_owner_process_recovery)


def receipt(display, pid, owner):
    release = {"event": "owner_release", "reason": "close", "verified": True,
               "keys_down": [], "buttons_down": [], "keys_unknown": [],
               "key_state_errors": []}
    return {"schema": "input-owner-recovery-v1", "display": display,
            "service_pid": pid, "service_start_ticks": 987,
            "owner_id": owner, "receipt_fsynced": True,
            "owner_thread_stopped": True, "close_error": None,
            "release_records": [release]}


class OwnerRecoveryGateTests(unittest.TestCase):
    class Planner:
        def close(self, timeout=1):
            return None

    def _cleanup_receipt(self, temp, recovery_result):
        out = Path(temp)
        runtime = out / "runtime"
        runtime.mkdir()
        cleanup = ControllerFailureCleanup(
            self.Planner(), out, owner_process_recovery=True)
        cleanup.process = SimpleNamespace(poll=lambda: -9)
        cleanup.events = [{"event": "input_owner_process_ready"}]
        cleanup.runtime = runtime
        error = RuntimeError("primary failure")
        with patch("doom_controller_failure_cleanup_v1.verify_or_recover_owner_process") as verify:
            if isinstance(recovery_result, BaseException):
                verify.side_effect = recovery_result
            elif recovery_result == "USE_RESULT":
                verify.return_value = {"recovery_mode": "supervisor_xtest_after_owner_process_death"}
            cleanup.__exit__(RuntimeError, error, None)
        return json.loads((out / "controller-failure.json").read_text())

    def test_failure_cleanup_allows_display_reuse_only_after_verified_emergency_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = self._cleanup_receipt(temp, "USE_RESULT")
            self.assertTrue(receipt["owner_process_recovery_verified"])
            self.assertTrue(receipt["owner_process_emergency_recovery_verified"])
            self.assertTrue(receipt["display_reuse_allowed"])

    def test_failure_cleanup_keeps_display_closed_when_owner_recovery_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = self._cleanup_receipt(temp, RuntimeError("focus mismatch"))
            self.assertFalse(receipt["owner_process_recovery_verified"])
            self.assertFalse(receipt["display_reuse_allowed"])

    def test_emergency_recovery_runs_only_after_normal_receipt_timeout(self):
        emergency = {"recovery_mode": "supervisor_xtest_after_owner_process_death"}
        with patch("doom_controller_failure_cleanup_v1.verify_owner_process_recovery",
                   side_effect=TimeoutError), patch(
                   "doom_controller_failure_cleanup_v1.recover_dead_owner_inputs",
                   return_value=emergency) as recover:
            self.assertIs(verify_or_recover_owner_process("runtime", []), emergency)
            recover.assert_called_once_with("runtime", [], kill=os.kill)

    def test_emergency_recovery_does_not_override_non_timeout_receipt_error(self):
        with patch("doom_controller_failure_cleanup_v1.verify_owner_process_recovery",
                   side_effect=ValueError("identity mismatch")), patch(
                   "doom_controller_failure_cleanup_v1.recover_dead_owner_inputs") as recover:
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                verify_or_recover_owner_process("runtime", [])
            recover.assert_not_called()

    def test_requires_matching_durable_receipt_and_dead_service(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "input-owner-process" / "input-owner-recovery-v1.json"
            target.parent.mkdir()
            target.write_text(json.dumps(receipt(":201", 23456, "owner-a")))
            events = [{"event": "input_owner_process_ready",
                       "schema": "input-owner-process-ready-v1",
                       "owner_id": "owner-a", "service_pid": 23456,
                       "service_start_ticks": 987,
                       "display": ":201", "receipt_path": str(target)}]
            def dead(pid, signal):
                self.assertEqual((pid, signal), (23456, 0))
                raise ProcessLookupError
            result = verify_owner_process_recovery(
                root, events, kill=dead, sleep=lambda _: None)
            self.assertEqual(result["owner_id"], "owner-a")

    def test_receipt_from_different_pid_generation_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "input-owner-process" / "input-owner-recovery-v1.json"
            target.parent.mkdir()
            target.write_text(json.dumps(receipt(":201", 23456, "owner-a")))
            events = [{"event": "input_owner_process_ready",
                       "schema": "input-owner-process-ready-v1",
                       "owner_id": "owner-a", "service_pid": 23456,
                       "service_start_ticks": 988,
                       "display": ":201", "receipt_path": str(target)}]
            with self.assertRaisesRegex(TimeoutError, "matching verified receipt"):
                verify_owner_process_recovery(
                    root, events, kill=lambda *_: (_ for _ in ()).throw(ProcessLookupError))

    def test_dead_owner_without_receipt_fails_normal_gate_immediately(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "input-owner-process" / "input-owner-recovery-v1.json"
            target.parent.mkdir()
            events = [{"event": "input_owner_process_ready",
                       "schema": "input-owner-process-ready-v1",
                       "owner_id": "owner-a", "service_pid": 23456,
                       "service_start_ticks": 987,
                       "display": ":201", "receipt_path": str(target)}]
            with self.assertRaisesRegex(TimeoutError, "without a matching verified receipt"):
                verify_owner_process_recovery(
                    root, events, timeout=100,
                    kill=lambda *_: (_ for _ in ()).throw(ProcessLookupError))

    def test_ledger_conservatively_retains_unacknowledged_down_and_button(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            owner = root / "input-owner-process"
            owner.mkdir()
            receipt_path = owner / "input-owner-recovery-v1.json"
            header = {"schema": "input-owner-state-ledger-v1", "record_type": "header",
                      "display": ":201", "service_pid": 23456,
                      "service_start_ticks": 987, "owner_id": "owner-a"}
            def transition(sequence, operation, phase, key, result=None):
                return {"schema": "input-owner-state-ledger-v1", "record_type": "transition",
                        "sequence": sequence, "request_id": sequence, "operation": operation,
                        "phase": phase, "display": ":201", "service_pid": 23456,
                        "service_start_ticks": 987, "owner_id": "owner-a",
                        "intent_token": "token-a", "expected_focus": 77,
                        "expected_surface": 77, "expected_geometry": [0, 0, 320, 200],
                        "key": key, "result": result}
            rows = [header, transition(1, "down", "intent", "a"),
                    transition(2, "button_down", "intent", 1)]
            ledger = owner / "input-owner-state-v1.jsonl"
            ledger.write_text("".join(json.dumps(row) + "\n" for row in rows))
            ready = {"event": "input_owner_process_ready",
                     "schema": "input-owner-process-ready-v1", "display": ":201",
                     "service_pid": 23456, "service_start_ticks": 987,
                     "owner_id": "owner-a", "receipt_path": str(receipt_path)}
            state = read_owner_state_ledger(root, [ready])
            self.assertEqual(set(state["active_keys"]), {"a"})
            self.assertEqual(set(state["active_buttons"]), {1})

    def test_ledger_rejects_untrusted_batch_key_type(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            owner = root / "input-owner-process"
            owner.mkdir()
            receipt_path = owner / "input-owner-recovery-v1.json"
            header = {"schema": "input-owner-state-ledger-v1", "record_type": "header",
                      "display": ":201", "service_pid": 23456,
                      "service_start_ticks": 987, "owner_id": "owner-a"}
            row = {"schema": "input-owner-state-ledger-v1", "record_type": "transition",
                   "sequence": 1, "request_id": 1, "operation": "up_batch", "phase": "intent",
                   "display": ":201", "service_pid": 23456, "service_start_ticks": 987,
                   "owner_id": "owner-a", "intent_token": "token-a", "expected_focus": 77,
                   "expected_surface": None, "expected_geometry": None, "key": [["bad"]], "result": None}
            (owner / "input-owner-state-v1.jsonl").write_text(
                json.dumps(header) + "\n" + json.dumps(row) + "\n")
            ready = {"event": "input_owner_process_ready",
                     "schema": "input-owner-process-ready-v1", "display": ":201",
                     "service_pid": 23456, "service_start_ticks": 987,
                     "owner_id": "owner-a", "receipt_path": str(receipt_path)}
            with self.assertRaisesRegex(ValueError, "up_batch keys"):
                read_owner_state_ledger(root, [ready])

    def test_ledger_accepts_actual_backend_event_envelope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            owner = root / "input-owner-process"
            owner.mkdir()
            ready = {"event": "input_owner_process_ready",
                     "schema": "input-owner-process-ready-v1", "display": ":201",
                     "service_pid": 23456, "service_start_ticks": 987,
                     "owner_id": "owner-a",
                     "receipt_path": str(owner / "input-owner-recovery-v1.json")}
            header = {"schema": "input-owner-state-ledger-v1", "record_type": "header",
                      "display": ":201", "service_pid": 23456,
                      "service_start_ticks": 987, "owner_id": "owner-a"}
            (owner / "input-owner-state-v1.jsonl").write_text(json.dumps(header) + "\n")
            state = read_owner_state_ledger(root, [{"type": "backend_event", "event": ready}])
            self.assertEqual(state["header"]["owner_id"], "owner-a")

    def test_rejects_receipt_path_outside_session_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events = [{"event": "input_owner_process_ready",
                       "schema": "input-owner-process-ready-v1",
                       "owner_id": "owner-a", "service_pid": 23456,
                       "service_start_ticks": 987,
                       "display": ":201", "receipt_path": str(root / "elsewhere.json")}]
            with self.assertRaisesRegex(RuntimeError, "outside session runtime"):
                verify_owner_process_recovery(root, events)

    def test_rejects_live_owner_even_with_valid_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "input-owner-process" / "input-owner-recovery-v1.json"
            target.parent.mkdir()
            target.write_text(json.dumps(receipt(":201", 23456, "owner-a")))
            events = [{"event": "input_owner_process_ready",
                       "schema": "input-owner-process-ready-v1",
                       "owner_id": "owner-a", "service_pid": 23456,
                       "service_start_ticks": 987,
                       "display": ":201", "receipt_path": str(target)}]
            now = [0.0]
            def clock():
                value = now[0]
                now[0] += .1
                return value
            with self.assertRaises(TimeoutError):
                with patch("doom_controller_failure_cleanup_v1._service_process_is_gone",
                           return_value=False):
                    verify_owner_process_recovery(
                        root, events, timeout=.5, clock=clock,
                        sleep=lambda _: None, kill=lambda *_: None)


if __name__ == "__main__":
    unittest.main()
