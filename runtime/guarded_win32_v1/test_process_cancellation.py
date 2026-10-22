"""Process-level cancellation composition with inert fake input state."""
import multiprocessing
import time
import unittest

from runtime.guarded_win32_v1.operation_owner import OperationOwner, OwnerRefused
from runtime.guarded_win32_v1.process_cancellation import (
    OperationCancellationSupervisor,
)


GENERATION = "a" * 64


def _blocked_fake_producer(down, started):
    down.set()
    started.set()
    while True:
        time.sleep(0.01)


def _blocked_before_fake_acceptance(started):
    started.set()
    while True:
        time.sleep(0.01)


def _fake_recovery_worker(down, neutral, start_gate, result_send, request):
    if not start_gate.wait(3):
        result_send.close()
        return
    down.clear()
    neutral.set()
    result_send.send({
        "operation_id": request["operation_id"],
        "target_generation": request["target_generation"],
        "recovery_id": request["recovery_id"],
        "release_accepted": True,
    })
    result_send.close()


def _blocked_recovery_worker(start_gate, started, result_send):
    if start_gate.wait(2):
        started.set()
        while True:
            time.sleep(0.01)
    result_send.close()


def _fake_readback_worker(neutral, request, result_send):
    result_send.send({
        "operation_id": request["operation_id"],
        "target_generation": request["target_generation"],
        "recovery_id": request["recovery_id"],
        "neutral": neutral.is_set(),
    })
    result_send.close()


def _blocked_readback_worker(started, result_send):
    started.set()
    while True:
        time.sleep(0.01)


def _recovery_without_receipt(start_gate):
    start_gate.wait(3)


def _recovery_with_wrong_receipt(start_gate, result_send, request):
    if start_gate.wait(3):
        result_send.send({
            "operation_id": "wrong-operation",
            "target_generation": request["target_generation"],
            "recovery_id": request["recovery_id"],
            "release_accepted": True,
        })
    result_send.close()


class NeverRetiresProcess:
    def __init__(self, pid):
        self.pid = pid
        self.exitcode = None

    def is_alive(self):
        return True

    def terminate(self):
        pass

    def kill(self):
        pass

    def join(self, _timeout=None):
        pass


def _identity(process):
    return {"pid": process.pid, "creation_time_100ns": id(process) or 1}


class ProcessCancellationTests(unittest.TestCase):
    def test_cancel_returns_pending_and_recovers_only_after_exact_child_exit(self):
        context = multiprocessing.get_context("spawn")
        down = context.Event()
        producer_started = context.Event()
        neutral = context.Event()
        producer = context.Process(target=_blocked_fake_producer,
                                   args=(down, producer_started))
        producer.start()
        supervisor = None
        recovery_checks = []
        recovery_exit_codes = []
        try:
            self.assertTrue(producer_started.wait(5))
            self.assertTrue(down.is_set())
            identity = _identity(producer)
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=_identity)
            owner.admit("operation-1", GENERATION,
                        time.monotonic_ns() + 5_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started(
                "operation-1", GENERATION, producer,
                process_identity=identity))

            recovery_handles = []

            def recovery_process_factory(request, start_gate):
                recovery_checks.append(producer.is_alive())
                receive, send = context.Pipe(duplex=False)
                recovery = context.Process(target=_fake_recovery_worker,
                    args=(down, neutral, start_gate, send, request))
                recovery_handles.append((recovery, receive, send))
                return recovery, receive

            observer_handles = []

            def observer_process_factory(request):
                receive, send = context.Pipe(duplex=False)
                observer = context.Process(target=_fake_readback_worker,
                    args=(neutral, request, send))
                observer_handles.append((observer, receive, send))
                return observer, receive

            supervisor = OperationCancellationSupervisor(
                owner, recovery_process_factory=recovery_process_factory,
                observer_process_factory=observer_process_factory,
                process_identity_reader=_identity)
            deadline_ns = time.monotonic_ns() + 3_000_000_000
            before = time.monotonic_ns()
            first = supervisor.cancel("operation-1", GENERATION,
                                      cleanup_deadline_ns=deadline_ns)
            elapsed_ns = time.monotonic_ns() - before
            second = supervisor.cancel("operation-1", GENERATION,
                                       cleanup_deadline_ns=deadline_ns)
            self.assertLess(elapsed_ns, 300_000_000)
            self.assertEqual(first["status"], "pending")
            self.assertEqual(second["operation_id"], first["operation_id"])
            self.assertFalse(first["release_confirmed"])
            self.assertIsNone(first["task_success"])
            self.assertFalse(first["replay_allowed"])

            wait_until = time.monotonic() + 4
            result = owner.result("operation-1")
            while result["status"] not in ("recovered", "unknown") and time.monotonic() < wait_until:
                time.sleep(0.01)
                result = owner.result("operation-1")
            self.assertEqual(result["status"], "recovered", result)
            self.assertFalse(producer.is_alive())
            self.assertEqual(recovery_checks, [False])
            self.assertFalse(down.is_set())
            self.assertTrue(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
        finally:
            if supervisor is not None:
                supervisor.close()
            for recovery, receive, send in recovery_handles:
                try:
                    if recovery.is_alive():
                        recovery.terminate()
                        recovery.join(2)
                except ValueError:
                    pass
                for connection in (receive, send):
                    try:
                        connection.close()
                    except OSError:
                        pass
                try:
                    recovery.close()
                except ValueError:
                    pass
            for observer, receive, send in observer_handles:
                try:
                    if observer.is_alive():
                        observer.terminate()
                        observer.join(2)
                except ValueError:
                    pass
                for connection in (receive, send):
                    try:
                        connection.close()
                    except OSError:
                        pass
                try:
                    observer.close()
                except ValueError:
                    pass
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    def test_cancel_before_producer_registration_keeps_custody_until_handle_arrives(self):
        context = multiprocessing.get_context("spawn")
        down = context.Event()
        producer_started = context.Event()
        neutral = context.Event()
        producer = context.Process(target=_blocked_fake_producer,
                                   args=(down, producer_started))
        producer.start()
        supervisor = None
        child_handles = []
        try:
            self.assertTrue(producer_started.wait(5))
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-late-producer", GENERATION,
                        time.monotonic_ns() + 4_000_000_000, ["key:a"])

            def recovery_factory(request, start_gate):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_fake_recovery_worker,
                    args=(down, neutral, start_gate, send, request))
                child_handles.append((process, receive, send))
                return process, receive

            def observer_factory(request):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_fake_readback_worker,
                    args=(neutral, request, send))
                child_handles.append((process, receive, send))
                return process, receive

            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=_identity)
            deadline_ns = time.monotonic_ns() + 3_000_000_000
            response = supervisor.cancel("operation-late-producer", GENERATION,
                                          cleanup_deadline_ns=deadline_ns)
            self.assertEqual(response["status"], "pending")
            self.assertFalse(owner.producer_started("operation-late-producer",
                GENERATION, producer, process_identity=_identity(producer)))
            limit = time.monotonic() + 3
            result = owner.result("operation-late-producer")
            while result["status"] not in ("recovered", "unknown") and time.monotonic() < limit:
                time.sleep(0.01)
                result = owner.result("operation-late-producer")
            self.assertEqual(result["status"], "recovered", result)
            self.assertFalse(producer.is_alive())
            self.assertFalse(down.is_set())
            self.assertTrue(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
        finally:
            if supervisor is not None:
                supervisor.close()
            for process, receive, send in child_handles:
                try:
                    if process.is_alive():
                        process.terminate()
                        process.join(2)
                except ValueError:
                    pass
                for connection in (receive, send):
                    try:
                        connection.close()
                    except OSError:
                        pass
                try:
                    process.close()
                except ValueError:
                    pass
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    def test_cancel_while_blocked_before_fake_acceptance_keeps_result_conservative(self):
        context = multiprocessing.get_context("spawn")
        producer_started = context.Event()
        down = context.Event()
        neutral = context.Event()
        producer = context.Process(target=_blocked_before_fake_acceptance,
                                   args=(producer_started,))
        producer.start()
        supervisor = None
        handles = []
        try:
            self.assertTrue(producer_started.wait(5))
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-before-accept", GENERATION,
                        time.monotonic_ns() + 3_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started("operation-before-accept",
                GENERATION, producer, process_identity=_identity(producer)))

            def recovery_factory(request, start_gate):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_fake_recovery_worker,
                    args=(down, neutral, start_gate, send, request))
                handles.append((process, receive, send))
                return process, receive

            def observer_factory(request):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_fake_readback_worker,
                    args=(neutral, request, send))
                handles.append((process, receive, send))
                return process, receive

            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=_identity)
            response = supervisor.cancel("operation-before-accept", GENERATION,
                cleanup_deadline_ns=time.monotonic_ns() + 2_000_000_000)
            self.assertEqual(response["status"], "pending")
            limit = time.monotonic() + 2
            result = owner.result("operation-before-accept")
            while result["status"] not in ("recovered", "unknown") and time.monotonic() < limit:
                time.sleep(0.005)
                result = owner.result("operation-before-accept")
            self.assertEqual(result["status"], "recovered", result)
            self.assertFalse(producer.is_alive())
            self.assertFalse(down.is_set())
            self.assertTrue(neutral.is_set())
            self.assertTrue(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
        finally:
            if supervisor is not None:
                supervisor.close()
            self._dispose_children(handles)
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    def test_blocked_recovery_process_expires_unknown_without_neutral_readback(self):
        context = multiprocessing.get_context("spawn")
        down = context.Event()
        producer_started = context.Event()
        recovery_started = context.Event()
        neutral = context.Event()
        producer = context.Process(target=_blocked_fake_producer,
                                   args=(down, producer_started))
        producer.start()
        supervisor = None
        readback_calls = []
        recovery_handles = []
        try:
            self.assertTrue(producer_started.wait(5))
            identity_reader = _identity
            producer_identity = _identity(producer)
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=identity_reader)
            owner.admit("operation-blocked-recovery", GENERATION,
                        time.monotonic_ns() + 2_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started(
                "operation-blocked-recovery", GENERATION, producer,
                process_identity=producer_identity))

            def recovery_process_factory(request, start_gate):
                result_receive, result_send = context.Pipe(duplex=False)
                process = context.Process(target=_blocked_recovery_worker,
                    args=(start_gate, recovery_started, result_send))
                recovery_handles.append((process, result_receive, result_send))
                return process, result_receive

            def readback_reader(request):
                readback_calls.append(request["recovery_id"])
                receive, send = context.Pipe(duplex=False)
                observer = context.Process(target=_fake_readback_worker,
                    args=(neutral, request, send))
                recovery_handles.append((observer, receive, send))
                return observer, receive

            supervisor = OperationCancellationSupervisor(
                owner, recovery_process_factory=recovery_process_factory,
                observer_process_factory=readback_reader,
                process_identity_reader=identity_reader,
                terminate_grace_s=0.05, kill_grace_s=0.05)
            deadline_ns = time.monotonic_ns() + 700_000_000
            response = supervisor.cancel("operation-blocked-recovery", GENERATION,
                                         cleanup_deadline_ns=deadline_ns)
            self.assertEqual(response["status"], "pending")
            self.assertTrue(recovery_started.wait(2))
            limit = time.monotonic() + 2
            result = owner.result("operation-blocked-recovery")
            while result["status"] != "unknown" and time.monotonic() < limit:
                time.sleep(0.01)
                result = owner.result("operation-blocked-recovery")
            self.assertEqual(result["status"], "unknown", result)
            self.assertTrue(recovery_started.is_set())
            self.assertFalse(neutral.is_set())
            self.assertEqual(readback_calls, [])
            self.assertFalse(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
        finally:
            if supervisor is not None:
                supervisor.close()
            for process, receive, send in recovery_handles:
                try:
                    if process.is_alive():
                        process.terminate()
                        process.join(2)
                except ValueError:
                    pass
                for connection in (receive, send):
                    try:
                        connection.close()
                    except OSError:
                        pass
                try:
                    process.close()
                except ValueError:
                    pass
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    def test_blocked_independent_observer_expires_unknown(self):
        context = multiprocessing.get_context("spawn")
        down = context.Event()
        producer_started = context.Event()
        observer_started = context.Event()
        neutral = context.Event()
        producer = context.Process(target=_blocked_fake_producer,
                                   args=(down, producer_started))
        producer.start()
        supervisor = None
        child_handles = []
        try:
            self.assertTrue(producer_started.wait(5))
            identity = _identity(producer)
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-blocked-observer", GENERATION,
                        time.monotonic_ns() + 3_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started("operation-blocked-observer",
                GENERATION, producer, process_identity=identity))

            def recovery_factory(request, start_gate):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_fake_recovery_worker,
                    args=(down, neutral, start_gate, send, request))
                child_handles.append((process, receive, send))
                return process, receive

            def observer_factory(request):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_blocked_readback_worker,
                    args=(observer_started, send))
                child_handles.append((process, receive, send))
                return process, receive

            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=_identity,
                terminate_grace_s=0.05, kill_grace_s=0.05)
            deadline_ns = time.monotonic_ns() + 900_000_000
            response = supervisor.cancel("operation-blocked-observer", GENERATION,
                                          cleanup_deadline_ns=deadline_ns)
            self.assertEqual(response["status"], "pending")
            self.assertTrue(observer_started.wait(2))
            limit = time.monotonic() + 2
            result = owner.result("operation-blocked-observer")
            while result["status"] != "unknown" and time.monotonic() < limit:
                time.sleep(0.01)
                result = owner.result("operation-blocked-observer")
            self.assertEqual(result["status"], "unknown", result)
            self.assertFalse(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
        finally:
            if supervisor is not None:
                supervisor.close()
            for process, receive, send in child_handles:
                try:
                    if process.is_alive():
                        process.terminate()
                        process.join(2)
                except ValueError:
                    pass
                for connection in (receive, send):
                    try:
                        connection.close()
                    except OSError:
                        pass
                try:
                    process.close()
                except ValueError:
                    pass
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    def test_unretired_producer_times_out_unknown_without_recovery(self):
        identity = {"pid": 50001, "creation_time_100ns": 90001}
        producer = NeverRetiresProcess(identity["pid"])
        owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is producer else None)
        owner.admit("operation-stuck-producer", GENERATION,
                    time.monotonic_ns() + 1_000_000_000, ["key:a"])
        self.assertTrue(owner.producer_started("operation-stuck-producer",
            GENERATION, producer, process_identity=identity))
        recovery_factory_calls = []

        def forbidden_recovery_factory(_request, _start_gate):
            recovery_factory_calls.append(True)
            raise AssertionError("recovery must not start before producer retirement")

        def forbidden_observer_factory(_request):
            raise AssertionError("observer must not run before confirmed recovery")

        supervisor = OperationCancellationSupervisor(owner,
            recovery_process_factory=forbidden_recovery_factory,
            observer_process_factory=forbidden_observer_factory,
            process_identity_reader=lambda handle: identity if handle is producer else None,
            terminate_grace_s=0, kill_grace_s=0)
        try:
            response = supervisor.cancel("operation-stuck-producer", GENERATION,
                cleanup_deadline_ns=time.monotonic_ns() + 100_000_000)
            self.assertEqual(response["status"], "pending")
            limit = time.monotonic() + 1
            result = owner.result("operation-stuck-producer")
            while result["status"] != "unknown" and time.monotonic() < limit:
                time.sleep(0.005)
                result = owner.result("operation-stuck-producer")
            self.assertEqual(result["status"], "unknown")
            self.assertFalse(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            self.assertEqual(recovery_factory_calls, [])
            with self.assertRaises(OwnerRefused):
                owner.admit("operation-after-unknown", "b" * 64,
                    time.monotonic_ns() + 1_000_000_000, ["key:b"])
        finally:
            supervisor.close()

    def test_recovery_identity_mismatch_never_opens_start_gate(self):
        context = multiprocessing.get_context("spawn")
        down = context.Event()
        producer_started = context.Event()
        recovery_started = context.Event()
        neutral = context.Event()
        producer = context.Process(target=_blocked_fake_producer,
                                   args=(down, producer_started))
        producer.start()
        supervisor = None
        handles = []
        try:
            self.assertTrue(producer_started.wait(5))

            def mismatching_identity_reader(handle):
                value = _identity(handle)
                if handle is not producer:
                    value = dict(value)
                    value["pid"] += 1
                return value

            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-wrong-recovery-identity", GENERATION,
                        time.monotonic_ns() + 3_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started(
                "operation-wrong-recovery-identity", GENERATION, producer,
                process_identity=_identity(producer)))

            def recovery_factory(request, start_gate):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_blocked_recovery_worker,
                    args=(start_gate, recovery_started, send))
                handles.append((process, receive, send))
                return process, receive

            def observer_factory(_request):
                raise AssertionError("identity mismatch must prevent readback")

            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=mismatching_identity_reader,
                terminate_grace_s=0.05, kill_grace_s=0.05)
            response = supervisor.cancel("operation-wrong-recovery-identity",
                GENERATION, cleanup_deadline_ns=time.monotonic_ns() + 1_500_000_000)
            self.assertEqual(response["status"], "pending")
            limit = time.monotonic() + 2
            result = owner.result("operation-wrong-recovery-identity")
            while result["status"] != "unknown" and time.monotonic() < limit:
                time.sleep(0.005)
                result = owner.result("operation-wrong-recovery-identity")
            self.assertEqual(result["status"], "unknown", result)
            self.assertFalse(recovery_started.is_set())
            self.assertFalse(neutral.is_set())
            self.assertFalse(result["release_confirmed"])
            self.assertFalse(result["replay_allowed"])
        finally:
            if supervisor is not None:
                supervisor.close()
            self._dispose_children(handles)
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    def test_missing_recovery_ipc_receipt_stays_unknown(self):
        context = multiprocessing.get_context("spawn")
        down = context.Event()
        producer_started = context.Event()
        neutral = context.Event()
        producer = context.Process(target=_blocked_fake_producer,
                                   args=(down, producer_started))
        producer.start()
        supervisor = None
        handles = []
        observer_factory_calls = []
        try:
            self.assertTrue(producer_started.wait(5))
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-lost-recovery-receipt", GENERATION,
                        time.monotonic_ns() + 3_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started(
                "operation-lost-recovery-receipt", GENERATION, producer,
                process_identity=_identity(producer)))

            def recovery_factory(_request, start_gate):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_recovery_without_receipt,
                    args=(start_gate,))
                handles.append((process, receive, send))
                return process, receive

            def observer_factory(_request):
                observer_factory_calls.append(True)
                raise AssertionError("missing recovery receipt must block observer")

            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=_identity)
            response = supervisor.cancel("operation-lost-recovery-receipt",
                GENERATION, cleanup_deadline_ns=time.monotonic_ns() + 2_000_000_000)
            self.assertEqual(response["status"], "pending")
            limit = time.monotonic() + 2
            result = owner.result("operation-lost-recovery-receipt")
            while result["status"] != "unknown" and time.monotonic() < limit:
                time.sleep(0.005)
                result = owner.result("operation-lost-recovery-receipt")
            self.assertEqual(result["status"], "unknown", result)
            self.assertFalse(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            self.assertEqual(observer_factory_calls, [])
        finally:
            if supervisor is not None:
                supervisor.close()
            self._dispose_children(handles)
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    def test_wrong_recovery_receipt_cannot_confirm_release(self):
        context = multiprocessing.get_context("spawn")
        down = context.Event()
        producer_started = context.Event()
        producer = context.Process(target=_blocked_fake_producer,
                                   args=(down, producer_started))
        producer.start()
        supervisor = None
        handles = []
        observer_factory_calls = []
        try:
            self.assertTrue(producer_started.wait(5))
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-wrong-receipt", GENERATION,
                        time.monotonic_ns() + 3_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started("operation-wrong-receipt",
                GENERATION, producer, process_identity=_identity(producer)))

            def recovery_factory(request, start_gate):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_recovery_with_wrong_receipt,
                    args=(start_gate, send, request))
                handles.append((process, receive, send))
                return process, receive

            def observer_factory(_request):
                observer_factory_calls.append(True)
                raise AssertionError("wrong recovery receipt must block observer")

            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=_identity)
            response = supervisor.cancel("operation-wrong-receipt", GENERATION,
                cleanup_deadline_ns=time.monotonic_ns() + 2_000_000_000)
            self.assertEqual(response["status"], "pending")
            limit = time.monotonic() + 2
            result = owner.result("operation-wrong-receipt")
            while result["status"] != "unknown" and time.monotonic() < limit:
                time.sleep(0.005)
                result = owner.result("operation-wrong-receipt")
            self.assertEqual(result["status"], "unknown", result)
            self.assertEqual(result["uncertainty"], "recovery_receipt_invalid_or_late")
            self.assertFalse(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            self.assertEqual(observer_factory_calls, [])
        finally:
            if supervisor is not None:
                supervisor.close()
            self._dispose_children(handles)
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    @staticmethod
    def _dispose_children(handles):
        for process, receive, send in handles:
            try:
                if process.is_alive():
                    process.terminate()
                    process.join(2)
            except ValueError:
                pass
            for connection in (receive, send):
                try:
                    connection.close()
                except OSError:
                    pass
            try:
                process.close()
            except ValueError:
                pass


if __name__ == "__main__":
    unittest.main()
