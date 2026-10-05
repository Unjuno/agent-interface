"""Synthetic focus-drift regression using an inert SendInput endpoint."""
import unittest

from runtime.backends.win32_v1.backend import Win32Backend
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM


class FocusRacingUser32:
    def __init__(self, *, steal_focus_on_down=False, race_after_focus_check=True):
        self.foreground = 1001
        self.target = 1001
        self.race_after_focus_check = False
        self.steal_focus_on_down = steal_focus_on_down
        self.race_after_focus_check_enabled = race_after_focus_check
        self.sent = []

    def IsWindow(self, hwnd):
        return hwnd in (1001, 2002)

    def ShowWindow(self, *_args):
        return 1

    def BringWindowToTop(self, *_args):
        return 1

    def SetForegroundWindow(self, hwnd):
        self.target = hwnd
        self.foreground = hwnd
        self.race_after_focus_check = True
        return 1

    def GetForegroundWindow(self):
        if self.race_after_focus_check:
            self.race_after_focus_check = False
            verified = self.target
            if self.race_after_focus_check_enabled:
                self.foreground = 2002
            return verified
        return self.foreground

    def GetAsyncKeyState(self, _vk):
        return 0

    def SendInput(self, _count, inputs, _size):
        item = inputs[0]
        down = not bool(item.ki.dwFlags & 0x0002)
        self.sent.append({
            "vk": int(item.ki.wVk),
            "down": down,
            "foreground": self.foreground,
        })
        if self.steal_focus_on_down and down:
            self.foreground = 2002
        return 1


class FocusDriftTests(unittest.TestCase):
    def make_backend(self, **user32_options):
        backend = Win32Backend.__new__(Win32Backend)
        backend.user32 = FocusRacingUser32(**user32_options)
        backend.targets = {"fixture": 1001}
        backend.emissions = 0
        backend.held_keys = {}
        backend._active_key_holds = {}
        backend._retained_key_holds = {}
        backend._hold_sequence = 0
        backend._backend_instance_id = "focus-drift-test"
        backend._current_input_transitions = None
        backend._current_program_id = None
        backend._current_operation_index = None
        backend._current_admitted_ns = None
        backend.last_input_transitions = []
        backend.held_buttons = set()
        backend.pending_unicode_ups = set()
        return backend

    def test_key_down_is_refused_if_foreground_changes_after_focus_check(self):
        backend = self.make_backend()
        program = {
            "program_id": "focus-drift",
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "key_state", "key": "Q", "down": True},
                {"op": "release_all"},
            ],
        }

        program.update({
            "schema": SCHEMA_PROGRAM,
            "source": {"observation_seq": 7, "binding_revision": 3},
            "authority": {
                "lease_id": "focus-drift-test",
                "expires_at_ns": 9000000000000000000,
            },
            "terminal": {"release_all_required": True},
        })
        reply = Win32RuntimeSession(backend).dispatch(
            program,
            current_observation_seq=7,
            current_binding_revision=3,
            now_ns=1,
        )

        self.assertEqual(reply["status"], "execution_failed", reply)
        self.assertIn("foreground focus changed", reply["detail"])
        self.assertTrue(reply["release"]["verified"])
        self.assertFalse(any(row["down"] for row in backend.user32.sent))
        self.assertEqual(backend.held_keys, {})

    def test_focus_loss_after_down_stops_normal_up_but_allows_cleanup(self):
        backend = self.make_backend(
            steal_focus_on_down=True, race_after_focus_check=False)
        program = {
            "program_id": "focus-lost-held-key",
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "key_state", "key": "Q", "down": True},
                {"op": "key_state", "key": "Q", "down": False},
                {"op": "release_all"},
            ],
            "schema": SCHEMA_PROGRAM,
            "source": {"observation_seq": 7, "binding_revision": 3},
            "authority": {
                "lease_id": "focus-drift-test",
                "expires_at_ns": 9000000000000000000,
            },
            "terminal": {"release_all_required": True},
        }

        reply = Win32RuntimeSession(backend).dispatch(
            program,
            current_observation_seq=7,
            current_binding_revision=3,
            now_ns=1,
        )

        self.assertEqual(reply["status"], "execution_failed", reply)
        self.assertIn("foreground focus changed", reply["detail"])
        self.assertTrue(reply["release"]["verified"])
        rows = reply["input_transitions"]
        self.assertEqual(
            [(row["operation"], row["cleanup"]) for row in rows],
            [("down", False), ("up", True)],
        )
        self.assertEqual(backend.user32.foreground, 2002)
        self.assertEqual(backend.held_keys, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
