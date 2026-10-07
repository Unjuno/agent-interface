"""Resolved-keycode aliases must be refused before a release batch touches X.

The Xlib surface here is synthetic. The tests use the real V12 InputOwner,
V4 transition wrapper, measured V39 backend and Executor V13; the executor case
stubs only game-frame capture. These are ordinary host regressions, not native
X11, physical-input, or performance evidence.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

LIVE = Path(__file__).resolve().parent
DOOM = LIVE.parent / "doom"
for path in (str(LIVE), str(DOOM)):
    if path not in sys.path:
        sys.path.insert(0, path)

# Import the compatibility helpers only. Do not import the fixture TestCase,
# which would expose its methods to unittest's module-level discovery.
import test_input_owner_v12_key_measurement as owner_fixture


class AliasDisplay(owner_fixture.FakeDisplay):
    def __init__(self, keycodes):
        super().__init__()
        self.keycodes = dict(keycodes)

    def keysym_to_keycode(self, keysym):
        if keysym in self.keycodes:
            return self.keycodes[keysym]
        return super().keysym_to_keycode(keysym)


class InputOwnerBatchAliasTests(unittest.TestCase):
    X_MODULE_NAMES = (
        "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
        "Xlib.ext", "Xlib.ext.xtest",
    )
    RELOADED_NAMES = (
        "input_owner_v12", "input_transition_owner_v3",
        "input_transition_owner_v4", "doom_typed_release_backend_v2",
        "doom_owner_thread_release_batch_backend_v1",
        "doom_batch_key_measurement_backend_v1", "executor_v13",
    )

    def setUp(self):
        # Load exception definitions before the fixture installs synthetic Xlib.
        import executor_v3  # noqa: F401

        self._saved_modules = {
            name: sys.modules.get(name)
            for name in self.X_MODULE_NAMES + self.RELOADED_NAMES
        }
        self.fake = None
        self.owners = []
        self.backend = None
        self.engine = None
        self._install_fake_x()
        self._reload("input_owner_v12")
        from input_owner_v12 import InputOwner
        self.InputOwner = InputOwner

    def _install_fake_x(self):
        x = types.ModuleType("Xlib.X")
        x.KeyPress, x.KeyRelease = 2, 3
        x.ButtonPress, x.ButtonRelease = 4, 5
        x.Button1Mask, x.AnyPropertyType, x.IsViewable = 256, 0, 2
        x.MotionNotify = 6
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda key: ord(key) if len(key) == 1 else 0
        display = types.ModuleType("Xlib.display")
        display.Display = lambda _name: self.fake
        error = types.ModuleType("Xlib.error")
        error.BadWindow = type("BadWindow", (Exception,), {})
        error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, code):
            self.fake.trace.append(("key_event", event, code))
            if event == x.KeyPress:
                self.fake.down.add(code)
            elif event == x.KeyRelease:
                remaining = self.fake.drop_counts.get(code, 0)
                if code in self.fake.persistent_drop_codes or remaining:
                    if remaining:
                        self.fake.drop_counts[code] = remaining - 1
                else:
                    self.fake.down.discard(code)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib = types.ModuleType("Xlib")
        xlib.X, xlib.XK, xlib.display, xlib.error, xlib.ext = x, xk, display, error, ext
        sys.modules.update({
            "Xlib": xlib, "Xlib.X": x, "Xlib.XK": xk,
            "Xlib.display": display, "Xlib.error": error,
            "Xlib.ext": ext, "Xlib.ext.xtest": xtest,
        })

    def _reload(self, name):
        sys.modules.pop(name, None)

    def _new_owner(self, keycodes, *, measure):
        self.fake = AliasDisplay(keycodes)
        owner = self.InputOwner(":fake-alias", measure_key_edges=measure)
        self.owners.append(owner)
        return owner

    def _stop_owner(self, owner):
        if owner is None:
            return
        owner.close()
        self.assertTrue(owner.stopped.wait(1), "owner thread did not stop")
        self.assertFalse(owner.thread.is_alive(), "owner thread leaked")

    def _cleanup_owner(self, owner, lease):
        record = owner.call("release", lease)
        self.assertTrue(record["verified"], record)
        self.assertEqual(self.fake.down, set())
        return record

    def _emit_raw(self, **data):
        print(json.dumps({"test": self.id(), **data}, sort_keys=True), flush=True)

    def test_alias_up_batch_refuses_before_io_in_both_orders_measurement_on_and_off(self):
        alias_map = {ord("a"): 38, ord("A"): 38}
        traces = []
        for measure in (False, True):
            for keys in (("a", "A"), ("A", "a")):
                with self.subTest(measure=measure, keys=keys):
                    owner = self._new_owner(alias_map, measure=measure)
                    lease = owner_fixture.FakeLease("alias-owner-intent")
                    try:
                        # The public owner admits the same physical code under
                        # separate logical names; exercise its batch boundary.
                        downs = [owner.call("down", lease, key) for key in keys]
                        trace_start = len(self.fake.trace)
                        query_start = self.fake.query_count
                        error = None
                        error_message = None
                        result = None
                        try:
                            result = owner.call("up_batch", lease, list(keys))
                        except ValueError as exc:
                            error = type(exc).__name__
                            error_message = str(exc)
                        batch_trace = self.fake.trace[trace_start:]
                        trace_end = len(self.fake.trace)
                        down_before_cleanup = sorted(self.fake.down)
                        query_delta = self.fake.query_count - query_start
                        release_codes = [row[2] for row in batch_trace
                                         if row[:2] == ("key_event", 3)]
                        cleanup = self._cleanup_owner(owner, lease)
                        trace_row = {
                            "measure": measure, "keys": list(keys),
                            "alias_keycode": 38, "rejected": error == "ValueError",
                            "error_type": error, "error_message": error_message,
                            "batch_trace_start": trace_start, "batch_trace_end": trace_end,
                            "down_before_cleanup": down_before_cleanup,
                            "result_count": len(result) if result else 0,
                            "batch_query_delta": query_delta,
                            "batch_release_codes": release_codes,
                            "cleanup_verified": cleanup["verified"],
                            "final_down": sorted(self.fake.down),
                            "trace": list(self.fake.trace),
                        }
                        traces.append(trace_row)
                        self._emit_raw(**trace_row)
                        self.assertEqual(error, "ValueError", "resolved aliases must be refused")
                        self.assertIn("distinct keycodes", error_message.lower())
                        self.assertEqual(query_delta, 0, "refusal must precede keymap queries")
                        self.assertEqual(release_codes, [], "refusal must precede every UP")
                        self.assertEqual(len(downs), 2)
                        self.assertEqual([row[2] for row in self.fake.trace[:trace_start]
                                          if row[:2] == ("key_event", 2)], [38, 38])
                        self.assertEqual(down_before_cleanup, [38],
                                         "refusal must leave the admitted key held for cleanup")
                    finally:
                        self._stop_owner(owner)
        self.assertEqual(len(traces), 4)

    def test_distinct_keycodes_remain_valid_with_measurement_on_and_off(self):
        rows = []
        for measure in (False, True):
            with self.subTest(measure=measure):
                owner = self._new_owner({ord("a"): 38, ord("s"): 39}, measure=measure)
                lease = owner_fixture.FakeLease("distinct-owner-intent")
                try:
                    downs = [owner.call("down", lease, key) for key in ("a", "s")]
                    ups = owner.call("up_batch", lease, ["s", "a"])
                    self.assertEqual([row["key"] for row in ups], ["s", "a"])
                    self.assertTrue(all(row["server_keyup_verified"] for row in ups))
                    if measure:
                        self.assertTrue(all(
                            row["physical_key_measurement"]["classification"] ==
                            "CONFIRMED_PHYSICAL_UP" for row in ups))
                        down_ids = {row["key"]: row["physical_key_measurement"]["actuation_id"]
                                    for row in downs}
                        for row in ups:
                            self.assertEqual(
                                row["physical_key_measurement"]["actuation_id"],
                                down_ids[row["key"]])
                    else:
                        self.assertTrue(all("physical_key_measurement" not in row for row in ups))
                    self.assertEqual(self.fake.down, set())
                    rows.append({"measure": measure, "ups": ups,
                                 "trace": list(self.fake.trace)})
                finally:
                    self._stop_owner(owner)
        self._emit_raw(control="distinct_keycodes", cases=rows)

    def test_measured_executor_cleans_up_after_alias_batch_refusal(self):
        # Map two allowed V39 key names to one keycode so the real measured
        # backend reaches the alias UP batch through its ordinary hold path.
        self.fake = AliasDisplay({ord("a"): 38, ord("s"): 38})
        for name in self.RELOADED_NAMES:
            self._reload(name)

        from doom_typed_release_backend_v2 import Backend as Ancestor
        from doom_batch_key_measurement_backend_v1 import Backend
        from executor_v13 import Executor

        events = []
        event_lock = threading.Lock()
        terminal_seen = threading.Event()

        def emit(row):
            with event_lock:
                events.append(dict(row))
                if row.get("event") == "terminal":
                    terminal_seen.set()

        def inert_game_facing_init(backend, session, out, sink, signal_readers):
            # Keep the measured owner/backend constructor real while avoiding
            # frame artifacts or a game-facing session in this fake-X test.
            backend.session = session
            backend.out = out
            backend.emit = sink
            backend.held = set()
            backend.touched = set()
            backend.sequence = 0
            backend.owner = types.SimpleNamespace(close=lambda: None)
            backend._input_event_context = None
            backend._release_batch = threading.local()
            backend._last_release_batch_delivery = None
            backend.observed_focus = 41
            backend.observed_pointer = None

        with patch.object(Ancestor, "__init__", inert_game_facing_init):
            self.backend = Backend(
                types.SimpleNamespace(name=":fake-alias"), None, emit,
                {"health": object(), "ammo": object()})
        self.backend.snapshot = lambda _identifier, _index: None
        self.owners.append(getattr(self.backend.owner, "_inner", self.backend.owner))
        self.engine = Executor(self.backend, emit)

        try:
            self.engine.submit(
                "alias-hold", [{"op": "hold", "keys": ["a", "s"], "duration_ms": 2}],
                expected_sequence=self.backend.sequence,
                valid_until_ns=time.perf_counter_ns() + 2_000_000_000)
            self.assertTrue(terminal_seen.wait(2), "executor did not publish terminal")
            terminal = next(row for row in events if row.get("event") == "terminal")
            release_rows = [row for row in events
                            if row.get("event") == "input_release_transition"]
            terminal_state = self.backend.owner.call("input_state")
            raw = getattr(self.backend.owner, "_inner", self.backend.owner)
            admitted = [row for row in events
                        if row.get("event") == "input_admission"]
            cleanup_records = [row for row in raw.records
                               if row.get("event") == "owner_release"]
            terminal_release = terminal.get("release", {})
            alias_failures = [row for row in release_rows
                              if row.get("release_batch_error_type") == "ValueError"]
            observed = {
                "status": terminal.get("status"),
                "error": terminal.get("error"),
                "release_verified": terminal.get("release", {}).get("verified"),
                "incomplete_release_rows": [
                    {key: row.get(key) for key in (
                        "key", "release_batch_complete", "release_batch_call_outcome",
                        "release_batch_disposition", "physical_key_measurement")}
                    for row in release_rows],
                "terminal_input_state": terminal_state,
                "owner_records": raw.records,
                "events": events,
                "admitted_before_batch_failure": admitted,
                "cleanup_records": cleanup_records,
                "terminal_release": terminal_release,
                "fake_keycodes_down": sorted(self.fake.down),
                "trace": list(self.fake.trace),
            }
            self._emit_raw(**observed)
            self.assertEqual(terminal.get("status"), "failed")
            self.assertIsInstance(terminal.get("error"), str)
            self.assertIn("ValueError", terminal["error"])
            self.assertIn("distinct keycodes", terminal["error"].lower())
            self.assertEqual(len(admitted), 2, admitted)
            self.assertEqual([row.get("key") for row in admitted], ["a", "s"])
            self.assertEqual([row[2] for row in self.fake.trace
                              if row[:2] == ("key_event", 2)], [38, 38])
            self.assertEqual(len({row.get("owner_id") for row in admitted}), 1)
            self.assertEqual(len({row.get("intent_token") for row in admitted}), 1)
            measured = [row["physical_key_measurement"] for row in admitted]
            self.assertEqual([row["classification"] for row in measured],
                             ["CONFIRMED_PHYSICAL_DOWN", "KEYMAP_EDGE_UNCONFIRMED"])
            self.assertIsInstance(measured[0]["actuation_id"], str)
            self.assertIsNone(measured[1]["actuation_id"])
            self.assertIsNone(measured[1]["adapter_edge"])
            self.assertIsNone(measured[1]["bracket"])
            self.assertEqual(len(alias_failures), 2, release_rows)
            self.assertTrue(all(row.get("release_batch_call_outcome") == "unknown_no_retry"
                                for row in alias_failures), release_rows)
            self.assertTrue(all(row.get("owner_id") == admitted[0].get("owner_id")
                                and row.get("intent_token") == admitted[0].get("intent_token")
                                for row in alias_failures), release_rows)
            self.assertTrue(cleanup_records, raw.records)
            cleanup = cleanup_records[-1]
            self.assertTrue(cleanup.get("verified"), cleanup)
            self.assertEqual(cleanup.get("keys_down"), [])
            self.assertEqual(cleanup.get("buttons_down"), [])
            self.assertEqual(terminal_state.get("owner_id"), admitted[0].get("owner_id"))
            self.assertEqual(terminal_state.get("owned_keycodes"), [])
            self.assertIsNone(terminal_state.get("active_lease_deadline_ns"))
            self.assertEqual(terminal_release.get("intent_token"), admitted[0].get("intent_token"))
            self.assertTrue(terminal.get("release", {}).get("verified"), terminal)
            self.assertTrue(terminal_state.get("release_pending") is False, terminal_state)
            self.assertEqual(self.fake.down, set())
            self.assertTrue(release_rows)
            self.assertTrue(all(row.get("release_batch_complete") is False
                                for row in release_rows))
            self.assertFalse(any(row.get("ordinary_release_candidate") is True
                                 for row in release_rows))
        finally:
            try:
                if self.engine is not None:
                    self.engine.close()
            finally:
                raw = getattr(self.backend.owner, "_inner", self.backend.owner)
                self._stop_owner(raw)
                self.engine = None

    def tearDown(self):
        if self.engine is not None:
            try:
                self.engine.close()
            except Exception:
                pass
        for owner in self.owners:
            if owner is None or getattr(owner, "stopped", None) is None:
                continue
            if not owner.stopped.is_set():
                try:
                    owner.close()
                except Exception:
                    pass
            self.assertTrue(owner.stopped.wait(1), "owner thread did not stop")
            self.assertFalse(owner.thread.is_alive(), "owner thread leaked")
        for name, module in self._saved_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


if __name__ == "__main__":
    unittest.main()
