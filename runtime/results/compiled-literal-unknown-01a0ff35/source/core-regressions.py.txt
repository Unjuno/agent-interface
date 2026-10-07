"""An explicitly authored scalar value remains subject to effect verification."""
import copy
import unittest

from runtime.core_v1.test_compiled_gui import Driver, interface


class LiteralDriver(Driver):
    def __init__(self, expected="unknown", observed="unknown", *, missing=False,
                 verdict="succeeded", stale=False, late=False):
        super().__init__()
        self.expected = expected
        self.observed = observed
        self.missing = missing
        self.verdict = verdict
        self.stale = stale
        self.late = late
        self.spec = interface()
        self.spec["actions"]["enter"]["expected_effect"] = {"phase": expected}
        self.spec["method"]["states"]["filled"]["branches"][0]["when"] = {"phase": expected}

    def observe(self, payload):
        row = super().observe(payload)
        if row["sequence"] == 2:
            if self.missing:
                row["predicates"] = {}
            else:
                row["predicates"] = {"phase": self.observed}
            if self.stale:
                row["evidence_digest"] = "digest1"
            if self.late:
                self.now = 10_000_000
        return row

    def verify(self, payload):
        row = super().verify(payload)
        if len(self.calls["verify_effect"]) == 1 and self.verdict != "succeeded":
            return {"status": self.verdict, "evidence_ref": None}
        return row

    def result(self):
        before = copy.deepcopy(self.spec)
        result = super().run(self.spec)
        if self.spec != before:
            raise AssertionError("caller interface changed")
        return result


class LiteralUnknownEffectTests(unittest.TestCase):
    def assert_stopped_after_enter(self, driver, result, reason, verifier_calls):
        self.assertEqual((result["outcome"], result["reason"]), ("SAFE_YIELD", reason))
        self.assertEqual(len(driver.calls["execute"]), 1)
        self.assertEqual(len(driver.calls["verify_effect"]), verifier_calls)
        self.assertEqual(result["completed_transitions"], 1)
        self.assertEqual(result["pending_effect"]["expected_effect"], {"phase": driver.expected})
        self.assertFalse(any(e["event"] == "branch_selected" and e["action"] == "save"
                             for e in result["critical_events"]))

    def test_explicit_unknown_literal_reaches_verifier_and_completion(self):
        driver = LiteralDriver()
        result = driver.result()
        self.assertEqual((result["outcome"], result["reason"]), ("TASK_SUCCEEDED", "method_complete"))
        self.assertEqual(result["completed_transitions"], 2)
        self.assertEqual(len(driver.calls["execute"]), 2)
        self.assertEqual(len(driver.calls["verify_effect"]), 2)
        self.assertEqual(driver.calls["verify_effect"][0]["expected_effect"], {"phase": "unknown"})
        self.assertEqual(driver.calls["verify_effect"][0]["observation"]["predicates"], {"phase": "unknown"})

    def test_literal_match_still_requires_negative_verifier_disposition(self):
        for status in ("failed", "unavailable"):
            with self.subTest(status=status):
                driver = LiteralDriver(verdict=status)
                result = driver.result()
                self.assert_stopped_after_enter(driver, result, "effect_" + status, 1)

    def test_nonmatching_legacy_unknown_stays_unavailable(self):
        driver = LiteralDriver(expected="known")
        self.assert_stopped_after_enter(driver, driver.result(), "effect_unavailable", 0)

    def test_missing_literal_predicate_stays_unavailable(self):
        driver = LiteralDriver(missing=True)
        self.assert_stopped_after_enter(driver, driver.result(), "effect_unavailable", 0)

    def test_other_literals_and_exact_scalar_types_keep_their_meaning(self):
        for value in ("known", "Unknown", "unknown "):
            with self.subTest(value=value):
                driver = LiteralDriver(expected=value, observed=value)
                self.assertEqual(driver.result()["outcome"], "TASK_SUCCEEDED")
                self.assertEqual(len(driver.calls["verify_effect"]), 2)
        for expected, actual in ((0, False), (False, 0), ("unknown", 0), ("unknown", True)):
            with self.subTest(expected=expected, actual=actual):
                driver = LiteralDriver(expected=expected, observed=actual)
                self.assert_stopped_after_enter(driver, driver.result(), "effect_failed", 0)

    def test_no_progress_and_deadline_precede_literal_verifier(self):
        for kwargs, reason in (({"stale": True}, "no_progress"),
                               ({"late": True}, "budget_exhausted")):
            with self.subTest(reason=reason):
                driver = LiteralDriver(**kwargs)
                self.assert_stopped_after_enter(driver, driver.result(), reason, 0)

    def test_literal_unknown_can_be_verified_in_two_successive_states(self):
        driver = LiteralDriver()
        driver.spec["actions"]["save"]["expected_effect"] = {"phase": "unknown"}
        driver.spec["method"]["states"]["done"]["branches"][0]["when"] = {"phase": "unknown"}
        original = driver.observe

        def observe(payload):
            row = original(payload)
            if row["sequence"] == 3:
                row["predicates"] = {"phase": "unknown"}
            return row

        driver.observe = observe
        result = driver.result()
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["completed_transitions"], 2)
        self.assertEqual(len(driver.calls["verify_effect"]), 2)
        self.assertEqual([e["status"] for e in result["critical_events"]
                          if e["event"] == "effect_checked"], ["succeeded", "succeeded"])


if __name__ == "__main__":
    unittest.main()
