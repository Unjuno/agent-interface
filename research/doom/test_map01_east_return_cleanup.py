"""Verify failure cleanup only from bound owner-service receipts."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from map01_east_return_audit import validate_failure_cleanup


class FailureCleanupTests(unittest.TestCase):
    def test_verified_receipt_requires_exit_eof_and_bound_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); service_dir = root / "input-owner-service"; service_dir.mkdir()
            inner = {"pid": 42, "parent_pid": 10, "owner_id": "owner", "service_id": "svc", "display": ":1"}
            startup = {"spawn_pid": 42, "startup": inner}
            outer = json.dumps(startup).encode(); (root / "session-owner-service-startup.json").write_bytes(outer)
            inner_bytes = json.dumps(inner).encode(); (service_dir / "startup.json").write_bytes(inner_bytes)
            identity = dict(inner, supervisor_pid=10)
            close = {"event":"owner_release", "reason":"close", "verified":True, "keys_down":[], "buttons_down":[], "keys_unknown":[], "key_state_errors":[]}
            core = {"verified":True, "service_id":"svc", "owner_thread_stopped":True, "release_records":[close]}
            digest = hashlib.sha256(inner_bytes).hexdigest()
            finish = {"verified":True, "owner_thread_stopped":True, "context_exit_success":True, "identity":identity, "startup_sha256":digest}
            recovery = {"verified":True, "identity":identity, "startup_sha256":digest, "core":core}
            report = {"service_id":"svc", "spawn_pid":42, "exit_code":0, "verified":True, "receipt_verified":True, "receipt_error":None, "process_alive":False, "finish":finish, "recovery":recovery}
            service = {"service_id":"svc", "verified":True, "startup_sha256":hashlib.sha256(outer).hexdigest(), "adapter":{"owner_id":"owner", "service_id":"svc", "errors":[], "obligation":None, "verified":True, "ordinary_close":core, "service_report":report}}
            (root / "session-owner-service-close.json").write_text(json.dumps(service))
            (root / "owner-events.json").write_text(json.dumps([close]))
            saved = {"receipt_verified":True, "finish":finish, "recovery":recovery}
            with patch("input_owner_process_v3.read_service_receipt", return_value=saved):
                self.assertIsNone(validate_failure_cleanup(root, process_exited=True, drain_eof=True))
                for exited, eof in ((False,True),(True,False)):
                    with self.assertRaises(ValueError): validate_failure_cleanup(root, process_exited=exited, drain_eof=eof)
                (root / "owner-events.json").write_text("[]")
                with self.assertRaises(ValueError): validate_failure_cleanup(root, process_exited=True, drain_eof=True)
                (root / "owner-events.json").write_text(json.dumps([close]))
                service["adapter"]["obligation"] = {"state":"unknown"}
                (root / "session-owner-service-close.json").write_text(json.dumps(service))
                with self.assertRaises(ValueError): validate_failure_cleanup(root, process_exited=True, drain_eof=True)
                service["adapter"]["obligation"] = None
                close["keys_down"] = ["Up"]
                (root / "owner-events.json").write_text(json.dumps([close]))
                (root / "session-owner-service-close.json").write_text(json.dumps(service))
                with self.assertRaises(ValueError): validate_failure_cleanup(root, process_exited=True, drain_eof=True)

if __name__ == "__main__": unittest.main()
