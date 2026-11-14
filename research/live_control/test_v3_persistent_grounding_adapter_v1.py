"""Contract tests for the App Server to adaptive-v3 model adapter."""
import unittest

from adaptive_acquisition_caller_v3 import ModelFailure
from integrated_efficiency_app_server_model_v1 import GroundingCallError
from v3_persistent_grounding_adapter_v1 import V3PersistentGroundingAdapter


USAGE = {"input_tokens": 123, "cached_input_tokens": 23,
         "cache_write_input_tokens": 0, "output_tokens": 12,
         "reasoning_output_tokens": 4}


class FakeModel:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, 0

    def call(self, *_args):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class V3PersistentGroundingAdapterTests(unittest.TestCase):
    def test_success_maps_provider_identity_usage_images_and_wait(self):
        model = FakeModel({"grounding": {"field_point": [1, 2]},
            "call_id": "turn-1", "thread_id": "thread-1", "usage": USAGE,
            "requested_model": "model-x", "requested_effort": "low",
            "runner_ns": 987, "cost": None})
        adapter = V3PersistentGroundingAdapter(model)
        result = adapter("root", "prompt", "image", "compiled", "workspace")
        self.assertEqual(result, {"call_id": "turn-1", "thread_id": "thread-1",
            "output": {"status": "target_reference",
                       "target": {"field_point": [1, 2]}},
            "usage": USAGE, "requested_model": "model-x",
            "requested_effort": "low", "cost": None,
            "visible_images_submitted": 1, "wait_ns": 987})
        self.assertEqual(model.calls, 1)

    def test_provider_failure_preserves_observed_usage_and_identity(self):
        error = GroundingCallError(RuntimeError("turn failed"),
            call_id="turn-2", thread_id="thread-2", usage=USAGE,
            visible_images_submitted=1, wait_ns=654,
            requested_model="model-x", requested_effort="medium")
        model = FakeModel(error=error)
        adapter = V3PersistentGroundingAdapter(model)
        with self.assertRaises(ModelFailure) as caught:
            adapter("root", "prompt", "image", "compiled", "workspace")
        failure = caught.exception
        self.assertEqual(failure.call_id, "turn-2")
        self.assertEqual(failure.thread_id, "thread-2")
        self.assertEqual(failure.usage, USAGE)
        self.assertEqual(failure.visible_images_submitted, 1)
        self.assertEqual(failure.wait_ns, 654)
        self.assertEqual(failure.typed_status, "FAILED_UPSTREAM")
        self.assertEqual(model.calls, 1)

    def test_bad_output_projection_keeps_completed_call_accounting(self):
        model = FakeModel({"grounding": {}, "call_id": "turn-3",
            "thread_id": "thread-3", "usage": USAGE,
            "requested_model": "model-x", "requested_effort": "low",
            "runner_ns": 321, "cost": None})
        adapter = V3PersistentGroundingAdapter(model,
            output_projector=lambda _: None)
        with self.assertRaises(ModelFailure) as caught:
            adapter("root", "prompt", "image", "compiled", "workspace")
        self.assertEqual(caught.exception.typed_status, "FAILED_OUTPUT")
        self.assertEqual(caught.exception.usage, USAGE)
        self.assertEqual(caught.exception.call_id, "turn-3")


if __name__ == "__main__":
    unittest.main()
