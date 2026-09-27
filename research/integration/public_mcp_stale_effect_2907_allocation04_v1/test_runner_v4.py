import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("SOURCE_COMMIT", "construction-only")
os.environ.setdefault("EXPERIMENT_IMAGE_ID", "construction-only")

import runner_effect_v4 as runner


class AdapterTests(unittest.TestCase):
    def test_trace_binds_six_retained_reads_to_one_transport(self):
        trace = {"session_id": "session-x", "retained_reads": [
            {"source_label": f"label-{i}", "session_id": None} for i in range(6)]}
        result = runner.annotate_trace(trace, "transport-123")
        self.assertTrue(all(row["session_id"] == "session-x" for row in result["retained_reads"]))
        self.assertEqual(result["retained_transport"], {
            "scope": "single-public-stdio-client-session", "session_id": "session-x",
            "transport_token": "transport-123", "read_count": 6, "same_client_context": True})

    def test_effect_persist_requires_exact_marker(self):
        with patch.object(runner, "OUT") as out:
            out.__truediv__.return_value.write_bytes = unittest.mock.Mock()
            runner.persist_effect_from_xprop(["xprop", "-id", "42", "WM_NAME"],
                                              SimpleNamespace(stdout='"unrelated"'))
            out.__truediv__.return_value.write_bytes.assert_not_called()

    def test_effect_persist_records_unique_window(self):
        with patch.object(runner, "OUT") as out:
            target = SimpleNamespace(write_bytes=unittest.mock.Mock())
            out.__truediv__.return_value = target
            title = f'WM_NAME(UTF8_STRING) = "{runner.MARKER} - Chromium"'
            runner.persist_effect_from_xprop(["xprop", "-id", "42", "WM_NAME"],
                                              SimpleNamespace(stdout=title))
            target.write_bytes.assert_called_once()


if __name__ == "__main__":
    unittest.main()

