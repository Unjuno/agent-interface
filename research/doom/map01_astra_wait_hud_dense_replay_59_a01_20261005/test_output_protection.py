from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PKG = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OutputProtectionTests(unittest.TestCase):
    def assert_refuses_existing_output(self, module_name: str, script: str) -> None:
        module = load_module(module_name, PKG / script)
        guard = getattr(module, "ensure_output_is_new", None)
        self.assertTrue(callable(guard), "script must expose its output preflight")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "retained.json"
            original = b'{"retained":true}\n'
            output.write_bytes(original)

            with self.assertRaises(FileExistsError):
                guard(output)

            self.assertEqual(output.read_bytes(), original)

    def test_candidate_refuses_existing_default_or_explicit_output(self) -> None:
        self.assert_refuses_existing_output("candidate_under_test", "run_candidate.py")

    def test_auditor_refuses_existing_default_or_explicit_output(self) -> None:
        self.assert_refuses_existing_output("auditor_under_test", "audit_independent.py")


if __name__ == "__main__":
    unittest.main()
