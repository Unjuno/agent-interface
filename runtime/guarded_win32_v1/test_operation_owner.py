"""Inert custody-gate tests for the Win32 operation owner."""
import unittest
import threading
import multiprocessing
import time

from runtime.guarded_win32_v1.operation_owner import OperationOwner, OwnerRefused


GEN_A = "a" * 64
GEN_B = "b" * 64
PRODUCER = {"pid": 4101, "creation_time_100ns": 7001}
OTHER_PRODUCER = {"pid": 4102, "creation_time_100ns": 7002}
PROCESS_IDENTITIES = {4101: PRODUCER, 4102: OTHER_PRODUCER}


class FakeClock:
    def __init__(self):
        self.now = 100

    def __call__(self):
        return self.now


class FakeProcess:
    def __init__(self, identity):
        self.pid = identity["pid"]
        self.alive = True
        self.exitcode = None

    def is_alive(self):
        return self.alive


def _inert_blocking_producer(started):
    started.set()
    while True:
        time.sleep(0.01)


class OperationOwnerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.owner = OperationOwner(clock_ns=self.clock,
            process_identity_reader=lambda process: PROCESS_IDENTITIES.get(process.pid))

    def start_cancelled_operation(self):
        self.owner.admit("op-1", GEN_A, 1_000, ["key:a", "button:left"])
        self.process = FakeProcess(PRODUCER)
        self.owner.producer_started("op-1", GEN_A, self.process,
                                    process_identity=PRODUCER)
        return self.owner.request_cancel("op-1", GEN_A, cleanup_deadline_ns=900)

    def test_gate_callback_that_opens_then_raises_cannot_claim_gate_remained_closed(self):
        self.owner.admit("op-gate-error", GEN_A, 1_000, ["key:a"], start_gate_required=True)
        process = FakeProcess(PRODUCER)
        self.assertTrue(self.owner.producer_started("op-gate-error", GEN_A, process,
                                                   process_identity=PRODUCER))
        gate = threading.Event()

        def open_then_raise():
            gate.set()
            raise RuntimeError("gate result lost after opening")

        self.assertFalse(self.owner.authorize_producer_start(
            "op-gate-error", GEN_A, process, open_then_raise))
        self.assertTrue(gate.is_set())
        result = self.owner.result("op-gate-error")
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["producer_gate_state"], "authorization_attempted")
        self.assertFalse(result["release_confirmed"])
        self.assertFalse(result["replay_allowed"])

    def test_cancel_closes_admission_until_exact_producer_retirement_and_readback(self):
        pending = self.start_cancelled_operation()
        self.assertEqual(pending["status"], "pending")
        self.assertFalse(pending["release_confirmed"])
        self.assertFalse(pending["replay_allowed"])
        self.assertIs(self.owner.producer_handle_for_retirement(
            "op-1", GEN_A), self.process)
        repeated = self.owner.request_cancel(
            "op-1", GEN_A, cleanup_deadline_ns=850)
        self.assertEqual(repeated["cleanup_deadline_ns"], 900)
        with self.assertRaises(OwnerRefused):
            self.owner.admit("op-2", GEN_B, 1_000, ["key:a"])

        impostor = FakeProcess(OTHER_PRODUCER)
        impostor.alive = False
        impostor.exitcode = 0
        self.assertFalse(self.owner.producer_retired(
            "op-1", GEN_A, impostor))
        self.assertIsNone(self.owner.claim_recovery("op-1", GEN_A))
        with self.assertRaises(OwnerRefused):
            self.owner.producer_retired(
                "op-1", GEN_B, self.process)
        self.assertIsNone(self.owner.claim_recovery("op-1", GEN_A))

        self.process.alive = False
        self.process.exitcode = 17
        self.assertTrue(self.owner.producer_retired(
            "op-1", GEN_A, self.process))
        recovery = self.owner.claim_recovery("op-1", GEN_A)
        self.assertEqual(recovery["obligations"], ["key:a", "button:left"])
        self.assertFalse(self.owner.claim_recovery("op-1", GEN_A))
        self.assertTrue(self.owner.recovery_completed(
            "op-1", GEN_A, recovery["recovery_id"], release_accepted=True,
            readback={"operation_id": "op-1", "target_generation": GEN_A,
                      "recovery_id": recovery["recovery_id"], "neutral": True}))
        terminal = self.owner.request_cancel(
            "op-1", GEN_A, cleanup_deadline_ns=850)
        self.assertTrue(terminal["release_confirmed"])
        self.assertEqual(terminal["recovery_id"], recovery["recovery_id"])

        with self.assertRaises(OwnerRefused):
            self.owner.admit("op-2", GEN_A, 1_000, ["key:a"])
        self.owner.admit("op-2", GEN_B, 1_000, ["key:a"])
        with self.assertRaises(OwnerRefused):
            self.owner.admit("op-1", GEN_B, 1_000, ["key:a"])

    def test_normal_completion_requires_exact_exit_and_verified_neutral_release(self):
        self.owner.admit("op-complete", GEN_A, 1_000, ["CTRL"],
                         start_gate_required=True)
        process = FakeProcess(PRODUCER)
        self.assertTrue(self.owner.producer_started("op-complete", GEN_A,
            process, process_identity=PRODUCER))
        self.assertTrue(self.owner.authorize_producer_start(
            "op-complete", GEN_A, process, lambda: None))
        process.alive = False
        process.exitcode = 0
        release = {"verified": True, "keys_down": [], "buttons_down": [],
                   "keys_unknown": [], "buttons_unknown": []}
        readback = {"operation_id": "op-complete", "target_generation": GEN_A,
                    "producer_exit_confirmed_ns": 100,
                    "observed_monotonic_ns": 100, "neutral": True}

        complete = getattr(self.owner, "producer_completed", None)
        self.assertTrue(callable(complete), "normal producer completion is not implemented")
        try:
            completed = complete("op-complete", GEN_A, process,
                release_receipt=release, readback=readback)
        except TypeError as error:
            self.fail(f"normal completion does not require independent readback: {error}")

        self.assertEqual(completed["phase"], "completed")
        self.assertTrue(completed["release_confirmed"])
        self.assertEqual(completed["completion_release_receipt"], release)
        self.assertEqual(completed["completion_readback"], readback)
        self.assertIsNone(completed["task_success"])
        self.assertFalse(completed["replay_allowed"])
        try:
            repeated = complete("op-complete", GEN_A, process,
                                release_receipt=release, readback=readback)
        except OwnerRefused as error:
            self.fail(f"identical completed producer receipt was not idempotent: {error}")
        self.assertEqual(repeated["phase"], "completed")
        changed_release = dict(release, receipt_source="different")
        with self.assertRaises(OwnerRefused):
            complete("op-complete", GEN_A, process,
                     release_receipt=changed_release, readback=readback)
        self.assertEqual(self.owner.admit("op-next", GEN_A, 1_000, [])[
            "status"], "admitted")

    def test_normal_completion_with_unknown_release_keeps_admission_closed(self):
        self.owner.admit("op-unknown-complete", GEN_A, 1_000, ["CTRL"],
                         start_gate_required=True)
        process = FakeProcess(PRODUCER)
        self.assertTrue(self.owner.producer_started("op-unknown-complete", GEN_A,
            process, process_identity=PRODUCER))
        self.assertTrue(self.owner.authorize_producer_start(
            "op-unknown-complete", GEN_A, process, lambda: None))
        process.alive = False
        process.exitcode = 0
        readback = {"operation_id": "op-unknown-complete",
                    "target_generation": GEN_A,
                    "producer_exit_confirmed_ns": 100,
                    "observed_monotonic_ns": 100, "neutral": True}

        complete = getattr(self.owner, "producer_completed", None)
        self.assertTrue(callable(complete), "normal producer completion is not implemented")
        completed = complete("op-unknown-complete", GEN_A,
            process, release_receipt={"verified": False,
                "keys_down": [], "buttons_down": [],
                "keys_unknown": ["CTRL"], "buttons_unknown": []},
            readback=readback)

        self.assertEqual(completed["phase"], "unknown")
        self.assertFalse(completed["release_confirmed"])
        with self.assertRaises(OwnerRefused):
            self.owner.admit("op-next", GEN_B, 1_000, [])

    def test_wrong_completion_handle_does_not_strand_live_producer_outside_cancel(self):
        self.owner.admit("op-wrong-completion", GEN_A, 1_000, ["CTRL"],
                         start_gate_required=True)
        process = FakeProcess(PRODUCER)
        self.assertTrue(self.owner.producer_started("op-wrong-completion", GEN_A,
            process, process_identity=PRODUCER))
        self.assertTrue(self.owner.authorize_producer_start(
            "op-wrong-completion", GEN_A, process, lambda: None))
        impostor = FakeProcess(OTHER_PRODUCER)
        impostor.alive = False
        impostor.exitcode = 0
        complete = self.owner.producer_completed

        with self.assertRaises(OwnerRefused):
            complete("op-wrong-completion", GEN_A, impostor,
                release_receipt={"verified": True, "keys_down": [],
                    "buttons_down": [], "keys_unknown": [], "buttons_unknown": []},
                readback={"operation_id": "op-wrong-completion",
                    "target_generation": GEN_A,
                    "producer_exit_confirmed_ns": 100,
                    "observed_monotonic_ns": 100, "neutral": True})

        self.assertEqual(self.owner.result("op-wrong-completion")["phase"], "running")
        self.assertEqual(self.owner.request_cancel("op-wrong-completion", GEN_A,
            cleanup_deadline_ns=900)["status"], "pending")

    def test_cancel_winning_before_start_authorization_keeps_child_gate_closed(self):
        self.owner.admit("op-gate", GEN_A, 1_000, ["key:a"])
        process = FakeProcess(PRODUCER)
        self.assertTrue(self.owner.producer_started("op-gate", GEN_A, process,
            process_identity=PRODUCER))
        self.owner.request_cancel("op-gate", GEN_A, cleanup_deadline_ns=900)
        released = []
        self.assertFalse(self.owner.authorize_producer_start(
            "op-gate", GEN_A, process, lambda: released.append(True)))
        self.assertEqual(released, [])

    def test_failed_readback_retains_unknown_custody_and_refuses_new_operation(self):
        self.start_cancelled_operation()
        self.process.alive = False
        self.process.exitcode = 0
        self.assertTrue(self.owner.producer_retired(
            "op-1", GEN_A, self.process))
        recovery = self.owner.claim_recovery("op-1", GEN_A)
        self.assertFalse(self.owner.recovery_completed(
            "op-1", GEN_A, recovery["recovery_id"], release_accepted=True,
            readback={"operation_id": "op-1", "target_generation": GEN_A,
                      "recovery_id": recovery["recovery_id"], "neutral": False}))
        receipt = self.owner.result("op-1")
        self.assertEqual(receipt["status"], "unknown")
        self.assertFalse(receipt["release_confirmed"])
        self.assertIsNone(receipt["task_success"])
        with self.assertRaises(OwnerRefused):
            self.owner.admit("op-2", GEN_B, 1_000, ["key:a"])

    def test_expired_cleanup_deadline_cannot_authorize_recovery(self):
        self.start_cancelled_operation()
        self.process.alive = False
        self.process.exitcode = 0
        self.assertTrue(self.owner.producer_retired(
            "op-1", GEN_A, self.process))
        self.clock.now = 901
        self.assertIsNone(self.owner.claim_recovery("op-1", GEN_A))
        receipt = self.owner.result("op-1")
        self.assertEqual(receipt["status"], "unknown")
        self.assertFalse(receipt["release_confirmed"])

    def test_cancel_during_child_startup_never_authorizes_late_child(self):
        self.owner.admit("op-1", GEN_A, 1_000, ["key:a"])
        pending = self.owner.request_cancel(
            "op-1", GEN_A, cleanup_deadline_ns=900)
        self.assertEqual(pending["status"], "pending")
        self.assertIsNone(self.owner.producer_handle_for_retirement(
            "op-1", GEN_A))
        self.process = FakeProcess(PRODUCER)
        self.assertFalse(self.owner.producer_started(
            "op-1", GEN_A, self.process, process_identity=PRODUCER))
        self.assertIs(self.owner.producer_handle_for_retirement(
            "op-1", GEN_A), self.process)
        self.assertEqual(self.owner.result("op-1")["phase"], "cancel_pending")
        self.process.alive = False
        self.process.exitcode = 0
        self.assertTrue(self.owner.producer_retired(
            "op-1", GEN_A, self.process))
        self.assertIsNotNone(self.owner.claim_recovery("op-1", GEN_A))

    def test_admission_accepts_a_valid_empty_obligation_snapshot(self):
        admitted = self.owner.admit("op-empty", GEN_A, 1_000, [])
        self.assertEqual(admitted["status"], "admitted")
        self.assertEqual(admitted["obligations"], [])

    def test_blocked_process_identity_query_does_not_hold_cancel_lock(self):
        entered = threading.Event()
        release = threading.Event()

        def blocked_identity_reader(_process):
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test identity barrier expired")
            return PRODUCER

        owner = OperationOwner(clock_ns=self.clock,
            process_identity_reader=blocked_identity_reader)
        owner.admit("op-1", GEN_A, 1_000, ["key:a"])
        process = FakeProcess(PRODUCER)
        started = []
        start_thread = threading.Thread(target=lambda: started.append(
            owner.producer_started("op-1", GEN_A, process,
                                   process_identity=PRODUCER)))
        start_thread.start()
        try:
            self.assertTrue(entered.wait(1))
            cancel_done = threading.Event()
            cancel_result = []

            def cancel():
                cancel_result.append(owner.request_cancel(
                    "op-1", GEN_A, cleanup_deadline_ns=900))
                cancel_done.set()

            cancel_thread = threading.Thread(target=cancel)
            cancel_thread.start()
            self.assertTrue(cancel_done.wait(1))
            self.assertEqual(cancel_result[0]["status"], "pending")
        finally:
            release.set()
            start_thread.join(2)
            if 'cancel_thread' in locals():
                cancel_thread.join(2)
        self.assertFalse(start_thread.is_alive())
        self.assertEqual(started, [False])

    def test_spawned_inert_child_must_exit_before_recovery_can_be_claimed(self):
        context = multiprocessing.get_context("spawn")
        started = context.Event()
        process = context.Process(target=_inert_blocking_producer,
                                  args=(started,))
        process.start()
        try:
            self.assertTrue(started.wait(5))
            identity = {"pid": process.pid, "creation_time_100ns": 9001}
            owner = OperationOwner(clock_ns=self.clock,
                process_identity_reader=lambda candidate: identity if candidate is process else None)
            owner.admit("spawned-op", GEN_A, 1_000, ["key:a"])
            self.assertTrue(owner.producer_started(
                "spawned-op", GEN_A, process, process_identity=identity))
            owner.request_cancel("spawned-op", GEN_A, cleanup_deadline_ns=900)
            self.assertIsNone(owner.claim_recovery("spawned-op", GEN_A))
            process.terminate()
            process.join(3)
            self.assertFalse(process.is_alive())
            self.assertTrue(owner.producer_retired(
                "spawned-op", GEN_A, process))
            self.assertIsInstance(process.exitcode, int)
            self.assertIsNotNone(owner.claim_recovery("spawned-op", GEN_A))
        finally:
            if process.is_alive():
                process.terminate()
                process.join(3)
            process.close()


if __name__ == "__main__":
    unittest.main()
