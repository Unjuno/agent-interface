"""Contracts for the opt-in outer process-owner recovery gate."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from doom_controller_failure_cleanup_v1 import verify_owner_process_recovery


def receipt(display, pid, owner):
    release = {"event": "owner_release", "reason": "close", "verified": True,
               "keys_down": [], "buttons_down": [], "keys_unknown": [],
               "key_state_errors": []}
    return {"schema": "input-owner-recovery-v1", "display": display,
            "service_pid": pid, "owner_id": owner, "receipt_fsynced": True,
            "owner_thread_stopped": True, "close_error": None,
            "release_records": [release]}


class OwnerRecoveryGateTests(unittest.TestCase):
    def test_requires_matching_durable_receipt_and_dead_service(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "input-owner-process" / "input-owner-recovery-v1.json"
            target.parent.mkdir()
            target.write_text(json.dumps(receipt(":201", 23456, "owner-a")))
            events = [{"event": "input_owner_process_ready",
                       "schema": "input-owner-process-ready-v1",
                       "owner_id": "owner-a", "service_pid": 23456,
                       "display": ":201", "receipt_path": str(target)}]
            def dead(pid, signal):
                self.assertEqual((pid, signal), (23456, 0))
                raise ProcessLookupError
            result = verify_owner_process_recovery(
                root, events, kill=dead, sleep=lambda _: None)
            self.assertEqual(result["owner_id"], "owner-a")

    def test_rejects_receipt_path_outside_session_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events = [{"event": "input_owner_process_ready",
                       "schema": "input-owner-process-ready-v1",
                       "owner_id": "owner-a", "service_pid": 23456,
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
                       "display": ":201", "receipt_path": str(target)}]
            now = [0.0]
            def clock():
                value = now[0]
                now[0] += .1
                return value
            with self.assertRaises(TimeoutError):
                verify_owner_process_recovery(
                    root, events, timeout=.5, clock=clock,
                    sleep=lambda _: None, kill=lambda *_: None)


if __name__ == "__main__":
    unittest.main()
