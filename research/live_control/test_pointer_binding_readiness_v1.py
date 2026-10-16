import unittest

from research.live_control.pointer_binding_readiness_v1 import evaluate


class PointerBindingReadinessTests(unittest.TestCase):
    def observation(self):
        binding = {"focus": 4, "surface": 3, "geometry": [0, 19, 1280, 781]}
        return {"id": "o", "sequence": 3, "capture_ns": 100,
            "pointer_binding": binding, "pointer_context_before": dict(binding),
            "pointer_context_after": dict(binding), "focus_samples_match": True}

    def test_coherent_binding_is_ready_without_authority(self):
        result = evaluate(self.observation(), 110)
        self.assertEqual(result["status"], "READY")
        self.assertTrue(result["may_submit_pointer_input"])
        self.assertFalse(result["grants_input_authority"])

    def test_focus_transition_waits(self):
        observation = self.observation()
        observation["pointer_binding"] = None
        observation["pointer_context_before"] = {"focus": 4, "surface": None,
                                                   "geometry": None}
        result = evaluate(observation, 110)
        self.assertEqual(result["status"], "WAIT_FOR_COHERENT_BINDING")
        self.assertFalse(result["may_submit_pointer_input"])


if __name__ == "__main__": unittest.main()
