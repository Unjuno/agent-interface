"""A validated builtin admission return must stay private across callbacks."""
import unittest

from runtime.core_v1.compiled_gui import run
from runtime.core_v1.test_compiled_gui import Driver, interface


class CompiledAdmissionReturnCustodyTests(unittest.TestCase):
    def exercise(self, mutation=None, stage=1, boundary="continue", initial=None):
        driver = Driver()
        ordinary_admit = driver.admit
        ordinary_execute = driver.execute
        returned = []
        validated = []
        dispatch = []
        self.last_driver = driver
        self.last_dispatch = dispatch
        consumed = set()

        def admit(payload):
            value = ordinary_admit(payload)
            if initial:
                value.update(initial)
            returned.append(value)
            validated.append(value.copy())
            return value

        def cancelled():
            if len(returned) == stage and stage not in consumed:
                consumed.add(stage)
                if mutation == "clear":
                    returned[-1].clear()
                elif mutation:
                    returned[-1].update(mutation)
                if boundary == "cancel":
                    return True
                if boundary == "exception":
                    raise RuntimeError("post-admission cancellation unavailable")
                if boundary == "deadline":
                    driver.now = 10_000_000
            return False

        def execute(payload):
            dispatch.append(payload.copy())
            return ordinary_execute(payload)

        result = run(interface(), {"observe": driver.observe, "admit": admit,
                     "execute": execute, "verify_effect": driver.verify,
                     "cancelled": cancelled, "journal": driver.journal},
                     clock=lambda: driver.now)
        return result, driver, returned, validated, dispatch

    def expected_dispatch(self, validated):
        return [{"action": action, "operation": action,
                 "authorization": value["authorization"],
                 "expected_sequence": value["expected_sequence"],
                 "valid_until_ns": min(value["valid_until_ns"], 10_000_000)}
                for action, value in zip(("enter", "save"), validated)]

    def test_retained_admission_edits_do_not_rebind_dispatch_fields(self):
        mutations = ({"authorization": "adapter-local-rebound"},
                     {"authorization": ""},
                     {"expected_sequence": 900},
                     {"expected_sequence": True},
                     {"valid_until_ns": 0},
                     {"eligible": False, "status": "missing", "authorization": None,
                      "expected_sequence": False, "valid_until_ns": True})
        for stage in (1, 2):
            for mutation in mutations:
                with self.subTest(stage=stage, mutation=mutation):
                    result, driver, returned, validated, dispatch = self.exercise(mutation, stage)
                    self.assertEqual(dispatch, self.expected_dispatch(validated))
                    for payload in dispatch:
                        self.assertIs(type(payload["authorization"]), str)
                        self.assertIs(type(payload["expected_sequence"]), int)
                        self.assertIs(type(payload["valid_until_ns"]), int)
                    self.assertEqual((result["outcome"], result["completed_transitions"]), ("TASK_SUCCEEDED", 2))
                    self.assertEqual(len(driver.calls["execute"]), 2)
                    # Python dict equality aliases True and1; compare types too.
                    self.assertTrue(any(type(returned[stage - 1][key]) is not type(value)
                                        or returned[stage - 1][key] != value
                                        for key, value in validated[stage - 1].items()))

    def test_retained_admission_clear_does_not_interrupt_authorized_prefix(self):
        for stage in (1, 2):
            with self.subTest(stage=stage):
                try:
                    result, _, returned, validated, dispatch = self.exercise("clear", stage)
                except KeyError as error:
                    self.fail(f"retained admission payload clearing changed dispatch: {error}")
                self.assertEqual(returned[stage - 1], {})
                self.assertEqual(dispatch, self.expected_dispatch(validated))
                self.assertEqual((result["outcome"], result["completed_transitions"]), ("TASK_SUCCEEDED", 2))

    def test_cancellation_still_stops_before_dispatch_after_local_clear(self):
        for stage in (1, 2):
            with self.subTest(stage=stage):
                result, driver, _, _, dispatch = self.exercise("clear", stage, "cancel")
                self.assertEqual((result["outcome"], result["reason"]), ("SAFE_YIELD", "cancelled"))
                self.assertEqual((result["completed_transitions"], len(dispatch), len(driver.calls["execute"])), (stage - 1, stage - 1, stage - 1))

    def test_deadline_still_stops_before_dispatch_after_local_clear(self):
        for stage in (1, 2):
            with self.subTest(stage=stage):
                result, driver, _, _, dispatch = self.exercise("clear", stage, "deadline")
                self.assertEqual((result["outcome"], result["reason"]), ("SAFE_YIELD", "budget_exhausted"))
                self.assertEqual((result["completed_transitions"], len(dispatch), len(driver.calls["execute"])), (stage - 1, stage - 1, stage - 1))

    def test_cancellation_exception_retains_typed_prefix_after_local_clear(self):
        for stage in (1, 2):
            with self.subTest(stage=stage):
                result, driver, returned, _, dispatch = self.exercise("clear", stage, "exception")
                self.assertEqual((result["outcome"], result["reason"]),
                                 ("RUNTIME_FAILED", "execution_failed"))
                self.assertEqual(returned[stage - 1], {})
                self.assertEqual((result["completed_transitions"], len(result["transitions"]),
                                  len(dispatch), len(driver.calls["execute"])),
                                 (stage - 1, stage - 1, stage - 1, stage - 1))
                self.assertTrue(all(row["release_verified"] is True for row in result["transitions"]))
                self.assertIsNone(result["pending_effect"])
                self.assertEqual(result["critical_events"][-2], {
                    "event": "cancellation_check_failed", "error_type": "RuntimeError"})
                self.assertEqual(result["critical_events"][-1], {
                    "event": "runtime_finished", "outcome": "RUNTIME_FAILED",
                    "reason": "execution_failed", "completed_transitions": stage - 1})

    def test_initial_malformed_fields_still_reject_before_dispatch(self):
        cases = ({"authorization": None}, {"authorization": ""},
                 {"expected_sequence": True}, {"expected_sequence": 900},
                 {"valid_until_ns": False}, {"valid_until_ns": 0})
        for value in cases:
            with self.subTest(initial=value):
                with self.assertRaisesRegex(ValueError, "fresh revalidated admission required"):
                    self.exercise(initial=value)
                self.assertEqual(self.last_dispatch, [])
                self.assertEqual(self.last_driver.calls["execute"], [])


if __name__ == "__main__":
    unittest.main()
