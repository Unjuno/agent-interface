"""Composed process custody through Win32RuntimeSession and Win32Backend with inert APIs."""
import multiprocessing
import os
import time
import unittest

from runtime.backends.win32_v1.backend import KEYEVENTF_KEYUP, VK_CONTROL, Win32Backend
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM
from runtime.guarded_win32_v1.operation_owner import OperationOwner
from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor

GENERATION = "a" * 64
OPERATION_ID = "b" * 32


class FakeUser32:
    def __init__(self, state, events, role, entered=None,
                 accept_before_block=False):
        self.state = state
        self.events = events
        self.role = role
        self.entered = entered
        self.accept_before_block = accept_before_block

    def GetAsyncKeyState(self, vk):
        return 0x8000 if self.state.get(vk, False) else 1

    def SendInput(self, count, inputs, size):
        item = inputs[0]
        vk = int(item.ki.wVk)
        down = not bool(int(item.ki.dwFlags) & KEYEVENTF_KEYUP)
        if self.role == "producer" and down:
            self.events.append({"kind": "producer_down_entered", "pid": os.getpid()})
            if self.accept_before_block:
                self.state[vk] = True
                self.events.append({"kind": "producer_down_accepted", "pid": os.getpid()})
            self.entered.set()
            time.sleep(30)
            return 1
        if self.role == "recovery" and not down:
            self.events.append({"kind": "recovery_up", "pid": os.getpid()})
            self.state[vk] = False
            return 1
        self.events.append({"kind": "unexpected_send", "pid": os.getpid(),
                            "vk": vk, "down": down})
        return 1


def _producer_session(start_gate, state, events, entered, accept_before_block):
    if not start_gate.wait(5):
        return
    backend = Win32Backend.__new__(Win32Backend)
    backend.user32 = FakeUser32(state, events, "producer", entered,
                                accept_before_block)
    backend.held_keys = {}
    backend.held_buttons = set()
    backend.pending_unicode_ups = set()
    backend.emissions = 0
    backend.manifest = lambda: Win32Backend.manifest(backend)
    backend.monotonic_ns = time.monotonic_ns
    session = Win32RuntimeSession(backend)
    program = {
        "schema": SCHEMA_PROGRAM,
        "program_id": "composed-test",
        "source": {"observation_seq": 1, "binding_revision": 1},
        "authority": {"lease_id": "composed-custody",
                      "expires_at_ns": time.monotonic_ns() + 15_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "key_state", "key": "CTRL", "down": True},
            {"op": "release_all"},
        ],
    }
    session.dispatch(program, current_observation_seq=1,
                     current_binding_revision=1)


def _recovery_observer_server(connection, role, state, events):
    connection.send({"status": "ready", "helper": role})
    while True:
        request = connection.recv()
        if request is None:
            return
        if role == "recovery":
            backend = Win32Backend.__new__(Win32Backend)
            backend.user32 = FakeUser32(state, events, "recovery")
            backend.held_keys = {"CTRL": VK_CONTROL}
            backend.held_buttons = set()
            backend.pending_unicode_ups = set()
            backend.emissions = 0
            release = backend.release_all()
            receipt = {
                "operation_id": request["operation_id"],
                "target_generation": request["target_generation"],
                "recovery_id": request["recovery_id"],
                "release_accepted": release["verified"] is True,
            }
        else:
            receipt = {
                "operation_id": request["operation_id"],
                "target_generation": request["target_generation"],
                "recovery_id": request["recovery_id"],
                "neutral": not state.get(VK_CONTROL, False),
            }
        connection.send(receipt)
        connection.send({"control": "operation_complete",
                         "request_id": request["request_id"]})


class RetainedProcess:
    """Parent-side trace wrapper that records confirmed child retirement."""
    def __init__(self, process, events, *, stubborn=False):
        self.process = process
        self.events = events
        self.stubborn = stubborn

    @property
    def pid(self):
        return self.process.pid

    @property
    def exitcode(self):
        return self.process.exitcode

    def is_alive(self):
        return self.process.is_alive()

    def terminate(self):
        if not self.stubborn:
            self.process.terminate()

    def join(self, timeout=None):
        self.process.join(timeout)
        if not self.process.is_alive() and type(self.process.exitcode) is int:
            if not any(row.get("kind") == "producer_exit_confirmed"
                       for row in list(self.events)):
                self.events.append({"kind": "producer_exit_confirmed",
                                    "pid": self.pid,
                                    "exitcode": self.process.exitcode})

    def kill(self):
        if not self.stubborn:
            self.process.kill()

    def close(self):
        self.process.close()


def _identity(process):
    return {"pid": process.pid, "creation_time_100ns": process.pid + 1_000_000_000}


class SupervisedWin32SessionTests(unittest.TestCase):
    def _run_case(self, *, accept_before_block, stubborn=False):
        context = multiprocessing.get_context("spawn")
        with context.Manager() as manager:
            state = manager.dict()
            events = manager.list()
            entered = context.Event()
            start_gate = context.Event()
            handles = []
            supervisor = None
            raw_producer = context.Process(target=_producer_session,
                args=(start_gate, state, events, entered,
                      accept_before_block), daemon=True)
            try:
                def helper_factory(role):
                    receive, send = context.Pipe(duplex=True)
                    helper = context.Process(target=_recovery_observer_server,
                        args=(send, role, state, events), daemon=True)
                    handles.append((helper, receive, send))
                    return helper, receive

                owner = OperationOwner(clock_ns=time.monotonic_ns,
                    process_identity_reader=_identity)
                supervisor = OperationCancellationSupervisor(owner,
                    recovery_process_factory=lambda: helper_factory("recovery"),
                    observer_process_factory=lambda: helper_factory("observer"),
                    process_identity_reader=_identity,
                    terminate_grace_s=0.05, kill_grace_s=0.05)
                deadline = time.monotonic_ns() + 8_000_000_000
                owner.admit(OPERATION_ID, GENERATION, deadline, ["key:CTRL"])
                raw_producer.start()
                producer = RetainedProcess(raw_producer, events, stubborn=stubborn)
                self.assertTrue(owner.producer_started(OPERATION_ID, GENERATION,
                    producer, process_identity=_identity(producer)))
                self.assertTrue(owner.authorize_producer_start(OPERATION_ID,
                    GENERATION, producer, start_gate.set))
                self.assertTrue(entered.wait(5), "producer never entered fake SendInput")
                self.assertEqual(bool(state.get(VK_CONTROL, False)), accept_before_block)

                response = supervisor.cancel(OPERATION_ID, GENERATION,
                    cleanup_deadline_ns=deadline)
                self.assertEqual(response["status"], "pending")
                limit = time.monotonic() + 6
                result = owner.result(OPERATION_ID)
                while result["status"] not in ("recovered", "unknown") and time.monotonic() < limit:
                    time.sleep(0.005)
                    result = owner.result(OPERATION_ID)

                if stubborn:
                    self.assertEqual(result["status"], "unknown", result)
                    self.assertFalse(result["release_confirmed"])
                    self.assertFalse(result["replay_allowed"])
                    self.assertFalse(any(row.get("kind") == "recovery_up"
                                         for row in list(events)))
                    return

                self.assertEqual(result["status"], "recovered", result)
                self.assertTrue(result["release_confirmed"])
                self.assertFalse(result["replay_allowed"])
                self.assertFalse(raw_producer.is_alive())
                trace = list(events)
                exit_index = next(i for i, row in enumerate(trace)
                                  if row.get("kind") == "producer_exit_confirmed")
                up_index = next(i for i, row in enumerate(trace)
                                if row.get("kind") == "recovery_up")
                self.assertLess(exit_index, up_index, trace)
                self.assertFalse(state.get(VK_CONTROL, False))
                self.assertEqual(sum(row.get("kind") == "recovery_up" for row in trace), 1)
            finally:
                if supervisor is not None:
                    supervisor.close()
                if raw_producer.pid is not None:
                    if raw_producer.is_alive():
                        raw_producer.terminate()
                        raw_producer.join(2)
                    try:
                        raw_producer.close()
                    except ValueError:
                        pass
                for helper, receive, send in handles:
                    try:
                        if helper.is_alive():
                            helper.terminate()
                            helper.join(1)
                    except (OSError, ValueError):
                        pass
                    for endpoint in (receive, send):
                        try:
                            endpoint.close()
                        except OSError:
                            pass
                    try:
                        helper.close()
                    except (OSError, ValueError):
                        pass

    def test_actual_session_backend_block_before_acceptance_retires_before_recovery(self):
        self._run_case(accept_before_block=False)

    def test_actual_session_backend_acceptance_before_return_retires_before_recovery(self):
        self._run_case(accept_before_block=True)

    def test_actual_session_backend_retirement_timeout_stays_unknown(self):
        self._run_case(accept_before_block=True, stubborn=True)


if __name__ == "__main__":
    unittest.main()
