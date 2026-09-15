import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from research.live_control.semantic_repair_model_v2 import classify, invoke


ROOT = Path(__file__).resolve().parent


class TypedSemanticInvocationTests(unittest.TestCase):
    def test_completed_historical_call(self):
        result = classify(ROOT / "results/compiled-gui-interface-live-05/2-positive/grounding-model")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["completed_turns"], 1)
        self.assertGreater(result["usage"]["input_tokens"], 0)
        self.assertFalse(result["grants_input_authority"])

    def test_retained_capacity_call_is_typed_deferral(self):
        result = classify(ROOT / "results/matched-semantic-repair-live-01/arm-01-local/initial-model")
        self.assertEqual(result["status"], "DEFERRED_UPSTREAM")
        self.assertEqual(result["reason"], "capacity_unavailable")
        self.assertEqual(result["model_threads_started"], 1)
        self.assertEqual(result["completed_turns"], 0)
        self.assertIsNone(result["usage"])
        self.assertIsNone(result["result"])
        self.assertFalse(result["grants_semantic_authority"])
        self.assertFalse(result["grants_input_authority"])

    def test_zero_exit_without_validated_output_fails_without_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "process.json").write_text(json.dumps({
                "exit_code": 0, "requested_model": "gpt-5.6-luna",
                "requested_effort": "low", "started_ns": 1,
                "exited_ns": 2}), encoding="utf-8")
            (root / "events.jsonl").write_text("", encoding="utf-8")
            result = classify(root)
        self.assertEqual(result["status"], "FAILED_OUTPUT")
        self.assertEqual(result["reason"], "invalid_model_output")
        self.assertIsNone(result["result"])
        self.assertFalse(result["grants_input_authority"])

    def test_launch_failure_is_typed_without_retry_or_authority(self):
        with patch("research.live_control.semantic_repair_model_v2.v1.call",
                   side_effect=OSError("launch unavailable")) as call:
            result = invoke("unused", "prompt", "image", "workspace")
        call.assert_called_once()
        self.assertEqual(result["status"], "FAILED_UPSTREAM")
        self.assertEqual(result["reason"], "model_process_failed")
        self.assertEqual(result["visible_images_submitted"], 1)
        self.assertFalse(result["grants_input_authority"])


if __name__ == "__main__":
    unittest.main()
