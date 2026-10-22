import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from recorded_integrated_efficiency_model_call_v1 import build_model_provider_call
from ledger import summarize
from provider_attempt_recorder import ProviderAttemptRecorder


class RecordedModelCallUsageTests(unittest.TestCase):
    def test_provider_bridge_preserves_detailed_turn_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "target.png"
            image.write_bytes(b"synthetic image")
            model_root = root / "call"
            expected = {
                "status": "reported",
                "input_tokens": 101,
                "output_tokens": 19,
                "cached_input_tokens": 70,
                "cache_write_input_tokens": 5,
                "reasoning_output_tokens": 8,
            }

            def model_call(call_root, prompt, call_image, contract, workspace):
                events = call_root / "model" / "events.jsonl"
                events.parent.mkdir(parents=True)
                events.write_bytes(
                    b'{"type":"item.completed","item":{"type":"agent_message",'
                    b'"text":"{}"}}\n')
                return {"usage": {key: value for key, value in expected.items()
                                  if key != "status"}}

            request, provider_call = build_model_provider_call(
                model_call=model_call, root=model_root, prompt="ground target",
                image=image, contract="compiled", workspace=root)
            recorder = ProviderAttemptRecorder(root / "ledger")
            asyncio.run(recorder.invoke_async(
                "attempt-01", request, provider_call))

            event = recorder.reconcile()["events"][0]
            self.assertEqual(event["usage"], expected)
            summary = summarize([{**event, "seq": 1}])
            self.assertEqual(summary["detailed_usage_status"], "incomplete")
            self.assertEqual(summary["cached_input_tokens"], 70)
            self.assertEqual(summary["cache_write_input_tokens"], 5)
            self.assertEqual(summary["reasoning_output_tokens"], 8)

    def test_detailed_usage_survives_when_primary_counts_are_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "target.png"
            image.write_bytes(b"synthetic image")
            expected = {
                "status": "partial",
                "input_tokens": None,
                "output_tokens": None,
                "cached_input_tokens": 7,
                "reasoning_output_tokens": 3,
            }

            def model_call(call_root, _prompt, _image, _contract, _workspace):
                events = call_root / "model" / "events.jsonl"
                events.parent.mkdir(parents=True)
                events.write_bytes(b'{"type":"turn.completed"}\n')
                return {"usage": {"cached_input_tokens": 7,
                                   "reasoning_output_tokens": 3}}

            request, provider_call = build_model_provider_call(
                model_call=model_call, root=root / "call", prompt="ground target",
                image=image, contract="compiled", workspace=root)
            recorder = ProviderAttemptRecorder(root / "ledger")
            asyncio.run(recorder.invoke_async(
                "attempt-02", request, provider_call))

            event = recorder.reconcile()["events"][0]
            self.assertEqual(event["usage"], expected)


if __name__ == "__main__":
    unittest.main()
