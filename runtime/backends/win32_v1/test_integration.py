from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from runtime.core_v1.contract import SCHEMA_PROGRAM, office_readiness
from runtime.backends.win32_v1.backend import Win32Backend, Win32BackendError, utf16_units, virtual_key
from runtime.backends.win32_v1.session import Win32RuntimeSession


def make_program(pid: str, *, seq=7, revision=3, expires=None, text="office", target="fixture", frame="window_client"):
    if expires is None:
        expires = time.monotonic_ns() + 30_000_000_000
    return {
        "schema": SCHEMA_PROGRAM,
        "program_id": pid,
        "source": {"observation_seq": seq, "binding_revision": revision},
        "authority": {"lease_id": "win32-integration", "expires_at_ns": expires},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "focus", "target": target},
            {"op": "pointer_move", "frame": frame, "x": 70, "y": 70},
            {"op": "pointer_button", "button": "left", "down": True},
            {"op": "pointer_button", "button": "left", "down": False},
            {"op": "wait_update", "timeout_ms": 50},
            {"op": "text", "text": text},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "wait_update", "timeout_ms": 80},
            {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 300, "h": 140},
            {"op": "release_all"},
        ],
    }


class PureWin32HelperTests(unittest.TestCase):
    def test_utf16_units(self):
        self.assertEqual(utf16_units("office"), tuple(ord(ch) for ch in "office"))
        self.assertEqual(utf16_units("😀"), (0xD83D, 0xDE00))
        with self.assertRaises(Win32BackendError):
            utf16_units("\ud800")

    def test_virtual_keys_fail_closed(self):
        self.assertEqual(virtual_key("CTRL"), 0x11)
        self.assertEqual(virtual_key("s"), ord("S"))
        with self.assertRaises(Win32BackendError):
            virtual_key("F13")


@unittest.skipUnless(sys.platform == "win32", "requires native Windows")
class Win32IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.meta = root / "meta.json"
        cls.effect = root / "effect.json"
        cls.events = root / "events.jsonl"
        cls.proc = subprocess.Popen([
            sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
            "--meta", str(cls.meta), "--effect", str(cls.effect), "--events", str(cls.events),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 10
        while time.time() < deadline and not cls.meta.exists():
            if cls.proc.poll() is not None:
                raise RuntimeError(f"fixture exited {cls.proc.returncode}: {cls.proc.stderr.read()}")
            time.sleep(0.05)
        if not cls.meta.exists():
            raise RuntimeError("fixture metadata timeout")
        hwnd = int(json.loads(cls.meta.read_text())["hwnd"])
        cls.backend = Win32Backend({"fixture": hwnd})
        cls.session = Win32RuntimeSession(cls.backend)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.backend.user32.PostMessageW(cls.backend.targets["fixture"], 0x0010, 0, 0)
        except Exception:
            pass
        try:
            cls.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            cls.proc.kill()
        cls.tmp.cleanup()

    def setUp(self):
        self.effect.unlink(missing_ok=True)

    def test_manifest_is_office_ready_with_explicit_boundary(self):
        manifest = self.backend.manifest()
        self.assertTrue(office_readiness(manifest)["ready"])
        self.assertEqual(manifest["platform"]["backend"], "win32")
        self.assertIn("Unicode", manifest["capabilities"]["input.text"]["detail"])

    def test_valid_program_has_independent_effect_capture_and_release(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("valid"), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "completed", row)
        self.assertGreater(self.backend.emissions, before)
        deadline = time.time() + 2
        while time.time() < deadline and not self.effect.exists():
            time.sleep(0.02)
        self.assertTrue(self.effect.exists(), self.events.read_text() if self.events.exists() else "no events")
        effect = json.loads(self.effect.read_text())
        self.assertEqual(effect, {"saved": True, "text": "office", "clicked": True})
        releases = row["execution"]["releases"]
        self.assertTrue(releases and releases[-1]["verified"])
        self.assertEqual(releases[-1]["keys_down"], [])
        self.assertEqual(releases[-1]["buttons_down"], [])
        self.assertEqual(len(row["execution"]["observations"]), 1)
        obs = row["execution"]["observations"][0]
        self.assertEqual(obs["bytes"], 300 * 140 * 4)
        self.assertEqual(len(obs["sha256"]), 64)

    def test_stale_observation_emits_zero_input(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("stale", seq=6), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["error"], "STALE_OBSERVATION")
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())

    def test_stale_binding_emits_zero_input(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("binding", revision=2), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["error"], "STALE_BINDING")
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())

    def test_expired_lease_emits_zero_input(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("expired", expires=1), current_observation_seq=7, current_binding_revision=3, now_ns=2)
        self.assertEqual(row["error"], "LEASE_EXPIRED")
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())

    def test_unknown_target_refuses_before_input(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("missing", target="missing"), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "refused")
        self.assertEqual(row["error"], "BACKEND_CONSTRAINT")
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())
        self.assertTrue(row["release"]["verified"])

    def test_invalid_unicode_refuses_before_input(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("bad-unicode", text="ok\ud800"), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "refused")
        self.assertEqual(row["error"], "BACKEND_CONSTRAINT")
        self.assertIn("surrogate", row["detail"])
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())

    def test_unsupported_coordinate_frame_refuses_in_core(self):
        before = self.backend.emissions
        row = self.session.dispatch(make_program("logical", frame="screen_logical"), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "refused")
        self.assertEqual(row["error"], "COORDINATE_UNSUPPORTED")
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())


if __name__ == "__main__":
    unittest.main()
