import importlib
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class V17BindingTests(unittest.TestCase):
    def load_v17(self):
        try:
            return importlib.import_module("session_map01_v17")
        except ModuleNotFoundError as error:
            self.fail(f"expected opt-in V17 wrapper is not implemented: {error}")

    def test_v17_binds_clock_v2_during_v16_main_and_restores_after_failure(self):
        v17 = self.load_v17()
        original = v17.previous.AcknowledgedSampler
        original_proxy = v17.previous.ObservedGameProxy
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "sources.json").write_text('{"existing":"sha"}\n', encoding="utf-8")

            def run_v16():
                self.assertIs(v17.previous.AcknowledgedSampler,
                              v17.AcknowledgedSamplerClockV2)
                self.assertIs(v17.previous.ObservedGameProxy,
                              v17.ObservedGameProxyClockV2)
                raise OSError("injected V16 failure")

            with patch.object(v17.previous.previous, "_option", return_value=str(out)), \
                 patch.object(v17.previous, "main", side_effect=run_v16):
                with self.assertRaisesRegex(OSError, "injected V16 failure"):
                    v17.main()

            self.assertIs(v17.previous.AcknowledgedSampler, original)
            self.assertIs(v17.previous.ObservedGameProxy, original_proxy)
            sources = json.loads((out / "sources.json").read_text(encoding="utf-8"))
            self.assertEqual(sources["existing"], "sha")
            self.assertIn("doom/session_map01_v17.py", sources)
            self.assertIn(
                "doom/acknowledged_scorer_status_clock_v2_59_20261004/acknowledged_scorer_clock_v2.py",
                sources)
            for key in (
                "doom/session_map01_v17.py",
                "doom/acknowledged_scorer_status_clock_v2_59_20261004/acknowledged_scorer_clock_v2.py",
            ):
                path = v17.RESEARCH / key
                self.assertEqual(sources[key], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_v17_returns_successful_v16_result(self):
        v17 = self.load_v17()
        original = v17.previous.AcknowledgedSampler
        original_proxy = v17.previous.ObservedGameProxy
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "sources.json").write_text("{}\n", encoding="utf-8")
            with patch.object(v17.previous.previous, "_option", return_value=str(out)), \
                 patch.object(v17.previous, "main", return_value="session-result"):
                self.assertEqual(v17.main(), "session-result")
            self.assertIs(v17.previous.AcknowledgedSampler, original)
            self.assertIs(v17.previous.ObservedGameProxy, original_proxy)


if __name__ == "__main__":
    unittest.main(verbosity=2)
