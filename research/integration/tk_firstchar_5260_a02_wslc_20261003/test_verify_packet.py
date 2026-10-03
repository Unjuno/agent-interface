import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).with_name("verify_packet.py")


class PacketCustodyTests(unittest.TestCase):
    def module(self):
        self.assertTrue(MODULE.is_file(), "retained custody verifier is missing")
        spec = importlib.util.spec_from_file_location("packet_verifier", MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, root):
        app = {"pid": 7, "saved_text": "hxy", "first_visual": {"observed_ns": 9}}
        ready = {"geometry": {"target_width": 20}}
        for name, value in [("app_result.json", app), ("ready.json", ready),
                            ("first_visual.json", app["first_visual"])]:
            (root / name).write_text(json.dumps(value), encoding="utf-8")
        return {"app": app, "app_pid": 7, "app_stdout": json.dumps(app),
                "ready": ready}

    def test_literal_custody_is_accepted(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            self.assertEqual(module.row_custody_errors(root, self.fixture(root)), [])

    def test_altered_app_file_is_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            row = self.fixture(root)
            (root / "app_result.json").write_text('{"saved_text":"xy"}', encoding="utf-8")
            self.assertIn("app_result_binding", module.row_custody_errors(root, row))

    def test_altered_stdout_is_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            row = self.fixture(root)
            row["app_stdout"] = "{}"
            self.assertIn("app_stdout_binding", module.row_custody_errors(root, row))

    def test_altered_ready_and_visual_files_are_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            row = self.fixture(root)
            (root / "ready.json").write_text("{}", encoding="utf-8")
            (root / "first_visual.json").write_text("{}", encoding="utf-8")
            errors = module.row_custody_errors(root, row)
            self.assertIn("ready_binding", errors)
            self.assertIn("first_visual_binding", errors)

    def test_wrong_app_pid_is_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            row = self.fixture(root)
            row["app_pid"] = 99
            self.assertIn("app_pid_binding", module.row_custody_errors(root, row))

    def test_manifest_rejects_wrong_hash_and_escape_path(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "empty").write_bytes(b"")
            empty_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            self.assertEqual(module.manifest_errors(root, [empty_hash + "  empty"]), [])
            self.assertTrue(module.manifest_errors(root, ["0" * 64 + "  empty"]))
            self.assertIn("unsafe_manifest_path", module.manifest_errors(root,
                [empty_hash + "  ../escape"]))

    def test_stop_packaging_cannot_hide_other_custody_errors(self):
        module = self.module()
        self.assertTrue(hasattr(module, "expected_readiness_stop"),
                        "explicit STOP packet qualification is missing")
        expected = [f"row_{i}:ready_binding" for i in range(96)]
        self.assertTrue(module.expected_readiness_stop(expected))
        self.assertFalse(module.expected_readiness_stop([]))
        self.assertFalse(module.expected_readiness_stop(expected + ["row_0:app_result_binding"]))
        self.assertFalse(module.expected_readiness_stop(expected[:-1]))


if __name__ == "__main__":
    unittest.main()
