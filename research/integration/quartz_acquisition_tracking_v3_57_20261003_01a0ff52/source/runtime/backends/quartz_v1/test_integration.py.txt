from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from runtime.core_v1.contract import SCHEMA_PROGRAM, office_readiness
from runtime.backends.quartz_v1.backend import QuartzBackend, QuartzBackendError, key_code, manifest_for_permissions, utf16_units
from runtime.backends.quartz_v1.session import QuartzRuntimeSession


def program(pid, ops, *, seq=7, revision=3, expires=None):
    if expires is None:
        expires = time.monotonic_ns() + 30_000_000_000
    return {
        "schema": SCHEMA_PROGRAM,
        "program_id": pid,
        "source": {"observation_seq": seq, "binding_revision": revision},
        "authority": {"lease_id": "quartz-integration", "expires_at_ns": expires},
        "terminal": {"release_all_required": True},
        "ops": ops + [{"op": "release_all"}],
    }


def valid(pid="valid"):
    return program(pid, [
        {"op": "focus", "target": "fixture"},
        {"op": "text", "text": "office"},
        {"op": "wait_update", "timeout_ms": 80},
        {"op": "observe", "frame": "screen_physical_px", "x": 0, "y": 0, "w": 200, "h": 120},
        {"op": "key_chord", "keys": ["ENTER"]},
        {"op": "wait_update", "timeout_ms": 180},
    ])


class PureQuartzTests(unittest.TestCase):
    def test_encoding_and_keys(self):
        self.assertEqual(utf16_units("office"), tuple(ord(x) for x in "office"))
        self.assertEqual(utf16_units("😀"), (0xD83D, 0xDE00))
        self.assertEqual(key_code("ENTER"), 36)
        with self.assertRaises(QuartzBackendError):
            utf16_units("\ud800")
        with self.assertRaises(QuartzBackendError):
            key_code("F13")

    def test_permission_manifests_fail_closed(self):
        row = manifest_for_permissions(False, False)
        self.assertEqual(row["capabilities"]["capture.frame"]["state"], "permission_required")
        self.assertEqual(row["capabilities"]["input.keyboard"]["state"], "permission_required")
        ready = manifest_for_permissions(True, True)
        self.assertTrue(office_readiness(ready)["ready"])


@unittest.skipUnless(sys.platform == "darwin", "requires native macOS")
class QuartzIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.meta = root / "meta.json"
        cls.effect = root / "effect.json"
        cls.events = root / "events.jsonl"
        cls.proc = subprocess.Popen([
            sys.executable, "-m", "runtime.backends.quartz_v1.fixture_app",
            "--meta", str(cls.meta), "--effect", str(cls.effect), "--events", str(cls.events),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 10
        while time.time() < deadline and not cls.meta.exists():
            if cls.proc.poll() is not None:
                raise RuntimeError(f"fixture exited {cls.proc.returncode}: {cls.proc.stderr.read()}")
            time.sleep(0.05)
        if not cls.meta.exists():
            raise RuntimeError("fixture metadata timeout")
        pid = int(json.loads(cls.meta.read_text())["pid"])
        cls.backend = QuartzBackend({"fixture": pid})
        cls.session = QuartzRuntimeSession(cls.backend)
        time.sleep(0.25)

    @classmethod
    def tearDownClass(cls):
        if cls.proc.poll() is None:
            cls.proc.terminate()
        try:
            cls.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            cls.proc.kill()
        cls.tmp.cleanup()

    def setUp(self):
        self.effect.unlink(missing_ok=True)

    def test_actual_permissions_and_manifest(self):
        self.assertTrue(self.backend.accessibility_granted)
        self.assertTrue(self.backend.screen_recording_granted)
        self.assertTrue(office_readiness(self.backend.manifest())["ready"])

    def test_expired_lease_zero_events(self):
        before = self.backend.emissions
        row = self.session.dispatch(
            program("expired", [{"op": "focus", "target": "fixture"}], expires=1),
            current_observation_seq=7, current_binding_revision=3, now_ns=2,
        )
        self.assertEqual(row["error"], "LEASE_EXPIRED")
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())

    def test_invalid_unicode_zero_events(self):
        before = self.backend.emissions
        row = self.session.dispatch(
            program("bad", [{"op": "focus", "target": "fixture"}, {"op": "text", "text": "ok\ud800"}]),
            current_observation_seq=7, current_binding_revision=3,
        )
        self.assertEqual(row["error"], "BACKEND_CONSTRAINT")
        self.assertEqual(self.backend.emissions, before)
        self.assertFalse(self.effect.exists())

    def test_pointer_move_has_physical_readback(self):
        row = self.session.dispatch(
            program("pointer", [
                {"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "frame": "screen_physical_px", "x": 40, "y": 40},
                {"op": "wait_update", "timeout_ms": 40},
            ]),
            current_observation_seq=7, current_binding_revision=3,
        )
        self.assertEqual(row["status"], "completed", row)
        x, y = self.backend.pointer_position()
        self.assertLessEqual(abs(x - 40), 2)
        self.assertLessEqual(abs(y - 40), 2)
        self.assertTrue(row["execution"]["releases"][-1]["verified"])

    def test_stale_binding_zero_events(self):
        before = self.backend.emissions
        row = self.session.dispatch(valid("binding"), current_observation_seq=7, current_binding_revision=2)
        self.assertEqual(row["error"], "STALE_BINDING")
        self.assertEqual(self.backend.emissions, before)

    def test_stale_observation_zero_events(self):
        before = self.backend.emissions
        row = self.session.dispatch(valid("stale"), current_observation_seq=6, current_binding_revision=3)
        self.assertEqual(row["error"], "STALE_OBSERVATION")
        self.assertEqual(self.backend.emissions, before)

    def test_unknown_target_zero_events(self):
        before = self.backend.emissions
        row = self.session.dispatch(
            program("missing", [{"op": "focus", "target": "missing"}]),
            current_observation_seq=7, current_binding_revision=3,
        )
        self.assertEqual(row["error"], "BACKEND_CONSTRAINT")
        self.assertEqual(self.backend.emissions, before)
        self.assertTrue(row["release"]["verified"])

    def test_unsupported_frame_core_refusal(self):
        before = self.backend.emissions
        row = self.session.dispatch(
            program("logical", [
                {"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "frame": "screen_logical", "x": 1, "y": 1},
            ]),
            current_observation_seq=7, current_binding_revision=3,
        )
        self.assertEqual(row["error"], "COORDINATE_UNSUPPORTED")
        self.assertEqual(self.backend.emissions, before)

    def test_valid_dialog_effect_capture_and_release(self):
        row = self.session.dispatch(valid(), current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "completed", row)
        deadline = time.time() + 3
        while time.time() < deadline and not self.effect.exists():
            time.sleep(0.02)
        self.assertTrue(self.effect.exists(), self.events.read_text() if self.events.exists() else "no events")
        effect = json.loads(self.effect.read_text())
        self.assertEqual(effect["text"], "office")
        self.assertTrue(effect["accepted"])
        obs = row["execution"]["observations"][0]
        self.assertEqual((obs["width"], obs["height"]), (200, 120))
        self.assertGreater(obs["bytes"], 0)
        self.assertEqual(len(obs["sha256"]), 64)
        self.assertTrue(row["execution"]["releases"][-1]["verified"])
        self.assertEqual(row["execution"]["releases"][-1]["keys_down"], [])
        self.assertEqual(row["execution"]["releases"][-1]["buttons_down"], [])


if __name__ == "__main__":
    unittest.main()
