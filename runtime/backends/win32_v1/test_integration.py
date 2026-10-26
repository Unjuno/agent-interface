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
from runtime.backends.win32_v1.backend import (
    Win32Backend,
    Win32BackendError,
    Win32ExecutionError,
    utf16_units,
    virtual_key,
)
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
    def test_arrow_key_events_use_extended_scan_codes(self):
        backend = Win32Backend.__new__(Win32Backend)
        emitted = []
        backend._send = lambda item: emitted.append(
            (int(item.ki.wVk), int(item.ki.wScan), int(item.ki.dwFlags))
        )

        backend._send_key(virtual_key("Up"), True)
        backend._send_key(virtual_key("Up"), False)

        self.assertEqual(emitted, [(0, 0x48, 0x0009), (0, 0x48, 0x000B)])

    def test_scan_code_mode_emits_tab_make_and_break_codes(self):
        backend = Win32Backend.__new__(Win32Backend)
        backend.user32 = type("MapApi", (), {
            "MapVirtualKeyW": staticmethod(lambda vk, mode: 0x0F)
        })()
        emitted = []
        backend._send = lambda item: emitted.append(
            (int(item.ki.wVk), int(item.ki.wScan), int(item.ki.dwFlags))
        )

        backend._send_key(virtual_key("TAB"), True, encoding="scan_code")
        backend._send_key(virtual_key("TAB"), False, encoding="scan_code")

        self.assertEqual(emitted, [(0, 0x0F, 0x0008), (0, 0x0F, 0x000A)])

    def test_scan_code_mode_refuses_a_virtual_key_without_a_scan_code(self):
        backend = Win32Backend.__new__(Win32Backend)
        backend.user32 = type("MapApi", (), {
            "MapVirtualKeyW": staticmethod(lambda vk, mode: 0)
        })()
        emitted = []
        backend._send = lambda item: emitted.append(item)

        with self.assertRaisesRegex(Win32BackendError, "no scan code"):
            backend._send_key(virtual_key("TAB"), True, encoding="scan_code")

        self.assertEqual(emitted, [])

    def test_release_all_reuses_the_held_key_encoding(self):
        backend, events = self._release_backend({9: False, 1: False})
        backend.held_keys = {"TAB": 9}
        backend.held_key_encodings = {"TAB": "scan_code"}
        backend.held_key_targets = {"TAB": None}
        backend._last_state_query_witness = []
        backend._send_key = lambda vk, down, encoding=None: events.append(
            ("key", vk, down, encoding)
        )

        receipt = backend.release_all()

        self.assertEqual(events[0], ("key", 9, False, "scan_code"))
        self.assertEqual(backend.held_key_encodings, {})
        self.assertTrue(receipt["verified"])

    def _release_backend(self, states):
        backend = Win32Backend.__new__(Win32Backend)
        backend.held_keys = {"CTRL": 17, "LEFT_CTRL": 17}
        backend.held_buttons = {"left"}
        backend.pending_unicode_ups = set()
        events = []

        class State:
            def __init__(self):
                self.sampled = []

            def GetAsyncKeyState(self, vk):
                self.sampled.append(vk)
                value = states[vk]
                return 0 if value is None else (0x8000 if value else 1)

        backend.user32 = State()
        backend._send_key = lambda vk, down: events.append(("key", vk, down))
        backend._send = lambda item: events.append(("mouse", int(item.mi.dwFlags)))
        return backend, events

    def test_release_all_samples_alias_once_and_retires_verified_obligations(self):
        backend, events = self._release_backend({17: False, 1: False})
        result = backend.release_all()
        self.assertEqual(backend.user32.sampled.count(17), 1)
        self.assertEqual(backend.user32.sampled.count(1), 1)
        self.assertEqual(backend.held_keys, {})
        self.assertEqual(backend.held_buttons, set())
        self.assertTrue(result["verified"])
        self.assertEqual(result["keys_unknown"], [])
        self.assertEqual(result["buttons_unknown"], [])
        self.assertEqual(events.count(("key", 17, False)), 1)

    def test_release_all_unknown_state_retains_all_obligations(self):
        backend, _ = self._release_backend({17: None, 1: False})
        result = backend.release_all()
        self.assertFalse(result["verified"])
        self.assertEqual(result["keys_unknown"], ["CTRL", "LEFT_CTRL"])
        self.assertEqual(result["buttons_unknown"], [])
        self.assertEqual(backend.held_keys, {"CTRL": 17, "LEFT_CTRL": 17})
        self.assertEqual(backend.held_buttons, set())

    def test_zero_state_with_stable_active_desktop_witness_retires_owned_inputs(self):
        backend, _ = self._release_backend({17: None, 1: None})
        backend.targets = {"fixture": 42}
        backend.held_key_targets = {"CTRL": "fixture", "LEFT_CTRL": "fixture"}
        backend.held_button_targets = {"left": "fixture"}
        evidence = {"target": "fixture", "input_desktop_active": True,
                    "desktop_hookcontrol_opened": True, "probe_integrity_rid": 8192,
                    "target_integrity_rid": 8192}
        backend._async_key_state_query_witness = lambda target: evidence

        result = backend.release_all()

        self.assertTrue(result["verified"])
        self.assertEqual(result["keys_unknown"], [])
        self.assertEqual(result["buttons_unknown"], [])
        self.assertEqual(result["state_query_witnesses"], {"17": [evidence, evidence],
                                                              "1": [evidence, evidence]})
        self.assertEqual(backend.held_keys, {})
        self.assertEqual(backend.held_buttons, set())

    def test_zero_state_without_stable_witness_remains_unknown(self):
        backend, _ = self._release_backend({17: None, 1: False})
        backend.targets = {"fixture": 42}
        backend.held_key_targets = {"CTRL": "fixture", "LEFT_CTRL": "fixture"}
        backend.held_button_targets = {"left": "fixture"}
        evidence = {"target": "fixture", "input_desktop_active": True}
        witnesses = iter((evidence, None))
        backend._async_key_state_query_witness = lambda _target: next(witnesses)

        result = backend.release_all()

        self.assertFalse(result["verified"])
        self.assertEqual(result["keys_unknown"], ["CTRL", "LEFT_CTRL"])
        self.assertEqual(backend.held_keys, {"CTRL": 17, "LEFT_CTRL": 17})

    def test_release_all_persistent_hold_then_later_clear(self):
        backend, _ = self._release_backend({17: True, 1: False})
        result = backend.release_all()
        self.assertEqual(result["keys_down"], ["CTRL", "LEFT_CTRL"])
        self.assertFalse(result["verified"])
        self.assertEqual(backend.held_keys, {"CTRL": 17, "LEFT_CTRL": 17})
        backend.user32.GetAsyncKeyState = lambda vk: 1
        result = backend.release_all()
        self.assertTrue(result["verified"])
        self.assertEqual(backend.held_keys, {})

    def test_release_all_state_query_exception_preserves_entire_ledger(self):
        backend, _ = self._release_backend({17: False, 1: False})
        def fail_second_query(vk):
            if vk == 1:
                raise OSError("injected query failure")
            return 1

        backend.user32.GetAsyncKeyState = fail_second_query
        with self.assertRaisesRegex(Win32BackendError, "key state query failed"):
            backend.release_all()
        self.assertEqual(backend.held_keys, {"CTRL": 17, "LEFT_CTRL": 17})
        self.assertEqual(backend.held_buttons, {"left"})

    def test_release_all_send_failure_preserves_ledger_without_state_query(self):
        backend, _ = self._release_backend({17: False, 1: False})
        backend._send_key = lambda vk, down: (_ for _ in ()).throw(OSError("injected send failure"))
        with self.assertRaisesRegex(OSError, "injected send failure"):
            backend.release_all()
        self.assertEqual(backend.user32.sampled, [])
        self.assertEqual(backend.held_keys, {"CTRL": 17, "LEFT_CTRL": 17})
        self.assertEqual(backend.held_buttons, {"left"})

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
                return 0x8000 if vk in self.stuck else 1

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


class Win32SessionRecoveryTests(unittest.TestCase):
    def backend(self):
        backend = Win32Backend.__new__(Win32Backend)
        backend.emissions = 0
        backend.held_keys = {}
        backend.held_buttons = set()
        backend.pending_unicode_ups = set()
        backend.manifest = lambda: Win32Backend.manifest(backend)
        backend.monotonic_ns = time.monotonic_ns
        backend.preflight = lambda program: None
        return backend

    def dispatch(self, session, program_id):
        return session.dispatch(
            make_program(program_id),
            current_observation_seq=7,
            current_binding_revision=3,
        )

    def test_verified_failure_cleanup_does_not_quarantine_or_block_next_dispatch(self):
        backend = self.backend()
        session = Win32RuntimeSession(backend)
        receipt = {"verified": True, "keys_down": [], "buttons_down": []}

        def fail_after_verified_cleanup(program):
            raise Win32ExecutionError(Win32BackendError("injected operation failure"), receipt, None)

        backend.execute = fail_after_verified_cleanup
        failed = self.dispatch(session, "failed-with-neutral-input")
        self.assertEqual(failed["status"], "execution_failed")
        self.assertEqual(failed["release"], receipt)
        self.assertFalse(failed["recovery_required"])
        self.assertFalse(session.recovery_required)

        backend.execute = lambda program: {"releases": [receipt]}
        next_result = self.dispatch(session, "next-dispatch")
        self.assertEqual(next_result["status"], "completed")

    def test_repeated_preflight_refusal_without_emission_does_not_quarantine(self):
        backend = self.backend()
        session = Win32RuntimeSession(backend)
        calls = 0

        def fail_on_execute_preflight(program):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise Win32BackendError("injected late preflight refusal")

        backend.preflight = fail_on_execute_preflight
        backend.execute = Win32Backend.execute.__get__(backend, Win32Backend)
        refused = self.dispatch(session, "late-preflight-refusal")
        self.assertEqual(refused["status"], "execution_failed")
        self.assertIn("preflight refusal", refused["detail"])
        self.assertEqual(backend.emissions, 0)
        self.assertFalse(refused["recovery_required"])
        self.assertFalse(session.recovery_required)

        receipt = {"verified": True, "keys_down": [], "buttons_down": []}
        backend.preflight = lambda program: None
        backend.execute = lambda program: {"releases": [receipt]}
        self.assertEqual(self.dispatch(session, "dispatch-after-preflight-refusal")["status"], "completed")

    def test_unverified_failure_cleanup_still_quarantines(self):
        backend = self.backend()
        session = Win32RuntimeSession(backend)
        receipt = {"verified": False, "keys_down": ["A"], "buttons_down": []}

        def fail_after_unverified_cleanup(program):
            raise Win32ExecutionError(Win32BackendError("injected operation failure"), receipt, None)

        backend.execute = fail_after_unverified_cleanup
        failed = self.dispatch(session, "failed-with-held-key")
        self.assertEqual(failed["status"], "execution_failed")
        self.assertTrue(failed["recovery_required"])
        self.assertTrue(session.recovery_required)
        self.assertEqual(self.dispatch(session, "blocked-next-dispatch")["error"], "INPUT_RECOVERY_REQUIRED")


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
        self.assertGreater(self.backend.emissions, before, row)
        deadline = time.time() + 2
        while time.time() < deadline and not self.effect.exists():
            time.sleep(0.02)
        self.assertTrue(self.effect.exists(), self.events.read_text() if self.events.exists() else "no events")
        effect = json.loads(self.effect.read_text())
        self.assertEqual(effect, {"saved": True, "text": "office", "clicked": True})
        releases = row["execution"]["releases"]
        self.assertTrue(releases)
        release = releases[-1]
        self.assertEqual(release["keys_down"], [])
        self.assertEqual(release["buttons_down"], [])
        if release["verified"]:
            self.assertEqual(row["status"], "completed", row)
            self.assertEqual(release["keys_unknown"], [])
            self.assertEqual(release["buttons_unknown"], [])
        else:
            # GetAsyncKeyState zero is ambiguous between up and inaccessible.
            # Preserve task-effect evidence while refusing to claim completion.
            self.assertEqual(row["status"], "release_unverified", row)
            self.assertTrue(row["recovery_required"])
            self.assertTrue(release["keys_unknown"] or release["buttons_unknown"], release)
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
