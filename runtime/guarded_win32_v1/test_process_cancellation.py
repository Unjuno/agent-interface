"""Process-level cancellation composition with inert fake input state."""
import multiprocessing
import os
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


class _BlockedNativeReleaseBackend:
    """Inert backend whose native release boundary never returns."""
    def __init__(self, targets, release_started):
        self.targets = targets
        self.release_started = release_started
        self.pending_unicode_ups = set()
        self.held_keys = {}
        self.held_key_targets = {}
        self.held_buttons = set()
        self.held_button_targets = {}

    def target_generation(self, _target):
        return GENERATION

    def release_all(self):
        self.release_started.set()
        while True:
            time.sleep(0.01)

    def close(self):
        return None


def _handle_blocked_native_recovery(request, response, release_started):
    from runtime.cli_v1.win32_supervisor_helpers import _recover
    result = _recover(request,
        backend_factory=lambda targets: _BlockedNativeReleaseBackend(
            targets, release_started),
        configured_targets={"fixture": 123})
    response.send(result)


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


def _ready_loop_helper(connection, name):
    connection.send({"status": "ready", "helper": name})
    while True:
        request = connection.recv()
        if request is None:
            return
        connection.send({"status": "completed", "helper": name,
                         "request_id": request["request_id"]})


def _invalid_ready_helper(connection):
    connection.send({"status": "ready", "helper": "unexpected"})
    time.sleep(2)


def _handle_crash_helper(_request, _response):
    os._exit(17)


class _OpenStartGate:
    def wait(self, _timeout=None):
        return True


class _PersistentResponse:
    def __init__(self, connection):
        self._connection = connection

    def send(self, value):
        self._connection.send(value)

    def close(self):
        return None


def _persistent_helper_server(connection, name, handler, handler_args):
    connection.send({"status": "ready", "helper": name})
    while True:
        request = connection.recv()
        if request is None:
            return
        handler(request, _PersistentResponse(connection), *handler_args)
        connection.send({"control": "operation_complete",
                         "request_id": request["request_id"]})


def _persistent_helper_factory(context, name, handler, handler_args, handles):
    def factory():
        receive, send = context.Pipe(duplex=True)
        process = context.Process(target=_persistent_helper_server,
            args=(send, name, handler, tuple(handler_args)), daemon=True)
        handles.append((process, receive, send))
        return process, receive
    return factory


def _handle_fake_recovery(request, response, down, neutral):
    _fake_recovery_worker(down, neutral, _OpenStartGate(), response, request)


def _handle_fake_observation(request, response, neutral):
    _fake_readback_worker(neutral, request, response)


def _handle_blocked_recovery(_request, response, started):
    _blocked_recovery_worker(_OpenStartGate(), started, response)


def _handle_blocked_observation(_request, response, started):
    _blocked_readback_worker(started, response)


def _handle_no_recovery_receipt(_request, _response):
    return None


def _handle_wrong_recovery_receipt(request, response):
    _recovery_with_wrong_receipt(_OpenStartGate(), response, request)


def _handle_mark_requested(_request, response, requested):
    requested.set()
    response.send({"status": "requested"})


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
    def test_helper_startup_and_readiness_failures_prevent_supervisor(self):
        context = multiprocessing.get_context("spawn")
        owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=_identity)
        handles = []

        def failed_factory():
            raise RuntimeError("injected helper startup failure")

        with self.assertRaisesRegex(RuntimeError, "startup failure"):
            OperationCancellationSupervisor(owner,
                recovery_process_factory=failed_factory,
                observer_process_factory=failed_factory,
                process_identity_reader=_identity)

        receive, send = context.Pipe(duplex=True)
        bad_ready = context.Process(target=_invalid_ready_helper, args=(send,),
                                    daemon=True)
        handles.append((bad_ready, receive, send))

        def bad_ready_factory():
            return bad_ready, receive

        good_factory = _persistent_helper_factory(context, "recovery",
            _handle_no_recovery_receipt, (), handles)
        with self.assertRaisesRegex(RuntimeError, "readiness or identity"):
            OperationCancellationSupervisor(owner,
                recovery_process_factory=good_factory,
                observer_process_factory=bad_ready_factory,
                process_identity_reader=_identity, startup_timeout_s=0.2,
                terminate_grace_s=0.05, kill_grace_s=0.05)
        self._dispose_children(handles)

    def test_recovery_and_observer_helpers_are_ready_before_admission(self):
        context = multiprocessing.get_context("spawn")
        factories_called = []
        processes = []
        endpoints = []

        def make_helper(name):
            receive, send = context.Pipe(duplex=True)
            process = context.Process(target=_ready_loop_helper,
                args=(send, name), daemon=True)
            factories_called.append(name)
            processes.append(process)
            endpoints.append((receive, send))
            return process, receive

        owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=_identity)
        supervisor = None
        try:
            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=lambda: make_helper("recovery"),
                observer_process_factory=lambda: make_helper("observer"),
                process_identity_reader=_identity)

            self.assertEqual(factories_called, ["recovery", "observer"])
            self.assertEqual(len(processes), 2)
            self.assertTrue(all(process.is_alive() for process in processes))
        finally:
            if supervisor is not None:
                supervisor.close()
            for receive, send in endpoints:
                try:
                    receive.close()
                except OSError:
                    pass
                try:
                    send.close()
                except OSError:
                    pass
            for process in processes:
                try:
                    if process.is_alive():
                        process.terminate()
                        process.join(1)
                    if not process.is_alive():
                        process.close()
                except ValueError:
                    pass

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
        recovery_handles = []
        observer_handles = []
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

            recovery_process_factory = _persistent_helper_factory(context,
                "recovery", _handle_fake_recovery, (down, neutral),
                recovery_handles)
            observer_process_factory = _persistent_helper_factory(context,
                "observer", _handle_fake_observation, (neutral,),
                observer_handles)

            supervisor = OperationCancellationSupervisor(
                owner, recovery_process_factory=recovery_process_factory,
                observer_process_factory=observer_process_factory,
                process_identity_reader=_identity)
            self.assertEqual(len(recovery_handles), 1)
            self.assertEqual(len(observer_handles), 1)
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
            self.assertEqual(len(recovery_handles), 1)
            self.assertEqual(len(observer_handles), 1)
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

            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_fake_recovery, (down, neutral), child_handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_fake_observation, (neutral,), child_handles)

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

            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_fake_recovery, (down, neutral), handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_fake_observation, (neutral,), handles)

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

            recovery_process_factory = _persistent_helper_factory(context,
                "recovery", _handle_blocked_recovery, (recovery_started,),
                recovery_handles)
            observer_process_factory = _persistent_helper_factory(context,
                "observer", _handle_fake_observation, (neutral,),
                recovery_handles)

            supervisor = OperationCancellationSupervisor(
                owner, recovery_process_factory=recovery_process_factory,
                observer_process_factory=observer_process_factory,
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
            self.assertFalse(neutral.is_set())
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

    def test_blocked_release_inside_native_recovery_adapter_stays_unknown(self):
        context = multiprocessing.get_context("spawn")
        down = context.Event()
        producer_started = context.Event()
        release_started = context.Event()
        neutral = context.Event()
        producer = context.Process(target=_blocked_fake_producer,
                                   args=(down, producer_started))
        producer.start()
        supervisor = None
        helper_handles = []
        try:
            self.assertTrue(producer_started.wait(5))
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-blocked-native-release", GENERATION,
                time.monotonic_ns() + 3_000_000_000, ["unicode:0041"])
            self.assertTrue(owner.producer_started(
                "operation-blocked-native-release", GENERATION, producer,
                process_identity=_identity(producer)))

            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_blocked_native_recovery, (release_started,), helper_handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_fake_observation, (neutral,), helper_handles)
            clock_offset_ns = [0]

            def supervisor_clock_ns():
                return time.monotonic_ns() + clock_offset_ns[0]

            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=_identity,
                clock_ns=supervisor_clock_ns,
                terminate_grace_s=0.05, kill_grace_s=0.05)

            # Give the Windows CI worker enough time to schedule the spawned
            # recovery helper into the blocking adapter before its deadline.
            deadline_ns = time.monotonic_ns() + 30_000_000_000
            response = supervisor.cancel("operation-blocked-native-release",
                GENERATION, cleanup_deadline_ns=deadline_ns)
            self.assertEqual(response["status"], "pending")
            started = release_started.wait(10)
            recovery_helper = helper_handles[0][0]
            self.assertTrue(started, {
                "owner": owner.result("operation-blocked-native-release"),
                "recovery_helper_alive": recovery_helper.is_alive(),
                "recovery_helper_exitcode": recovery_helper.exitcode,
            })

            deadline_advanced_at_ns = time.monotonic_ns()
            clock_offset_ns[0] = deadline_ns + 1 - time.monotonic_ns()
            unknown_limit_ns = deadline_advanced_at_ns + 1_000_000_000
            result = owner.result("operation-blocked-native-release")
            while (result["status"] != "unknown"
                    and time.monotonic_ns() < unknown_limit_ns):
                time.sleep(0.01)
                result = owner.result("operation-blocked-native-release")
            unknown_observed_ns = time.monotonic_ns()

            self.assertEqual(result["status"], "unknown", result)
            self.assertLessEqual(unknown_observed_ns, unknown_limit_ns,
                "blocked release must become UNKNOWN promptly after deadline")
            self.assertTrue(down.is_set())
            self.assertFalse(neutral.is_set())
            self.assertFalse(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            self.assertFalse(recovery_helper.is_alive())
        finally:
            if supervisor is not None:
                supervisor.close()
            for process, receive, send in helper_handles:
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

            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_fake_recovery, (down, neutral), child_handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_blocked_observation, (observer_started,), child_handles)

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
        context = multiprocessing.get_context("spawn")
        recovery_requested = context.Event()
        observer_requested = context.Event()
        helper_handles = []
        recovery_factory = _persistent_helper_factory(context, "recovery",
            _handle_mark_requested, (recovery_requested,), helper_handles)
        observer_factory = _persistent_helper_factory(context, "observer",
            _handle_mark_requested, (observer_requested,), helper_handles)

        supervisor = OperationCancellationSupervisor(owner,
            recovery_process_factory=recovery_factory,
            observer_process_factory=observer_factory,
            process_identity_reader=lambda handle: (identity if handle is producer
                else _identity(handle)),
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
            self.assertFalse(recovery_requested.is_set())
            self.assertFalse(observer_requested.is_set())
            with self.assertRaises(OwnerRefused):
                owner.admit("operation-after-unknown", "b" * 64,
                    time.monotonic_ns() + 1_000_000_000, ["key:b"])
        finally:
            supervisor.close()
            self._dispose_children(helper_handles)

    def test_prestarted_helper_identity_mismatch_prevents_ready_supervisor(self):
        context = multiprocessing.get_context("spawn")
        owner = OperationOwner(clock_ns=time.monotonic_ns,
                               process_identity_reader=_identity)
        handles = []

        def mismatching_identity_reader(handle):
            value = _identity(handle)
            value["pid"] += 1
            return value

        recovery_factory = _persistent_helper_factory(context, "recovery",
            _handle_no_recovery_receipt, (), handles)
        observer_factory = _persistent_helper_factory(context, "observer",
            _handle_no_recovery_receipt, (), handles)
        with self.assertRaisesRegex(RuntimeError, "identity"):
            OperationCancellationSupervisor(owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=mismatching_identity_reader,
                terminate_grace_s=0.05, kill_grace_s=0.05)
        self._dispose_children(handles)

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
        observer_requested = context.Event()
        try:
            self.assertTrue(producer_started.wait(5))
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-lost-recovery-receipt", GENERATION,
                        time.monotonic_ns() + 3_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started(
                "operation-lost-recovery-receipt", GENERATION, producer,
                process_identity=_identity(producer)))

            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_no_recovery_receipt, (), handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_mark_requested, (observer_requested,), handles)

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
            self.assertFalse(observer_requested.is_set())
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
        observer_requested = context.Event()
        try:
            self.assertTrue(producer_started.wait(5))
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                                   process_identity_reader=_identity)
            owner.admit("operation-wrong-receipt", GENERATION,
                        time.monotonic_ns() + 3_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started("operation-wrong-receipt",
                GENERATION, producer, process_identity=_identity(producer)))

            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_wrong_recovery_receipt, (), handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_mark_requested, (observer_requested,), handles)

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
            self.assertFalse(observer_requested.is_set())
        finally:
            if supervisor is not None:
                supervisor.close()
            self._dispose_children(handles)
            if producer.is_alive():
                producer.terminate()
                producer.join(2)
            producer.close()

    def test_helper_death_during_request_is_unknown_without_replacement(self):
        context = multiprocessing.get_context("spawn")
        producer_started = context.Event()
        producer = context.Process(target=_blocked_before_fake_acceptance,
                                   args=(producer_started,))
        producer.start()
        supervisor = None
        handles = []
        factory_calls = {"recovery": 0, "observer": 0}
        try:
            self.assertTrue(producer_started.wait(5))
            owner = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=_identity)
            owner.admit("operation-helper-died", GENERATION,
                time.monotonic_ns() + 3_000_000_000, ["key:a"])
            self.assertTrue(owner.producer_started("operation-helper-died",
                GENERATION, producer, process_identity=_identity(producer)))
            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_crash_helper, (), handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_mark_requested, (context.Event(),), handles)

            def counted_recovery_factory():
                factory_calls["recovery"] += 1
                return recovery_factory()

            def counted_observer_factory():
                factory_calls["observer"] += 1
                return observer_factory()

            supervisor = OperationCancellationSupervisor(owner,
                recovery_process_factory=counted_recovery_factory,
                observer_process_factory=counted_observer_factory,
                process_identity_reader=_identity)
            supervisor.cancel("operation-helper-died", GENERATION,
                cleanup_deadline_ns=time.monotonic_ns() + 2_000_000_000)
            limit = time.monotonic() + 2
            result = owner.result("operation-helper-died")
            while result["status"] != "unknown" and time.monotonic() < limit:
                time.sleep(0.005)
                result = owner.result("operation-helper-died")
            self.assertEqual(result["status"], "unknown")
            self.assertFalse(result["release_confirmed"])
            self.assertFalse(result["replay_allowed"])
            self.assertEqual(factory_calls, {"recovery": 1, "observer": 1})
            self.assertEqual(len(handles), 2)
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
