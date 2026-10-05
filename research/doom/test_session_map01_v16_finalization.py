import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import session_map01_v16 as candidate

class FinalizationTests(unittest.TestCase):
    def exercise(self, session_error=None, malformed=False):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            sources = out / "sources.json"
            sources.write_text("{bad" if malformed else "{}", encoding="utf-8")
            previous = candidate.previous
            old_sample, old_proxy = previous._coherent_progress_sample, previous._GameProxy
            def run():
                if session_error is not None:
                    raise session_error
                return 37
            with patch.object(previous, "_option", return_value=tmp), patch.object(previous, "main", side_effect=run):
                try:
                    result = candidate.main()
                    return result, json.loads(sources.read_text())
                finally:
                    self.assertIs(previous._coherent_progress_sample, old_sample)
                    self.assertIs(previous._GameProxy, old_proxy)

    def test_success_preserves_result_and_records_sources(self):
        value, sources = self.exercise()
        self.assertEqual(value, 37)
        for key in ("doom/session_map01_v16.py", "doom/acknowledged_scorer_v1.py"):
            self.assertEqual(len(sources[key]), 64)

    def test_session_failure_preserves_same_exception(self):
        error = RuntimeError("session sentinel")
        with self.assertRaises(RuntimeError) as caught:
            self.exercise(error)
        self.assertIs(caught.exception, error)

    def test_provenance_only_failure_propagates(self):
        with self.assertRaises(json.JSONDecodeError):
            self.exercise(malformed=True)

    def test_dual_failure_preserves_both(self):
        error = RuntimeError("session sentinel")
        with self.assertRaises(BaseExceptionGroup) as caught:
            self.exercise(error, True)
        self.assertIs(caught.exception.exceptions[0], error)
        self.assertIsInstance(caught.exception.exceptions[1], json.JSONDecodeError)

    def test_interrupt_and_provenance_failure_preserves_both(self):
        error = KeyboardInterrupt("interrupt sentinel")
        with self.assertRaises(BaseExceptionGroup) as caught:
            self.exercise(error, True)
        self.assertIs(caught.exception.exceptions[0], error)
        self.assertIsInstance(caught.exception.exceptions[1], json.JSONDecodeError)

if __name__ == "__main__":
    unittest.main()
