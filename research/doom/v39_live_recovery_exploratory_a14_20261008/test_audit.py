import unittest

from audit import classify_protocol_deviation


class ProtocolDeviationTests(unittest.TestCase):
    def setUp(self):
        self.freeze = {
            "purpose": "identify startup stage; no planner turn or model call",
            "diagnostic_adapter": {"diagnostic_sha256": "expected-marker-source"},
        }
        self.adapter = {"file": "research/doom/session_map01_v12.py"}

    def test_matching_model_free_diagnostic_source_is_not_a_deviation(self):
        reasons, deviation, expected, actual = classify_protocol_deviation(
            self.freeze, self.adapter,
            {"doom/session_map01_v12.py": "expected-marker-source"}, 0,
        )
        self.assertFalse(deviation)
        self.assertEqual(reasons, {
            "planner_turns_when_forbidden": False,
            "declared_diagnostic_source_not_executed": False,
        })
        self.assertEqual((expected, actual), ("expected-marker-source", "expected-marker-source"))

    def test_unexpected_planner_turn_is_a_deviation(self):
        _, deviation, _, _ = classify_protocol_deviation(
            self.freeze, self.adapter,
            {"doom/session_map01_v12.py": "expected-marker-source"}, 1,
        )
        self.assertTrue(deviation)

    def test_wrong_or_missing_diagnostic_source_is_a_deviation_without_turns(self):
        for runtime_sources in (
            {"doom/session_map01_v12.py": "ordinary-source"},
            {},
        ):
            with self.subTest(runtime_sources=runtime_sources):
                reasons, deviation, expected, actual = classify_protocol_deviation(
                    self.freeze, self.adapter, runtime_sources, 0,
                )
                self.assertTrue(deviation)
                self.assertTrue(reasons["declared_diagnostic_source_not_executed"])
                self.assertEqual(expected, "expected-marker-source")
                self.assertEqual(actual, runtime_sources.get("doom/session_map01_v12.py"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
