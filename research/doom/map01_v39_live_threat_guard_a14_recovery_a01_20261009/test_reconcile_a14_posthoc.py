import unittest

from reconcile_a14_posthoc import collect_action_health_rejections


def receipt(fingerprint, source, fresh, maximum):
    return {
        "status": "REJECTED_PREDICATE",
        "reason": "health_max_decrease_from_source_failed",
        "requires_new_decision": True,
        "contract": {
            "action_fingerprint": fingerprint,
            "source": {"signals": {"health": {"value": source}}},
        },
        "snapshot": {"signals": {"health": {"value": fresh}}},
        "checks": [{"signal_id": "health", "operator": "max_decrease_from_source",
                    "expected": maximum, "observed": fresh, "passed": False}],
    }


class ReconciliationTest(unittest.TestCase):
    def test_deduplicates_repeated_receipts_and_keeps_distinct_actions(self):
        first = receipt("a", 97, 85, 10)
        second = receipt("b", 85, 70, 8)
        report = {"decisions": [
            {"iteration": 1, "running_action_guard": {"invalidation": first,
                                                        "running_validity": {"invalidation": first}}},
            {"iteration": 2, "final_action_admission": {"action_validity": second}},
        ]}
        rows = collect_action_health_rejections(report)
        self.assertEqual([(r["decision_iteration"], r["source_health"], r["fresh_health"],
                           r["maximum_allowed_decrease"], r["outcome"]) for r in rows],
                         [(1, 97, 85, 10, "revoked_after_executor_acceptance"),
                          (2, 85, 70, 8, "rejected_before_executor_admission")])

    def test_conflicting_duplicate_fingerprint_fails_closed(self):
        report = {"decisions": [{"iteration": 1,
                                 "running_action_guard": {"invalidation": receipt("a", 97, 85, 10),
                                                          "running_validity": {"invalidation": receipt("a", 97, 80, 10)}}}]}
        with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
            collect_action_health_rejections(report)


if __name__ == "__main__":
    unittest.main()
