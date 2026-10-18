import unittest

from candidate import classify


def case(case_id, **overrides):
    value = {
        "id": case_id,
        "worlds": [
            {
                "value": "A",
                "other": "untouched",
                "hidden": "h0",
                "callback_count": 0,
                "accepted": False,
                "can_update": True,
            }
        ],
        "view_fields": ["value"],
        "semantic_fields": ["value"],
        "requested_view": {"value": "B"},
        "operation": {
            "mode": "set",
            "target": "value",
            "declared_total": True,
            "declared_idempotent": True,
            "declared_side_effect_free": True,
            "declared_last_write_wins": True,
        },
        "observed_epoch": 4,
        "current_epoch": 4,
        "completion": "complete",
    }
    value.update(overrides)
    return value


class LensLawCandidateTests(unittest.TestCase):
    def test_valid_set_satisfies_all_three_scoped_laws(self):
        result = classify(case("valid-set"))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["laws"],
            {"get_put": True, "put_get": True, "put_put": True},
        )

    def test_benign_hidden_state_outside_equivalence_is_preserved(self):
        result = classify(
            case(
                "benign-hidden",
                semantic_fields=["value"],
                worlds=[{
                    "value": "A",
                    "other": "untouched",
                    "hidden": "h0",
                    "callback_count": 0,
                    "accepted": False,
                    "can_update": True,
                }],
            )
        )
        self.assertEqual(result["status"], "PASS")

    def test_wrong_field_target_violates_put_get(self):
        result = classify(
            case("wrong-field", operation={
                "mode": "wrong_field",
                "target": "other",
                "input_field": "value",
                "declared_total": True,
                "declared_idempotent": True,
                "declared_side_effect_free": True,
                "declared_last_write_wins": True,
            })
        )
        self.assertEqual(result["status"], "VIOLATION")
        self.assertFalse(result["laws"]["put_get"])

    def test_ignored_update_violates_put_get(self):
        result = classify(
            case("ignored", operation={
                "mode": "ignored",
                "target": "value",
                "declared_total": True,
                "declared_idempotent": True,
                "declared_side_effect_free": True,
                "declared_last_write_wins": True,
            })
        )
        self.assertEqual(result["status"], "VIOLATION")
        self.assertFalse(result["laws"]["put_get"])

    def test_duplicate_callback_is_visible_to_get_put_even_if_final_label_matches(self):
        result = classify(
            case(
                "duplicate-callback",
                semantic_fields=["value", "callback_count"],
                operation={
                    "mode": "duplicate_callback",
                    "target": "value",
                    "declared_total": True,
                    "declared_idempotent": True,
                    "declared_side_effect_free": True,
                    "declared_last_write_wins": True,
                },
            )
        )
        self.assertEqual(result["status"], "VIOLATION")
        self.assertFalse(result["laws"]["get_put"])
        self.assertTrue(result["baselines"]["final_label_only"])

    def test_first_write_wins_is_detected_by_put_put_after_single_write_looks_correct(self):
        result = classify(
            case("first-write-wins", operation={
                "mode": "first_write_wins",
                "target": "value",
                "declared_total": True,
                "declared_idempotent": True,
                "declared_side_effect_free": True,
                "declared_last_write_wins": True,
            })
        )
        self.assertEqual(result["status"], "VIOLATION")
        self.assertTrue(result["laws"]["put_get"])
        self.assertFalse(result["laws"]["put_put"])
        self.assertTrue(result["baselines"]["final_label_only"])

    def test_same_view_with_different_update_domains_abstains(self):
        result = classify(
            case(
                "lossy-projection",
                worlds=[
                    {"value": "A", "other": "x", "hidden": "enabled", "callback_count": 0, "accepted": False, "can_update": True},
                    {"value": "A", "other": "y", "hidden": "disabled", "callback_count": 0, "accepted": False, "can_update": False},
                ],
                operation={
                    "mode": "conditional_set",
                    "target": "value",
                    "declared_total": True,
                    "declared_idempotent": True,
                    "declared_side_effect_free": True,
                    "declared_last_write_wins": True,
                },
            )
        )
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "AMBIGUOUS_APPLICABILITY")

    def test_stale_view_abstains(self):
        result = classify(case("stale", current_epoch=5))
        self.assertEqual((result["status"], result["reason"]), ("UNKNOWN", "STALE_EPOCH"))

    def test_partial_operation_is_not_applicable(self):
        operation = case("partial")["operation"]
        operation["declared_total"] = False
        result = classify(case("partial", operation=operation))
        self.assertEqual(
            (result["status"], result["reason"]),
            ("NOT_APPLICABLE", "PARTIAL_DOMAIN"),
        )

    def test_pending_async_completion_abstains(self):
        result = classify(case("pending", completion="pending"))
        self.assertEqual(
            (result["status"], result["reason"]),
            ("UNKNOWN", "COMPLETION_PENDING"),
        )

    def test_completed_async_update_is_evaluated(self):
        result = classify(case("completed", completion="complete"))
        self.assertEqual(result["status"], "PASS")

    def test_non_idempotent_operation_is_not_applicable(self):
        operation = case("counter")["operation"]
        operation["mode"] = "increment"
        operation["declared_idempotent"] = False
        result = classify(case("counter", operation=operation))
        self.assertEqual(
            (result["status"], result["reason"]),
            ("NOT_APPLICABLE", "NON_IDEMPOTENT"),
        )


if __name__ == "__main__":
    unittest.main()
