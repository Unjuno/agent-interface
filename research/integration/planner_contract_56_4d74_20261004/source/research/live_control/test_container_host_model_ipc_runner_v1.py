from pathlib import Path
import json
import os
import stat
import tempfile
import unittest
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import container_host_model_ipc_runner_v1 as runner


class ContainerHostIpcContractTest(unittest.TestCase):
    def test_runner_is_fail_closed_and_shared_volume_bound(self):
        source = Path(__file__).with_name("container_host_model_ipc_runner_v1.py").read_text()
        self.assertIn("HOST_MODEL_IPC_DIR", source)
        self.assertIn('"authority_granted": False', source)
        self.assertIn("response timeout", source)
        self.assertIn('"started_ns": started_ns', source)
        self.assertIn('"exited_ns": exited_ns', source)

    def test_runner_has_no_direct_input_api(self):
        source = Path(__file__).with_name("container_host_model_ipc_runner_v1.py").read_text()
        self.assertNotIn("dispatch_golden_v3", source)
        self.assertNotIn("pointer_button", source)
        self.assertNotIn("input.text", source)

    @unittest.skipUnless(hasattr(os, "getuid") and hasattr(os, "getgid"),
                         "owner-only IPC test requires POSIX uid/gid")
    def test_atomic_request_applies_host_owner_and_retains_private_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "request.json"
            owner = (os.getuid(), os.getgid())
            runner.atomic_json_write(path, {"authority_granted": False}, owner=owner)
            metadata = path.stat()
            self.assertEqual((metadata.st_uid, metadata.st_gid), owner)
            self.assertEqual(stat.S_IMODE(metadata.st_mode), 0o600)
            self.assertFalse(list(Path(temp).glob("request.json.*.tmp")))
            self.assertFalse(json.loads(path.read_text())["authority_granted"])

    def test_ipc_owner_environment_requires_uid_and_gid_together(self):
        with patch.dict(os.environ, {
                "HOST_MODEL_IPC_OWNER_UID": "1002",
                "HOST_MODEL_IPC_OWNER_GID": "1002"}, clear=False):
            self.assertEqual(runner.ipc_owner_from_environment(), (1002, 1002))
        with patch.dict(os.environ, {"HOST_MODEL_IPC_OWNER_UID": "1002"}, clear=False):
            os.environ.pop("HOST_MODEL_IPC_OWNER_GID", None)
            with self.assertRaisesRegex(ValueError, "must be set together"):
                runner.ipc_owner_from_environment()


if __name__ == "__main__":
    unittest.main()
