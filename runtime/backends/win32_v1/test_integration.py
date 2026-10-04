from __future__ import annotations

import ctypes
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



class CaptureContractDLL:
    """Fake GDI enforces the documented deselection and deletion preconditions."""

    def __init__(self, fault=None):
        self.fault = fault
        self.selected = 9
        self.events = []

    def GetDC(self, hwnd):
        return 1

    def CreateCompatibleDC(self, dc):
        return 2

    def CreateCompatibleBitmap(self, dc, width, height):
        return 3

    def SelectObject(self, dc, bitmap):
        self.events.append("select" if bitmap == 3 else "restore")
        if bitmap == 3 and self.fault in {"select_zero", "select_error"}:
            return 0 if self.fault == "select_zero" else ctypes.c_void_p(-1).value
        if bitmap == 9 and self.fault in {"restore_zero", "restore_error"}:
            fault, self.fault = self.fault, None
            return 0 if fault == "restore_zero" else ctypes.c_void_p(-1).value
        previous, self.selected = self.selected, bitmap
        return previous

    def PrintWindow(self, hwnd, dc, flags):
        assert self.selected == 3
        return self.fault != "draw"

    def BitBlt(self, *args):
        assert self.selected == 3
        return self.fault != "draw"

    def GetDIBits(self, dc, bitmap, start, height, buffer, info, usage):
        self.events.append("read")
        assert self.selected != bitmap, "GetDIBits bitmap is still selected"
        if self.fault == "rows":
            return height - 1
        buffer.raw = bytes(range(len(buffer)))
        return height

    def DeleteObject(self, bitmap):
        assert self.selected != bitmap, "deleting selected bitmap"
        self.events.append("delete_bitmap")
        return 1

    def DeleteDC(self, dc):
        self.events.append("delete_dc")
        return 1

    def ReleaseDC(self, hwnd, dc):
        self.events.append("release_dc")
        return 1


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



    def capture_contract_backend(self, fault=None):
        backend = object.__new__(Win32Backend)
        dll = CaptureContractDLL(fault)
        backend.gdi32 = backend.user32 = dll
        return backend, dll

    def test_capture_initial_selection_failure_prevents_drawing(self):
        for print_window in (True, False):
            for fault in ("select_zero", "select_error"):
                with self.subTest(print_window=print_window, fault=fault):
                    backend, dll = self.capture_contract_backend(fault)
                    with self.assertRaisesRegex(Win32BackendError, "bitmap selection failed"):
                        backend._capture_hdc(7, 0, 0, 2, 2, print_window=print_window)
                    self.assertEqual(dll.selected, 9)
                    self.assertEqual(dll.events, ["select", "delete_bitmap", "delete_dc", "release_dc"])

    def test_capture_deselects_before_readout(self):
        for print_window in (True, False):
            with self.subTest(print_window=print_window):
                backend, dll = self.capture_contract_backend()
                raw = backend._capture_hdc(7, 0, 0, 2, 2, print_window=print_window)
                self.assertEqual(raw, bytes(range(16)))
                self.assertLess(dll.events.index("restore"), dll.events.index("read"))
                self.assertEqual(dll.events.count("restore"), 1)
                self.assertEqual(dll.selected, 9)
                self.assertEqual(dll.events[-3:], ["delete_bitmap", "delete_dc", "release_dc"])

    def test_capture_failures_release_resources(self):
        for print_window in (True, False):
            for fault in ("draw", "rows"):
                with self.subTest(print_window=print_window, fault=fault):
                    backend, dll = self.capture_contract_backend(fault)
                    with self.assertRaises(Win32BackendError):
                        backend._capture_hdc(7, 0, 0, 2, 2, print_window=print_window)
                    self.assertEqual(dll.selected, 9)
                    self.assertEqual(dll.events[-3:], ["delete_bitmap", "delete_dc", "release_dc"])

    def test_capture_failed_deselection_prevents_readout(self):
        for print_window in (True, False):
            for fault in ("restore_zero", "restore_error"):
                with self.subTest(print_window=print_window, fault=fault):
                    backend, dll = self.capture_contract_backend(fault)
                    with self.assertRaisesRegex(Win32BackendError, "deselection failed"):
                        backend._capture_hdc(7, 0, 0, 2, 2, print_window=print_window)
                    self.assertNotIn("read", dll.events)
                    self.assertEqual(dll.events.count("restore"), 2)
                    self.assertEqual(dll.selected, 9)
                    self.assertEqual(dll.events[-3:], ["delete_bitmap", "delete_dc", "release_dc"])


    def _unicode_delivery_backend(self,failures=()):
        trace=[];failures=set(failures)
        b=Win32Backend.__new__(Win32Backend)
        b.held_keys={};b.held_buttons=set();b.pending_unicode_ups=set()
        def send(unit,down):
            trace.append((unit,down))
            if len(trace) in failures:raise Win32BackendError('injected send failure')
        b._send_unicode_unit=send
        return b,trace
    def test_unicode_delivery_healthy(self):
        b,t=self._unicode_delivery_backend();b.text('AA');self.assertEqual(t,[(65,True),(65,False)]*2);self.assertEqual(b.pending_unicode_ups,set())
    def test_unicode_delivery_down_failure(self):
        b,t=self._unicode_delivery_backend((1,));self.assertRaises(Win32BackendError,b.text,'A');self.assertEqual(b.pending_unicode_ups,set())
    def test_unicode_delivery_up_failure_and_compensation(self):
        b,t=self._unicode_delivery_backend((2,));self.assertRaises(Win32BackendError,b.text,'A');self.assertEqual(b.pending_unicode_ups,{65});b.release_all();self.assertEqual(t,[(65,True),(65,False),(65,False)]);self.assertEqual(b.pending_unicode_ups,set())
    def test_unicode_delivery_compensation_failure_retains(self):
        b,t=self._unicode_delivery_backend((2,3));self.assertRaises(Win32BackendError,b.text,'A');self.assertRaises(Win32BackendError,b.release_all);self.assertEqual(b.pending_unicode_ups,{65});self.assertEqual(len(t),3)
    def test_unicode_delivery_pending_refuses_new_text(self):
        b,t=self._unicode_delivery_backend();b.pending_unicode_ups.add(65);self.assertRaises(Win32BackendError,b.text,'B');self.assertEqual(t,[])
    def test_unicode_delivery_surrogate_first_unit_failure_stops(self):
        b,t=self._unicode_delivery_backend((2,));self.assertRaises(Win32BackendError,b.text,'\U0001f642');self.assertEqual(b.pending_unicode_ups,{0xd83d});self.assertEqual(t,[(0xd83d,True),(0xd83d,False)])


    def test_unicode_delivery_failure_still_releases_regular_key(self):
        backend, trace = self._unicode_delivery_backend((1,))
        backend.pending_unicode_ups.add(65)
        backend.held_keys["CTRL"] = 17
        regular = []
        backend._send_key = lambda vk, down: regular.append((vk, down))
        class State:
            def GetAsyncKeyState(self, vk):
                return 0
        backend.user32 = State()
        with self.assertRaises(Win32BackendError):
            backend.release_all()
        self.assertEqual(regular, [(17, False)])
        self.assertEqual(backend.pending_unicode_ups, {65})

    def test_unverified_explicit_up_stops_following_operations(self):
        class State:
            def __init__(self, stuck, raises=False):
                self.stuck = stuck
                self.raises = raises

            def GetAsyncKeyState(self, vk):
                if self.raises:
                    raise OSError("inert state query failure")
                return 0x8000 if vk in self.stuck else 0

        cases = (
            ([{"op": "key_state", "key": "SHIFT", "down": True},
              {"op": "key_state", "key": "SHIFT", "down": False}], {0x10}),
            ([{"op": "key_chord", "keys": ["CTRL", "S"]}], {0x11, ord("S")}),
            ([{"op": "key_chord", "keys": ["CTRL", "S"]}], {0x11}),
            ([{"op": "pointer_button", "button": "left", "down": True},
              {"op": "pointer_button", "button": "left", "down": False}], {1}),
        )
        for raises in (False, True):
            for ops, stuck in cases:
                with self.subTest(raises=raises, ops=ops):
                    backend = Win32Backend.__new__(Win32Backend)
                    backend.held_keys = {}
                    backend.held_buttons = set()
                    backend.pending_unicode_ups = set()
                    backend.emissions = 0
                    backend.user32 = State(stuck, raises)
                    events = []
                    backend.preflight = lambda program: None
                    def record(event):
                        events.append(event)
                        backend.emissions += 1
                    backend._send_key = lambda vk, down: record(("key", vk, down))
                    backend._send_unicode_unit = lambda unit, down: record(("text", unit, down))
                    backend._send = lambda item: record(("mouse", int(item.mi.dwFlags)))
                    program = {"ops": ops + [{"op": "text", "text": "x"}]}
                    with self.assertRaises(Win32BackendError):
                        backend.execute(program)
                    self.assertFalse(any(event[0] == "text" for event in events))

        backend = Win32Backend.__new__(Win32Backend)
        backend.held_keys = {}
        backend.held_buttons = set()
        backend.pending_unicode_ups = set()
        backend.emissions = 0
        backend.user32 = State(set())
        events = []
        backend.preflight = lambda program: None
        def record(event):
            events.append(event)
            backend.emissions += 1
        backend._send_key = lambda vk, down: record(("key", vk, down))
        backend._send_unicode_unit = lambda unit, down: record(("text", unit, down))
        result = backend.execute({"ops": [
            {"op": "key_state", "key": "SHIFT", "down": True},
            {"op": "key_state", "key": "SHIFT", "down": False},
            {"op": "text", "text": "x"},
        ]})
        self.assertEqual(result["emissions"], 4)
        self.assertEqual([event[0] for event in events], ["key", "key", "text", "text"])


@unittest.skipUnless(sys.platform == "win32", "requires native Windows")
class Win32IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = None
        cls.backend = None
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._cleanup_fixture)
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
    def _cleanup_fixture(cls):
        backend = getattr(cls, "backend", None)
        if backend is not None:
            try:
                backend.user32.PostMessageW(backend.targets["fixture"], 0x0010, 0, 0)
            except Exception:
                pass
        proc = getattr(cls, "proc", None)
        if proc is not None:
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
            finally:
                # Leave resources intact when terminal ownership is unconfirmed.
                if proc.poll() is not None and proc.stderr is not None:
                    proc.stderr.close()
        tmp = getattr(cls, "tmp", None)
        if tmp is not None:
            tmp.cleanup()

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
