"""Recovery and admission behavior while a Win32 input call is unresolved."""
import threading
import time
import unittest

from runtime.backends.win32_v1.backend import (
    INPUT_KEYBOARD, KEYEVENTF_KEYUP, VK_CONTROL, Win32Backend,
)
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM


class BlockingSendInput:
    def __init__(self, accept_before_block):
        self.accept_before_block = accept_before_block
        self.down = set()
        self.events = []
        self.entered = threading.Event()
        self.resume = threading.Event()

    def SendInput(self, count, inputs, size):
        self.assert_keyboard_input(count, inputs)
        item = inputs[0]
        vk = int(item.ki.wVk)
        is_down = not bool(int(item.ki.dwFlags) & KEYEVENTF_KEYUP)
        if is_down and not self.entered.is_set():
            self.events.append("down_entered")
            if self.accept_before_block:
                self.down.add(vk)
                self.events.append("down_accepted")
            self.entered.set()
            if not self.resume.wait(5):
                raise TimeoutError("input barrier expired")
            if not self.accept_before_block:
                self.down.add(vk)
                self.events.append("down_accepted")
        elif is_down:
            self.down.add(vk)
            self.events.append("down_accepted")
        else:
            self.down.discard(vk)
            self.events.append("up")
        return 1

    @staticmethod
    def assert_keyboard_input(count, inputs):
        if count != 1 or inputs[0].type != INPUT_KEYBOARD:
            raise AssertionError("expected one keyboard input")

    def GetAsyncKeyState(self, vk):
        return 0x8000 if vk in self.down else 1


def make_session(api):
    backend = Win32Backend.__new__(Win32Backend)
    backend.targets = {}
    backend.held_keys = {}
    backend.held_key_targets = {}
    backend.held_buttons = set()
    backend.held_button_targets = {}
    backend.focused_target = None
    backend.pending_unicode_ups = set()
    backend.emissions = 0
    backend._last_state_query_witness = []
    backend.user32 = api
    backend.monotonic_ns = time.monotonic_ns
    backend._key_down_state = lambda vk, target: vk in api.down
    session = Win32RuntimeSession(backend)
    program = {
        "schema": SCHEMA_PROGRAM,
        "program_id": "inflight-sendinput",
        "source": {"observation_seq": 1, "binding_revision": 1},
        "authority": {"lease_id": "inflight-test",
                      "expires_at_ns": time.monotonic_ns() + 10_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "key_state", "key": "CTRL", "down": True},
            {"op": "release_all"},
        ],
    }
    return session, backend, program


class InflightRecoveryTests(unittest.TestCase):
    def run_blocked_case(self, *, accept_before_block):
        api = BlockingSendInput(accept_before_block)
        session, backend, program = make_session(api)
        dispatched = []
        producer = threading.Thread(target=lambda: dispatched.append(
            session.dispatch(program, current_observation_seq=1,
                             current_binding_revision=1)))
        producer.start()
        self.assertTrue(api.entered.wait(2), "SendInput did not reach the barrier")
        self.assertEqual(api.down == {VK_CONTROL}, accept_before_block)
        before_recovery = list(api.events)
        try:
            recovery = session.recover_input()

            self.assertEqual(recovery["status"], "pending", recovery)
            self.assertEqual(recovery["error"], "INPUT_PRODUCER_UNRESOLVED")
            self.assertFalse(recovery["release_attempted"])
            self.assertTrue(recovery["recovery_required"])
            self.assertEqual(api.events, before_recovery)
            self.assertEqual(api.down == {VK_CONTROL}, accept_before_block)

            overlap = session.dispatch(program, current_observation_seq=1,
                                       current_binding_revision=1)
            self.assertEqual(overlap["status"], "pending", overlap)
            self.assertEqual(overlap["error"], "INPUT_PRODUCER_UNRESOLVED")
            self.assertFalse(overlap["input_dispatched"])
            self.assertFalse(overlap["release_attempted"])
            self.assertFalse(overlap["replay_allowed"])
            self.assertEqual(api.events, before_recovery)
        finally:
            api.resume.set()
            producer.join(3)
        self.assertFalse(producer.is_alive(), "producer did not finish after resume")
        self.assertEqual(len(dispatched), 1)
        self.assertEqual(dispatched[0]["status"], "completed", dispatched[0])
        self.assertEqual(api.events.count("down_accepted"), 1)
        self.assertEqual(api.events.count("up"), 1)
        self.assertLess(api.events.index("down_accepted"), api.events.index("up"))
        self.assertEqual(api.down, set())
        self.assertFalse(session.recovery_required)
        self.assertEqual(session.recover_input()["error"],
                         "INPUT_RECOVERY_NOT_REQUIRED")
        self.assertEqual(backend.held_keys, {})

    def test_recovery_and_overlapping_dispatch_wait_for_accepted_down_return(self):
        self.run_blocked_case(accept_before_block=True)

    def test_recovery_and_overlapping_dispatch_wait_for_preacceptance_block(self):
        self.run_blocked_case(accept_before_block=False)


if __name__ == "__main__":
    unittest.main()
