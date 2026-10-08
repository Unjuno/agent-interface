"""Explicit literal predicates compose with the existing real guarded adapter."""
import unittest
from runtime.guarded_x11_v1.compiled import run
from runtime.guarded_x11_v1.test_compiled import Bridge, spec, bindings


class GuardedLiteralUnknownTests(unittest.TestCase):
    def run_literal(self, verdict):
        bridge = Bridge()
        plan = spec()
        plan["actions"]["enter"]["expected_effect"] = {"phase": "unknown"}
        plan["method"]["states"]["filled"]["branches"][0]["when"] = {"phase": "unknown"}
        calls = []

        def perceive(native, image):
            return {"phase": "unknown" if bridge.phase == 1 else bridge.phase,
                    "present": True}

        def verify(payload, native, image):
            calls.append(payload)
            status = verdict if len(calls) == 1 else "succeeded"
            return {"status": status, "evidence_ref": "independent-literal-witness"
                    if status == "succeeded" else None}

        result = run(bridge, plan, bindings(), perceive=perceive, verify_effect=verify)
        return bridge, result, calls

    def test_literal_match_composes_with_guarded_verifier_and_completion(self):
        bridge, result, calls = self.run_literal("succeeded")
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["completed_transitions"], 2)
        self.assertEqual(len(bridge.inputs), 2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["expected_effect"], {"phase": "unknown"})
        effects = [value for name, value in bridge.saved if name.endswith("-effect.json")]
        self.assertEqual(len(effects), 2)
        self.assertEqual(effects[0]["result"]["evidence_ref"], "independent-literal-witness")

    def test_literal_match_keeps_guarded_negative_verdict_and_completed_prefix(self):
        for verdict in ("failed", "unavailable"):
            with self.subTest(verdict=verdict):
                bridge, result, calls = self.run_literal(verdict)
                self.assertEqual((result["outcome"], result["reason"]), ("SAFE_YIELD", "effect_" + verdict))
                self.assertEqual(result["completed_transitions"], 1)
                self.assertEqual(result["pending_effect"]["expected_effect"], {"phase": "unknown"})
                self.assertEqual(len(bridge.inputs), 1)
                self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
