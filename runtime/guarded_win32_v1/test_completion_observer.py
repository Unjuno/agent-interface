import unittest
from unittest.mock import patch

from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor


GENERATION = "a" * 64
OPERATION = "b" * 32


class Owner:
    def __init__(self):
        self.unknown = []

    def result(self, operation_id):
        if operation_id != OPERATION:
            raise ValueError("unknown operation")
        return {"phase": "running", "target_generation": GENERATION,
                "obligations": ["key:fixture:CTRL"]}

    def mark_unknown(self, operation_id, generation, reason):
        self.unknown.append((operation_id, generation, reason))


class CompletionObserverTests(unittest.TestCase):
    def supervisor(self, *, now=500, receipt=None):
        owner = Owner()
        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._owner = owner
        supervisor._clock_ns = lambda: now
        supervisor._exchange_helper = lambda role, request, deadline: receipt
        supervisor._invalidate_helper = lambda role, deadline: None
        return supervisor, owner

    def test_returns_exact_operation_and_generation_bound_post_exit_readback(self):
        receipt = {"operation_id": OPERATION,
            "target_generation": GENERATION, "recovery_id": "c" * 32,
            "neutral": True, "observed_monotonic_ns": 450}
        supervisor, owner = self.supervisor(receipt=receipt)
        requests = []

        def exchange(role, request, deadline):
            requests.append((role, request, deadline))
            receipt["recovery_id"] = request["recovery_id"]
            return receipt

        supervisor._exchange_helper = exchange
        result = supervisor.observe_completed(OPERATION, GENERATION,
            producer_exit_confirmed_ns=400, deadline_ns=600)

        self.assertEqual(set(result), {"operation_id", "target_generation",
            "producer_exit_confirmed_ns", "observed_monotonic_ns", "neutral"})
        self.assertEqual(result["producer_exit_confirmed_ns"], 400)
        self.assertEqual(result["observed_monotonic_ns"], 450)
        self.assertEqual(requests[0][0], "observer")
        self.assertEqual(requests[0][1]["obligations"], ["key:fixture:CTRL"])
        self.assertEqual(requests[0][1]["request_id"],
                         requests[0][1]["recovery_id"])
        self.assertEqual(owner.unknown, [])

    def test_rejects_readback_before_exit_and_marks_operation_unknown(self):
        receipt = {"operation_id": OPERATION,
            "target_generation": GENERATION, "recovery_id": "c" * 32,
            "neutral": True, "observed_monotonic_ns": 399}
        supervisor, owner = self.supervisor(receipt=receipt)
        supervisor._exchange_helper = lambda _role, request, _deadline: {
            **receipt, "recovery_id": request["recovery_id"]}

        result = supervisor.observe_completed(OPERATION, GENERATION,
            producer_exit_confirmed_ns=400, deadline_ns=600)

        self.assertIsNone(result)
        self.assertEqual(len(owner.unknown), 1)
        self.assertIn("invalid_or_late", owner.unknown[0][2])

    def test_configured_normal_completion_horizon_is_sampled_and_receipted(self):
        now = [500]
        supervisor, owner = self.supervisor(now=500)
        supervisor._clock_ns = lambda: now[0]
        supervisor.late_input_horizon_ns = 30
        supervisor._late_input_sample_interval_s = 10 / 1_000_000_000
        requests = []

        def exchange(role, request, deadline):
            requests.append((role, dict(request), deadline))
            now[0] += 10
            return {"operation_id": OPERATION,
                "target_generation": GENERATION,
                "recovery_id": request["recovery_id"],
                "neutral": True, "key_button_states": [False],
                "unicode_event_units": 0,
                "observed_monotonic_ns": now[0]}

        supervisor._exchange_helper = exchange
        def advance(seconds):
            now[0] += max(1, int(seconds * 1_000_000_000))

        supervisor_sleep = advance
        with patch("runtime.guarded_win32_v1.process_cancellation.time.sleep",
                   side_effect=supervisor_sleep):
            result = supervisor.observe_completed(OPERATION, GENERATION,
                producer_exit_confirmed_ns=400, deadline_ns=600)

        self.assertTrue(result["late_input_horizon_verified"])
        self.assertEqual(result["late_input_horizon_ns"], 30)
        self.assertGreaterEqual(result["late_input_observation_count"], 2)
        self.assertGreaterEqual(
            result["late_input_observation_end_monotonic_ns"]
            - result["late_input_observation_start_monotonic_ns"], 30)
        self.assertEqual(
            result["late_input_observation_start_monotonic_ns"], 400)
        self.assertEqual(owner.unknown, [])
        self.assertGreaterEqual(len(requests), 2)

    def test_delayed_old_input_during_normal_completion_horizon_fails_closed(self):
        now = [500]
        supervisor, owner = self.supervisor(now=500)
        supervisor._clock_ns = lambda: now[0]
        supervisor.late_input_horizon_ns = 30
        supervisor._late_input_sample_interval_s = 10 / 1_000_000_000
        observer_count = [0]

        def exchange(role, request, deadline):
            self.assertEqual(role, "observer")
            observer_count[0] += 1
            # A delayed operation from the retired producer arrives after the
            # first neutral sample, while the public completion horizon runs.
            delayed_down = observer_count[0] == 2
            now[0] += 10
            return {"operation_id": OPERATION,
                "target_generation": GENERATION,
                "recovery_id": request["recovery_id"],
                "neutral": not delayed_down,
                "key_button_states": [delayed_down],
                "unicode_event_units": 0,
                "observed_monotonic_ns": now[0]}

        supervisor._exchange_helper = exchange

        def advance(seconds):
            now[0] += max(1, int(seconds * 1_000_000_000))

        with patch("runtime.guarded_win32_v1.process_cancellation.time.sleep",
                   side_effect=advance):
            result = supervisor.observe_completed(OPERATION, GENERATION,
                producer_exit_confirmed_ns=400, deadline_ns=600)

        self.assertIsNone(result)
        self.assertEqual(observer_count[0], 2)
        self.assertEqual(len(owner.unknown), 1)
        self.assertIn("normal_completion_horizon_receipt_invalid_or_late",
            owner.unknown[0][2])

    def test_normal_horizon_rejects_unobserved_gap_after_producer_exit(self):
        supervisor, owner = self.supervisor(now=500)
        supervisor.late_input_horizon_ns = 30
        supervisor._late_input_sample_interval_s = 10 / 1_000_000_000
        supervisor._exchange_helper = lambda _role, request, _deadline: {
            "operation_id": OPERATION,
            "target_generation": GENERATION,
            "recovery_id": request["recovery_id"],
            "neutral": True, "key_button_states": [False],
            "unicode_event_units": 0, "observed_monotonic_ns": 30_000_500}

        result = supervisor.observe_completed(OPERATION, GENERATION,
            producer_exit_confirmed_ns=400, deadline_ns=40_000_000)

        self.assertIsNone(result)
        self.assertEqual(len(owner.unknown), 1)
        self.assertIn("normal_completion_observer_receipt_invalid_or_late",
            owner.unknown[0][2])

    def test_incomplete_horizon_at_deadline_is_unknown_not_success(self):
        now = [500]
        supervisor, owner = self.supervisor(now=500)
        supervisor._clock_ns = lambda: now[0]
        supervisor.late_input_horizon_ns = 100
        supervisor._late_input_sample_interval_s = 10 / 1_000_000_000
        calls = [0]
        clock_values = iter((500, 500, 500, 500, 500, 560,
                             560, 560, 560, 560, 601, 601))
        supervisor._clock_ns = lambda: next(clock_values, 601)

        def exchange(_role, request, _deadline):
            calls[0] += 1
            # Initial neutral sample at producer exit (500), then one at 560; the
            # requested 100 ns horizon cannot fit before deadline 600.
            observed = 500 if calls[0] == 1 else 560
            now[0] = observed
            return {"operation_id": OPERATION,
                "target_generation": GENERATION,
                "recovery_id": request["recovery_id"],
                "neutral": True, "key_button_states": [False],
                "unicode_event_units": 0,
                "observed_monotonic_ns": observed}

        supervisor._exchange_helper = exchange
        with patch("runtime.guarded_win32_v1.process_cancellation.time.sleep",
                   return_value=None):
            result = supervisor.observe_completed(OPERATION, GENERATION,
                producer_exit_confirmed_ns=500, deadline_ns=600)

        self.assertIsNone(result)
        self.assertEqual(calls[0], 3)
        self.assertEqual(len(owner.unknown), 1)
        self.assertIn("duration_uncovered", owner.unknown[0][2])

    def test_refuses_non_running_or_wrong_generation_operations(self):
        supervisor, owner = self.supervisor(receipt={})
        owner.result = lambda _operation: {"phase": "recovered",
            "target_generation": GENERATION, "obligations": []}
        self.assertIsNone(supervisor.observe_completed(OPERATION, GENERATION,
            producer_exit_confirmed_ns=400, deadline_ns=600))
        owner.result = lambda _operation: {"phase": "running",
            "target_generation": "d" * 64, "obligations": []}
        self.assertIsNone(supervisor.observe_completed(OPERATION, GENERATION,
            producer_exit_confirmed_ns=400, deadline_ns=600))
        self.assertEqual(owner.unknown, [])


if __name__ == "__main__":
    unittest.main()
