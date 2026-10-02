import unittest

from analyze import analyze_window


def observation(sequence, capture_ns, health, *, ready_ns=None, emit_ns=None, status="observed"):
    return {
        "event": "typed_observation",
        "sequence": sequence,
        "capture_ns": capture_ns,
        "typed_ready_ns": ready_ns if ready_ns is not None else capture_ns + 10,
        "emit_ns": emit_ns if emit_ns is not None else capture_ns + 20,
        "signals": {"health": {"status": status, "value": health}},
    }


def report(start=100, end=1_000, source_sequence=7, source_health=85):
    return {
        "decisions": [
            {
                "iteration": 2,
                "controller_model_started_ns": start,
                "controller_model_ended_ns": end,
                "final_action_admission": {
                    "action_validity": {
                        "contract": {
                            "source": {
                                "sequence": source_sequence,
                                "capture_ns": start - 50,
                                "signals": {
                                    "health": {"status": "observed", "value": source_health}
                                },
                            }
                        }
                    }
                },
            }
        ]
    }


class ContinuationGuardWindowTests(unittest.TestCase):
    def test_finds_first_fresh_below_source_health_during_model_wait(self):
        rows = [
            observation(7, 50, 85),
            observation(8, 120, 85),
            observation(9, 300, 82, ready_ns=315, emit_ns=320),
            observation(10, 900, 70),
        ]
        result = analyze_window(report(), rows)
        self.assertEqual(result["trigger"]["sequence"], 9)
        self.assertEqual(result["trigger"]["reason"], "health_below_source")
        self.assertEqual(result["remaining_after_emit_ns"], 680)

    def test_unavailable_fresh_health_invalidates_before_later_decline(self):
        rows = [
            observation(8, 120, None, status="unavailable"),
            observation(9, 300, 82),
        ]
        result = analyze_window(report(), rows)
        self.assertEqual(result["trigger"]["sequence"], 8)
        self.assertEqual(result["trigger"]["reason"], "health_unavailable")

    def test_stale_sequence_invalidates_before_health_comparison(self):
        rows = [observation(7, 120, 85)]
        result = analyze_window(report(), rows)
        self.assertEqual(result["trigger"]["reason"], "non_fresh_sequence")

    def test_no_rejection_observed_before_answer_is_not_a_pass(self):
        rows = [observation(8, 120, 85), observation(9, 900, 85)]
        result = analyze_window(report(), rows)
        self.assertEqual(result["trigger"], None)
        self.assertEqual(result["disposition"], "NO_GUARD_REJECTION_OBSERVED")


if __name__ == "__main__":
    unittest.main()
