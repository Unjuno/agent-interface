"""Keep each original UP's sample distinct from another key's retry sample."""
import contextlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch

from test_input_owner_v12_explicit_up_cancel import FakeDisplay, Lease


@contextlib.contextmanager
def fake_owner():
    display = FakeDisplay()
    display.query_number = 0
    display.fail_query_numbers = set()
    display.drops_by_code = {}
    query_keymap = display.query_keymap

    def query():
        display.query_number += 1
        if display.query_number in display.fail_query_numbers:
            display.trace.append(("query_error", display.query_number, tuple(sorted(display.down))))
            raise RuntimeError("synthetic retry-only keymap failure")
        return query_keymap()

    display.query_keymap = query
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                  Button1Mask=256, AnyPropertyType=0)
    xlib.XK = types.SimpleNamespace(string_to_keysym=ord)
    xlib.display = types.ModuleType("Xlib.display")
    xlib.display.Display = lambda _name: display
    xlib.error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                      BadDrawable=type("BadDrawable", (Exception,), {}))
    ext = types.ModuleType("Xlib.ext")
    ext.xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(connection, event, code):
        if connection is not display:
            raise AssertionError("unexpected display connection")
        display.trace.append(("key_event", event, code))
        if event == xlib.X.KeyPress:
            display.down.add(code)
        elif event == xlib.X.KeyRelease:
            if display.drops_by_code.get(code, 0):
                display.drops_by_code[code] -= 1
            else:
                display.down.discard(code)

    ext.xtest.fake_input = fake_input
    with patch.dict(sys.modules, {"Xlib": xlib, "Xlib.display": xlib.display,
                                  "Xlib.ext": ext, "Xlib.ext.xtest": ext.xtest}):
        source = Path(__file__).with_name("input_owner_v12.py")
        spec = importlib.util.spec_from_file_location("batch_sample_custody_owner", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Logical timestamps distinguish samples without testing wall-clock speed.
        ticks = itertools.count(100000, 100)
        module.time = types.SimpleNamespace(perf_counter_ns=lambda: next(ticks),
                                            monotonic=time.monotonic)
        owner = module.InputOwner(":fake-batch-custody")
        try:
            yield owner, display
        finally:
            owner.close()


class BatchSampleCustodyTests(unittest.TestCase):
    def observe(self, dropped_code, retry_query_error=False):
        with fake_owner() as (owner, display):
            lease = Lease()
            owner.call("down", lease, "W")
            owner.call("down", lease, "A")
            display.trace.clear()
            display.query_number = 0
            display.drops_by_code[dropped_code] = 1
            if retry_query_error:
                display.fail_query_numbers.add(3)
            rows = owner.call("up_batch", lease, ["A", "W"])
            trace = list(display.trace)
            state = owner.call("input_state")
            rejection = None
            before_press_count = sum(event[:2] == ("key_event", 2) for event in display.trace)
            if retry_query_error:
                try:
                    owner.call("down", lease, "W")
                except RuntimeError as error:
                    rejection = str(error)
            after_press_count = sum(event[:2] == ("key_event", 2) for event in display.trace)
            result = {"case": f"drop-{dropped_code}-error-{retry_query_error}",
                      "rows": rows, "trace": trace, "state_after_batch": state,
                      "following_down_error": rejection,
                      "following_press_count": after_press_count - before_press_count,
                      "clock": "synthetic monotonic nanosecond labels; no latency inference",
                      "real_x11": False, "physical_verification_authoritative": False}
        result["owner_stopped"] = owner.stopped.is_set()
        result["final_fake_keys_down"] = sorted(display.down)
        print(json.dumps(result, sort_keys=True), flush=True)
        if directory := os.environ.get("BATCH_CUSTODY_OUT"):
            with (Path(directory) / (result["case"] + ".json")).open("x") as stream:
                json.dump(result, stream, indent=2, sort_keys=True)
        return result

    def assert_original_up_order(self, trace):
        queries = [i for i, row in enumerate(trace) if row[0] in ("query_keymap", "query_error")]
        self.assertEqual(len(queries), 3)
        originals = [row[2] for row in trace[queries[0] + 1:queries[1]]
                     if row[:2] == ("key_event", 3)]
        self.assertEqual(originals, [39, 38])

    def test_first_and_last_key_retry_keep_one_initial_sample(self):
        for dropped_code in (39, 38):
            with self.subTest(dropped_code=dropped_code):
                result = self.observe(dropped_code)
                self.assert_original_up_order(result["trace"])
                initial = [row["server_keyup_attempts"][0] for row in result["rows"]]
                self.assertEqual(initial[0]["keymap_sampled_ns"], initial[1]["keymap_sampled_ns"])
                self.assertEqual([row["server_key_down_after"] for row in initial],
                                 [dropped_code == 39, dropped_code == 38])
                self.assertEqual([row["server_keyup_attempt_count"] for row in result["rows"]],
                                 [2 if dropped_code == 39 else 1, 2 if dropped_code == 38 else 1])
                self.assertTrue(all(row["server_keyup_verified"] for row in result["rows"]))
                self.assertFalse(result["state_after_batch"]["release_pending"])
                self.assertTrue(result["owner_stopped"])

    def test_retry_query_error_does_not_replace_later_initial_evidence(self):
        result = self.observe(39, retry_query_error=True)
        self.assert_original_up_order(result["trace"])
        first, second = result["rows"]
        initial_first, retry = first["server_keyup_attempts"]
        initial_second, = second["server_keyup_attempts"]
        self.assertIsNone(retry["server_key_down_after"])
        self.assertEqual(retry["keymap_after_error"]["type"], "RuntimeError")
        self.assertEqual(initial_second["keymap_sampled_ns"], initial_first["keymap_sampled_ns"])
        self.assertIs(initial_second["server_key_down_after"], False)
        self.assertIsNone(initial_second["keymap_after_error"])
        self.assertTrue(second["server_keyup_verified"])
        self.assertFalse(first["server_keyup_verified"])
        self.assertTrue(result["state_after_batch"]["release_pending"])
        self.assertEqual(result["state_after_batch"]["owned_keycodes"], [39])
        self.assertIn("release pending", result["following_down_error"])
        self.assertEqual(result["following_press_count"], 0)
        self.assertTrue(result["owner_stopped"])
        self.assertEqual(result["final_fake_keys_down"], [])


if __name__ == "__main__":
    unittest.main()
