"""Synthetic focus-drift regression using an inert SendInput endpoint."""
import unittest
import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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


@unittest.skipUnless(sys.platform == "win32", "requires native Windows")
class NativeForegroundFenceTests(unittest.TestCase):
    """Exercise the focus fence with real HWNDs, without emitting OS input."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.processes = []
        self.paths = {}
        for name in ("decoy", "target"):
            folder = self.root / name
            folder.mkdir()
            paths = {
                key: folder / f"{key}.json"
                for key in ("meta", "effect", "events")
            }
            command = [
                sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
                "--meta", str(paths["meta"]), "--effect", str(paths["effect"]),
                "--events", str(paths["events"]),
            ]
            if name == "target":
                decoy_meta = self.paths["decoy"]["meta"]
                command.extend([
                    "--switch-to",
                    str(json.loads(decoy_meta.read_text())["hwnd"]),
                ])
            proc = subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
            )
            self.processes.append((proc, paths))
            self.paths[name] = paths
            if name == "decoy":
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline and not paths["meta"].exists():
                    if proc.poll() is not None:
                        self.fail(f"fixture exited {proc.returncode}: {proc.stderr.read()}")
                    time.sleep(0.02)
                self.assertTrue(paths["meta"].exists(), "decoy fixture metadata timeout")
        target_proc, target_paths = self.processes[-1]
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not target_paths["meta"].exists():
            if target_proc.poll() is not None:
                self.fail(f"fixture exited {target_proc.returncode}: {target_proc.stderr.read()}")
            time.sleep(0.02)
        self.assertTrue(target_paths["meta"].exists(), "target fixture metadata timeout")
        self.target_hwnd = int(json.loads(self.paths["target"]["meta"].read_text())["hwnd"])
        self.decoy_hwnd = int(json.loads(self.paths["decoy"]["meta"].read_text())["hwnd"])
        self.backend = Win32Backend({"fixture": self.target_hwnd})
        self.session = Win32RuntimeSession(self.backend)
        self.control_user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.control_user32.PostMessageW.argtypes = [
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t
        ]
        self.control_user32.PostMessageW.restype = ctypes.c_int

    def tearDown(self):
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        for _proc, paths in self.processes:
            try:
                if paths["meta"].exists():
                    hwnd = int(json.loads(paths["meta"].read_text())["hwnd"])
                    user32.PostMessageW(hwnd, 0x0010, 0, 0)
            except Exception:
                pass
        for proc, _paths in self.processes:
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        self.tmp.cleanup()

    def test_native_focus_change_after_focus_refuses_before_sendinput(self):
        program = {
            "schema": SCHEMA_PROGRAM,
            "program_id": "native-focus-drift",
            "source": {"observation_seq": 7, "binding_revision": 3},
            "authority": {
                "lease_id": "native-focus-drift",
                "expires_at_ns": time.monotonic_ns() + 30_000_000_000,
            },
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "key_state", "key": "Q", "down": True},
                {"op": "release_all"},
            ],
        }
        original_focus = self.backend.focus
        swaps = []

        def focus_then_switch(target):
            original_focus(target)
            posted = bool(self.control_user32.PostMessageW(
                self.target_hwnd, 0x8001, 0, 0
            ))
            deadline = time.monotonic() + 3
            foreground = 0
            while time.monotonic() < deadline:
                foreground = int(self.backend.user32.GetForegroundWindow() or 0)
                if foreground == self.decoy_hwnd:
                    break
                time.sleep(0.01)
            swaps.append({"message_posted": posted, "foreground": foreground})

        self.backend.focus = focus_then_switch
        send_calls = []

        def forbidden_sendinput(*_args):
            send_calls.append("called")
            return 0

        self.backend.user32.SendInput = forbidden_sendinput
        reply = self.session.dispatch(
            program, current_observation_seq=7, current_binding_revision=3
        )

        raw = {
            "target_hwnd": self.target_hwnd,
            "decoy_hwnd": self.decoy_hwnd,
            "foreground_switch": swaps,
            "reply": reply,
            "sendinput_calls": send_calls,
            "target_effect_exists": self.paths["target"]["effect"].exists(),
            "decoy_effect_exists": self.paths["decoy"]["effect"].exists(),
            "target_events": self.paths["target"]["events"].read_text().splitlines(),
            "decoy_events": self.paths["decoy"]["events"].read_text().splitlines(),
        }
        raw_path = os.environ.get("AI_FOCUS_DRIFT_RAW")
        if raw_path:
            Path(raw_path).write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")

        self.assertEqual(swaps, [{"message_posted": True, "foreground": self.decoy_hwnd}])
        self.assertEqual(reply["status"], "execution_failed", reply)
        self.assertIn("foreground focus changed", reply["detail"])
        self.assertEqual(send_calls, [])
        self.assertTrue(reply["release"]["verified"], reply)
        self.assertEqual(reply["input_transitions"], [])
        self.assertFalse(self.paths["target"]["effect"].exists())
        self.assertFalse(self.paths["decoy"]["effect"].exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
