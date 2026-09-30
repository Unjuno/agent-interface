import unittest

from contract import evaluate


class ConformanceTests(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "initial": "READY",
            "transitions": [
                {
                    "from": "READY",
                    "input": {"type": "OBSERVE"},
                    "to": "FRESH",
                    "allowed_outputs": [
                        {"type": "OBSERVED", "generation": 1, "target": "A"}
                    ],
                },
                {
                    "from": "READY",
                    "input": {"type": "ADMIT", "target": "A"},
                    "to": "READY",
                    "allowed_outputs": [{"type": "REFUSED", "reason": "NO_FRESH_EVIDENCE"}],
                },
                {
                    "from": "FRESH",
                    "input": {"type": "ADMIT", "target": "A"},
                    "to": "ADMITTED",
                    "allowed_outputs": [{"type": "ADMITTED", "target": "A"}],
                },
            ],
        }

    def test_hidden_internal_transitions_do_not_break_conformance(self):
        trace = [
            {
                "input": {"type": "OBSERVE"},
                "outputs": [{"type": "OBSERVED", "generation": 1, "target": "A"}],
                "internal": ["BATCH_FLUSH", "RETRY_CACHE_READ"],
            },
            {"input": {"type": "ADMIT", "target": "A"},
             "outputs": [{"type": "ADMITTED", "target": "A"}], "internal": []},
        ]
        self.assertEqual(evaluate(self.spec, trace)["status"], "CONFORMANT")

    def test_missing_output_is_unknown_not_explicit_quiescence(self):
        trace = [{"input": {"type": "OBSERVE"}, "outputs": [], "internal": []}]
        result = evaluate(self.spec, trace)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "MISSING_OUTPUT_NOT_QUIESCENCE")

    def test_explicit_quiescence_label_is_distinct_from_missing_output(self):
        spec = {
            "initial": "PENDING",
            "tra