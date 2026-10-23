import unittest

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
