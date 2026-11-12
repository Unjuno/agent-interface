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
        # Nonzero successful up sample; zero now deliberately means unknown.
        return 0x8000 if vk in self.down else 1


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

    def test_query_exception_preserves_only_unknown_obligations(self):
        obj = self.make_backend({"Q": 81}, {"left"}, down=(81, 1), query_failure=1)
        with self.assertRaisesRegex(native.Win32BackendError,
                                    "key state query failed"):
            self.row(obj, obj.release_all)
        self.assertEqual(obj.user32.queries, [81, 1])
        self.assertEqual(obj.held_keys, {"Q": 81})
        self.assertEqual(obj.held_buttons, set())

    def test_send_exception_preserves_precheck_ledger(self):
        obj = self.make_backend({"Q": 81, "R": 82}, {"left"},
                                down=(81, 82, 1), send_failure=2)
        with self.assertRaisesRegex(native.Win32BackendError, "send failure") as caught:
            self.row(obj, obj.release_all)
        self.assertEqual([row["vk"] for row in obj.user32.sends], [81, 82, 1])
        self.assertEqual(set(obj.user32.queries), {81, 82, 1})
        self.assertEqual(caught.exception.release_attempt_errors, [{
            "domain": "key_up", "virtual_key": 82,
            "encoding": None, "error_type": "Win32BackendError"}])
        self.assertEqual(caught.exception.release_attempt_receipt["keys_down"], ["R"])
        attempts = caught.exception.release_attempt_receipt["release_attempts"]
        self.assertEqual([row["outcome"] for row in attempts],
                         ["returned", "raised", "returned"])
        self.assertTrue(attempts[1]["sendinput_call_started"])
        self.assertIsNone(attempts[1]["sendinput_return_count"])
        self.assertEqual(attempts[1]["sendinput_error_type"],
                         "Win32BackendError")
        self.assertEqual(obj.held_keys, {"R": 82})
        self.assertEqual(obj.held_buttons, set())
        sends_after_first_attempt = len(obj.user32.sends)
        retry = self.row(obj, obj.release_all)
        self.assertTrue(retry["verified"])
        self.assertEqual(obj.held_keys, {})
        self.assertEqual(obj.held_buttons, set())
        # Q and the button had neutral readbacks already, so retry only sends R.
        self.assertEqual(len(obj.user32.sends), sends_after_first_attempt + 1)

    def test_session_projects_failed_release_attempt_receipt(self):
        obj = self.make_backend({"Q": 81}, down=(81,), send_failure=1)
        session = Win32RuntimeSession(obj)
        program = {"schema": SCHEMA_PROGRAM, "program_id": "release-fails-once",
            "source": {"observation_seq": 7, "binding_revision": 3},
            "authority": {"lease_id": "inert-lease", "expires_at_ns": 100},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "release_all"}]}
        result = session.dispatch(program, current_observation_seq=7,
            current_binding_revision=3, now_ns=1)
        self.assertEqual(result["status"], "execution_failed")
        self.assertEqual(result["release_attempt_errors"], [{
            "domain": "key_up", "virtual_key": 81,
            "encoding": None, "error_type": "Win32BackendError"}])
        self.assertEqual(result["release_attempt_receipt"]["keys_down"], ["Q"])
        self.assertTrue(result["release"]["verified"])
        self.assertFalse(result["recovery_required"])

    def test_session_completion_keeps_successful_release_attempts(self):
        obj = self.make_backend({"Q": 81}, down=(81,))
        session = Win32RuntimeSession(obj)
        program = {"schema": SCHEMA_PROGRAM, "program_id": "release-receipt",
            "source": {"observation_seq": 7, "binding_revision": 3},
            "authority": {"lease_id": "inert-lease", "expires_at_ns": 100},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "release_all"}]}
        result = session.dispatch(program, current_observation_seq=7,
            current_binding_revision=3, now_ns=1)
        self.assertEqual(result["status"], "completed")
        release = result["execution"]["releases"][0]
        self.assertTrue(release["verified"])
        self.assertEqual(release["release_attempts"][0]["domain"], "key_up")
        self.assertTrue(release["release_attempts"][0]["sendinput_call_started"])
        self.assertEqual(release["release_attempts"][0]["sendinput_return_count"], 1)

    def test_session_recovery_returns_release_attempt_receipt(self):
        obj = self.make_backend({"Q": 81}, down=(81,), send_failure=1)
        session = Win32RuntimeSession(obj)
        session.recovery_required = True
        result = session.recover_input()
        self.assertEqual(result["status"], "recovery_failed")
        self.assertEqual(result["release_attempt_errors"], [{
            "domain": "key_up", "virtual_key": 81,
            "encoding": None, "error_type": "Win32BackendError"}])
        self.assertEqual(result["release_attempt_receipt"]["keys_down"], ["Q"])
        self.assertTrue(result["recovery_required"])

    def test_readback_error_does_not_skip_later_obligations(self):
        obj = self.make_backend({"Q": 81, "R": 82}, {"left"},
                                down=(81, 82, 1), query_failure=1)
        with self.assertRaisesRegex(native.Win32BackendError,
                                    "key state query failed") as caught:
            self.row(obj, obj.release_all)
        self.assertEqual(obj.user32.queries, [81, 82, 1])
        self.assertEqual(set(obj.user32.queries), {81, 82, 1})
        attempts = caught.exception.release_attempt_receipt["release_attempts"]
        self.assertEqual([row["outcome"] for row in attempts],
                         ["returned", "returned", "returned"])
        self.assertEqual([row["sendinput_return_count"] for row in attempts],
                         [1, 1, 1])
        self.assertEqual(obj.held_keys, {"Q": 81})
        self.assertEqual(obj.held_buttons, set())

    def test_query_error_does_not_replay_other_confirmed_neutral_keys(self):
        obj = self.make_backend({"Q": 81, "R": 82}, down=(81, 82),
                                query_failure=2)
        with self.assertRaisesRegex(native.Win32BackendError,
                                    "key state query failed"):
            self.row(obj, obj.release_all)
        self.assertEqual(obj.held_keys, {"R": 82})
        sends_after_first_attempt = len(obj.user32.sends)
        retry = self.row(obj, obj.release_all)
        self.assertTrue(retry["verified"])
        self.assertEqual(len(obj.user32.sends), sends_after_first_attempt + 1)
        self.assertEqual(obj.held_keys, {})

    def test_successful_unicode_up_is_not_replayed_after_state_query_error(self):
        obj = self.make_backend({"Q": 81}, down=(81,), query_failure=1)
        obj.pending_unicode_ups = set()
        obj.pending_unicode_ups.add(65)
        with self.assertRaisesRegex(native.Win32BackendError,
                                    "key state query failed") as caught:
            self.row(obj, obj.release_all)
        self.assertEqual(obj.pending_unicode_ups, set())
        attempts = caught.exception.release_attempt_receipt["release_attempts"]
        self.assertEqual([row["domain"] for row in attempts],
                         ["unicode_up", "key_up"])
        self.assertEqual(attempts[0]["outcome"], "returned")
        self.assertEqual(attempts[0]["sendinput_return_count"], 1)
        unicode_up_sends = [row for row in obj.user32.sends
            if row["vk"] == 0]
        self.assertEqual(len(unicode_up_sends), 1)

        obj.user32.query_failure = None
        recovered = self.row(obj, obj.release_all)
        self.assertTrue(recovered["verified"])
        self.assertEqual(obj.pending_unicode_ups, set())
        self.assertEqual(sum(row["vk"] == 0 for row in obj.user32.sends), 1)
        self.assertEqual([row["domain"]
            for row in recovered["release_attempts"]], ["key_up"])

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
        emissions_after_first = obj.emissions
        second = self.row(obj, lambda: dispatch("second"))
        self.assertEqual(first["status"], "release_unverified")
        self.assertEqual(second["status"], "refused")
        self.assertEqual(second["error"], "INPUT_RECOVERY_REQUIRED")
        self.assertEqual(obj.emissions, emissions_after_first)

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

    def test_successful_release_retains_each_sendinput_up_receipt(self):
        obj = self.make_backend({"Q": 81, "R": 82}, {"left"},
                                down=(81, 82, 1))
        receipt = self.row(obj, obj.release_all)
        self.assertTrue(receipt["verified"])
        self.assertEqual(receipt["release_attempts"], [
            {"ordinal": 0, "domain": "key_up", "virtual_key": 81,
             "key_names": ["Q"], "encoding": None,
             "sendinput_call_started": True, "sendinput_return_count": 1,
             "sendinput_error_type": None, "outcome": "returned",
             "error_type": None},
            {"ordinal": 1, "domain": "key_up", "virtual_key": 82,
             "key_names": ["R"], "encoding": None,
             "sendinput_call_started": True, "sendinput_return_count": 1,
             "sendinput_error_type": None, "outcome": "returned",
             "error_type": None},
            {"ordinal": 2, "domain": "button_up", "button": "left",
             "sendinput_call_started": True, "sendinput_return_count": 1,
             "sendinput_error_type": None, "outcome": "returned",
             "error_type": None},
        ])

    def test_zero_sendinput_return_is_retained_as_a_failed_attempt(self):
        obj = self.make_backend({"Q": 81}, down=(81,))
        obj.user32.SendInput = lambda _count, _items, _size: 0
        with patch.object(native.ctypes, "get_last_error", return_value=0,
                          create=True):
            with self.assertRaisesRegex(native.Win32BackendError,
                                        "SendInput failed") as caught:
                obj.release_all()
        attempts = caught.exception.release_attempt_receipt["release_attempts"]
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["outcome"], "raised")
        self.assertTrue(attempts[0]["sendinput_call_started"])
        self.assertEqual(attempts[0]["sendinput_return_count"], 0)
        self.assertIsNone(attempts[0]["sendinput_error_type"])
        self.assertEqual(attempts[0]["error_type"], "Win32BackendError")


if __name__ == "__main__":
    unittest.main()
