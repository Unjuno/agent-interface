import unittest

from research.live_control.adaptive_acquisition_caller_v2 import (
    LOCAL_EXECUTION_YIELD_REASONS,
    run,
)
from runtime.core_v1.compiled_gui import YIELD_REASONS


class AdaptiveAcquisitionYieldVocabularyTests(unittest.TestCase):
    def test_compiled_runtime_refusal_is_preserved_by_caller_contract(self):
        self.assertLessEqual(YIELD_REASONS, LOCAL_EXECUTION_YIELD_REASONS)
        refusal = {
            "status": "safe_yield",
            "reason": "execution_refused",
            "completed_actions": 0,
        }
        usage = {
            "input_tokens": 10,
            "cached_input_tokens": 0,
            "cache_write_input_tokens": 0,
            "output_tokens": 2,
            "reasoning_output_tokens": 1,
        }

        def model_result(call_id, output):
            return {
                "call_id": call_id,
                "output": output,
                "usage": usage,
                "requested_model": "gpt-5.6-luna",
                "requested_effort": "low",
                "cost": None,
            }

        effect_calls = []
        result = run(
            {
                "target": "test target",
                "route": "cold",
                "coarse_origin": "model_produced",
                "provided_coarse": None,
                "cached_target": None,
                "repair_on": [],
                "session_id": "execution-refusal-composition",
            },
            {
                "observe_source": lambda _payload: {"frame": "fresh"},
                "coarse_model": lambda _payload: model_result(
                    "coarse-1", {"status": "candidate", "point": [1, 1]}),
                "acquire_anchor": lambda _payload: {"anchor": "fresh"},
                "anchor_model": lambda _payload: model_result(
                    "anchor-1", {
                        "status": "target_reference",
                        "target": {"point": [1, 1], "receipt": "target"},
                    }),
                "final_revalidate": lambda _payload: {"status": "revalidated"},
                "execute": lambda _payload: refusal,
                "verify_effect": lambda _payload: effect_calls.append(_payload),
            },
        )
        self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE")
        self.assertEqual(result["reason"], "execution_refused")
        self.assertEqual(result["delivery"], "not_attempted")
        self.assertEqual(result["execution_progress"], refusal)
        self.assertEqual(result["input_authority"], "none")
        self.assertEqual(result["accounting"]["attempted_calls"], 2)
        self.assertEqual(result["accounting"]["usage_totals"]["input_tokens"], 20)
        self.assertEqual(effect_calls, [])


if __name__ == "__main__":
    unittest.main()
