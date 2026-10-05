"""Ordinary fault regressions: real methods, inert API and no desktop input."""
import json
import unittest
from unittest.mock import patch

from runtime.backends.win32_v1 import backend as native
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM


class InertAPI:
    def __init__(self, down=(), *, stubborn=(), send_failure=None, query_failure=None):
        self.down = set(down)
        self.stubborn = set(stubborn)
        self.send_failure = send_failure
        self.query_failure = query_failure
        self.sends = []
        self.queries = []

    def SendInput(self, count, items, size):
        item = items[0]
        if item.type == native.INPUT_KEYBOARD:
            vk = int(item.ki.wVk)
            up = bool(item.ki.dwFlags & native.KEYEVENTF_KEYUP)
        else:
            match = [(vk, bool(item.mi.dwFlags & up))
                     for _, up, vk in native.BUTTON_FLAGS.values()
                     if item.mi.dwFlags & up]
            if len(match) != 1:
                raise AssertionError("only known button-UP emissions allowed")
            vk, up = match[0]
        if count != 1 or not up:
            raise AssertionError("only single UP emissions allowed")
        self.sends.append({"vk": vk, "up": up})
        if len(self.sends) == self.send_failure:
            raise native.Win32BackendError("inert send failure")
        if vk not in self.stubborn:
            self.down.discard(vk)
        return 1

    def GetAsyncKeyState(self, vk):
        self.queries.append(vk)
        if len(self.queries) == self.query_failure:
            raise RuntimeError("inert query unavailable")
        return 0x8000 if vk in self.down else 0


class ReleaseLedgerTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(native.Win32Backend, "__init__",
                                      side_effect=AssertionError("constructor forbidden")))
        self.enterContext(patch.object(native.ctypes, "WinDLL", create=True,
                                      side_effect=AssertionError("WinDLL forbidden")))
        self.enterContext(patch.object(native.time, "sleep", return_value=None))

    def make_backend(self, keys=None, buttons=None, **api_options):
        obj = native.Win32Backend.__new__(native.Win32Backend)
        obj.held_keys = dict(keys or {})
        obj.held_buttons = set(buttons or ())
        obj.emissions = 0
        obj.user32 = InertAPI(**api_options)
        return obj

    def row(self, obj, call):
        try:
            value = call()
        except Exception as error:
            self.log(obj, {"exception": type(error).__name__, "detail": str(error)})
            raise
        self.log(obj, value)
        return value

    def log(self, obj, value):
        print(json.dumps({"test": self.id(), "value": value,
                          "held_keys": obj.held_keys,
                          "held_buttons": sorted(obj.held_buttons),
                          "api_down": sorted(obj.user32.down),
                          "sends": obj.user32.sends,
                          "queries": obj.user32.queries}, sort_keys=True))

    def test_persistent_down_does_not_become_neutral_on_second_call(self):
        obj = self.make_backend({"Q": 81}, {"left"}, down=(81, 1), stubborn=(81, 1))
        first = self.row(obj, obj.release_all)
        second = self.row(obj, obj.release_all)
        self.assertFalse(first["verified"])
        self.assertFalse(second["verified"])
        self.assertEqual(second["keys_down"], ["Q"])
        self.assertEqual(second["buttons_down"], ["left"])
        self.assertEqual(obj.held_keys, {"Q": 81})
        self.assertEqual(obj.held_buttons, {"left"})

    def test_mixed_up_down_retires_only_confirmed_up_obligations(self):
        obj = self.make_backend({"Q": 81, "R": 82}, {"left", "right"},
                                down=(81, 82, 1, 2), stubborn=(81, 1))
        first = self.row(obj, obj.release_all)
        self.assertFalse(first["verified"])
        self.assertEqual(obj.held_keys, {"Q": 81})
        self.assertEqual(obj.held_buttons, {"left"})

    def test_later_neutral_confirmation_retires_retained_obligations(self):
        obj = self.make_backend({"Q": 81}, {"left"}, down=(81, 1), stubborn=(81, 1))
        first = self.row(obj, obj.release_all)
        first_ledger = (dict(obj.held_keys), set(obj.held_buttons))
        obj.user32.stubborn.clear()
        second = self.row(obj, obj.release_all)
        self.assertFalse(first["verified"])
        self.assertEqual(first_ledger, ({"Q": 81}, {"left"}))
        self.assertTrue(second["verified"])
        self.assertEqual(obj.held_keys, {})
        self.assertEqual(obj.held_buttons, set())
        self.assertEqual(len(obj.user32.sends), 4)

    def test_query_exception_preserves_precheck_ledger(self):
        # The best-effort per-key pre-sample is query 1; fail the strict
        # post-UP neutral-state read on query 2.
        obj = self.make_backend({"Q": 81}, {"left"}, down=(81, 1), query_failure=2)
        with self.assertRaisesRegex(RuntimeError, "query unavailable"):
            self.row(obj, obj.release_all)
        self.assertEqual(obj.held_keys, {"Q": 81})
        self.assertEqual(obj.held_buttons, {"left"})

    def test_per_key_pre_sample_failure_does_not_block_safety_up(self):
        obj = self.make_backend({"Q": 81}, down=(81,), query_failure=1)
        obj._retained_key_holds = {"Q": "hold-q"}
        receipt = self.row(obj, obj.release_all)
        self.assertTrue(receipt["verified"])
        self.assertEqual(obj.user32.down, set())
        transition = obj.last_input_transitions[-1]
        self.assertEqual(transition["operation"], "up")
        self.assertEqual(transition["os_key_state_classification"],
                         "OS_KEY_STATE_UNAVAILABLE")
        self.assertFalse(transition["state_before"]["available"])
        self.assertFalse(transition["state_after"]["down"])

    def test_send_exception_preserves_precheck_ledger(self):
        obj = self.make_backend({"Q": 81, "R": 82}, {"left"},
                                down=(81, 82, 1), send_failure=2)
        with self.assertRaisesRegex(native.Win32BackendError, "send failure"):
            self.row(obj, obj.release_all)
        self.assertEqual(obj.held_keys, {"Q": 81, "R": 82})
        self.assertEqual(obj.held_buttons, {"left"})

    def test_session_does_not_complete_after_previous_unverified_release(self):
        obj = self.make_backend({"Q": 81}, {"left"}, down=(81, 1), stubborn=(81, 1))
        session = Win32RuntimeSession(obj)
        def dispatch(pid):
            program = {"schema": SCHEMA_PROGRAM, "program_id": pid,
                       "source": {"observation_seq": 7, "binding_revision": 3},
                       "authority": {"lease_id": "inert-lease", "expires_at_ns": 100},
                       "terminal": {"release_all_required": True},
                       "ops": [{"op": "release_all"}]}
            return session.dispatch(program, current_observation_seq=7,
                                    current_binding_revision=3, now_ns=1)
        first = self.row(obj, lambda: dispatch("first"))
        second = self.row(obj, lambda: dispatch("second"))
        self.assertEqual(first["status"], "release_unverified")
        self.assertEqual(second["status"], "release_unverified")

    def test_confirmed_up_and_empty_controls_verify_without_unrelated_scan(self):
        obj = self.make_backend({"Q": 81}, {"left"}, down=(81, 1, 90))
        first = self.row(obj, obj.release_all)
        self.assertTrue(first["verified"])
        self.assertEqual(set(obj.user32.queries), {81, 1})
        self.assertEqual(obj.user32.down, {90})
        obj.user32.queries.clear()
        second = self.row(obj, obj.release_all)
        self.assertTrue(second["verified"])
        self.assertEqual(obj.user32.queries, [])


if __name__ == "__main__":
    unittest.main()
