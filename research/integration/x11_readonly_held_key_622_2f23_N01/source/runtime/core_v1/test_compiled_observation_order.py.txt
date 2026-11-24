"""Capture-time causality at the existing compiled adapter boundary."""
import unittest

from runtime.core_v1.compiled_gui import run
from runtime.core_v1.test_compiled_gui import interface


class CaptureDriver:
    """Inert synchronous adapters with one declared monotonic clock domain."""

    def __init__(self, captures=(5, 30, 120)):
        self.captures = captures
        self.now = 0
        self.observations = 0
        self.executions = []
        self.verifications = []

    def observe(self, request):
        index = self.observations
        self.observations += 1
        self.now = (10, 100, 200)[index]
        return {
            "sequence": index + 1,
            "captured_ns": self.captures[index],
            "surface": "form",
            "predicates": {"phase": index},
            "evidence_ref": f"frame-{index + 1}",
            "evidence_digest": f"digest-{index + 1}",
        }

    def admit(self, request):
        return {
            "eligible": True, "status": "revalidated",
            "authorization": "one-use",
            "expected_sequence": request["observation"]["sequence"],
            "valid_until_ns": 1_000_000,
        }

    def execute(self, request):
        self.executions.append(request)
        self.now = (20, 110)[len(self.executions) - 1]
        return {
            "status": "completed", "action_id": f"action-{len(self.executions)}",
            "effect_ref": f"effect-{len(self.executions)}",
            "release": {"verified": True, "keys_down": [], "buttons_down": []},
        }

    def verify(self, request):
        self.verifications.append(request)
        return {"status": "succeeded",
                "evidence_ref": request["observation"]["evidence_ref"]}

    def run(self):
        return run(interface(), {
            "observe": self.observe, "admit": self.admit,
            "execute": self.execute, "verify_effect": self.verify,
            "cancelled": lambda: False,
        }, clock=lambda: self.now)


class CompiledObservationOrderTests(unittest.TestCase):
    def assert_stopped(self, driver, completed, verified):
        receipt = driver.run()
        self.assertEqual((receipt["outcome"], receipt["reason"]),
                         ("SAFE_YIELD", "stale_observation"))
        self.assertEqual(receipt["completed_transitions"], completed)
        self.assertEqual(len(driver.executions), completed)
        self.assertEqual(len(driver.verifications), verified)
        self.assertEqual(len(receipt["observations"]), completed)
        if completed:
            self.assertEqual(receipt["pending_effect"]["action"],
                             "enter" if completed == 1 else "save")
            self.assertTrue(all(t["release_verified"] for t in receipt["transitions"]))

    def test_future_initial_capture_does_not_authorize_input(self):
        for captured in (11, 1000):
            with self.subTest(captured=captured):
                self.assert_stopped(CaptureDriver((captured, 30, 120)), 0, 0)

    def test_capture_before_first_execution_return_cannot_verify_or_continue(self):
        for captured in (0, 10, 19):
            with self.subTest(captured=captured):
                self.assert_stopped(CaptureDriver((5, captured, 120)), 1, 0)

    def test_capture_before_final_execution_return_cannot_complete(self):
        for captured in (0, 100, 109):
            with self.subTest(captured=captured):
                self.assert_stopped(CaptureDriver((5, 30, captured)), 2, 1)

    def test_future_effect_capture_preserves_verified_prefix(self):
        for captures, completed, verified in (
            ((5, 101, 120), 1, 0), ((5, 30, 201), 2, 1),
        ):
            with self.subTest(captures=captures):
                self.assert_stopped(CaptureDriver(captures), completed, verified)

    def test_equal_boundaries_and_later_captures_remain_valid(self):
        for captures in ((0, 20, 110), (5, 30, 120), (10, 100, 200)):
            with self.subTest(captures=captures):
                driver = CaptureDriver(captures)
                receipt = driver.run()
                self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED")
                self.assertEqual(receipt["completed_transitions"], 2)
                self.assertEqual(len(driver.verifications), 2)
                self.assertIsNone(receipt["pending_effect"])


if __name__ == "__main__":
    unittest.main()
