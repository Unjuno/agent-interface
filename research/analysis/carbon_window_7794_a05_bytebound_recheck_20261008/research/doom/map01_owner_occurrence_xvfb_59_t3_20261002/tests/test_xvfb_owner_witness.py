"""Real-X-server characterization of per-occurrence keymap witnesses."""
import importlib.util
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dependencies" / "input_owner_v11.py"


class Lease:
    intent_token = "xvfb-t3-repeat-w"

    def __init__(self, expected_focus):
        self.expected_focus = expected_focus
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.cancel = threading.Event()

    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("test lease expired")


def run_two_pulses(source):
    with tempfile.TemporaryDirectory(prefix="agent-interface-xvfb-t3-") as temp:
        auth = Path(temp) / "empty.Xauthority"
        auth.write_bytes(b"")
        env = dict(os.environ, XAUTHORITY=str(auth))
        proc = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "640x480x24",
             "-nolisten", "tcp", "-ac"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        try:
            ready, _, _ = select.select([proc.stdout], [], [], 5)
            if not ready:
                raise RuntimeError("Xvfb did not allocate a display within 5s")
            number = proc.stdout.readline().strip()
            if not number.isdecimal():
                raise RuntimeError("Xvfb returned an invalid display number")
            display_name = ":" + number

            from Xlib import display
            probe = display.Display(display_name)
            focus = probe.get_input_focus().focus
            expected_focus = focus.id if hasattr(focus, "id") else focus
            probe.close()

            executor = types.ModuleType("executor_v3")
            executor.Cancelled = type("Cancelled", (Exception,), {})
            executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
            sys.modules["executor_v3"] = executor
            spec = importlib.util.spec_from_file_location("t3_input_owner", source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            owner = module.InputOwner(display_name)
            lease = Lease(expected_focus)
            admissions = [owner.call("down", lease, "W")]
            owner.call("up", lease, "W")
            admissions.append(owner.call("down", lease, "W"))
            owner.call("up", lease, "W")
            owner.close()
            return admissions, owner.records
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=3)
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()


class XvfbKeymapWitnessTests(unittest.TestCase):
    def test_each_repeated_occurrence_reflects_server_bitmap_down_then_up(self):
        admissions, records = run_two_pulses(SOURCE)
        witnesses = [row for row in records
                     if row.get("event") == "owner_keymap_witness"]
        self.assertEqual(len(witnesses), 6,
                         "X server evidence requires pre/down/up per occurrence")
        ids = [row.get("interval_id") for row in admissions]
        self.assertEqual(len(ids), 2)
        self.assertTrue(all(isinstance(value, str) and value for value in ids))
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual([row.get("interval_id") for row in witnesses],
                         [ids[0]] * 3 + [ids[1]] * 3)
        self.assertEqual([row.get("stage") for row in witnesses],
                         ["pre_down", "post_down", "post_up"] * 2)
        self.assertEqual([row.get("key_down") for row in witnesses],
                         [False, True, False] * 2)
        for row in witnesses:
            bitmap = bytes.fromhex(row["bitmap_hex"])
            code = row["keycode"]
            self.assertEqual(len(bitmap), 32)
            self.assertEqual(bool(bitmap[code // 8] & (1 << (code % 8))),
                             row["key_down"])
            self.assertIs(row["grants_input_authority"], False)
            self.assertIs(row["physical_key_up_claimed"], False)
        terminal = [row for row in records if row.get("event") == "owner_release"]
        self.assertEqual(len(terminal), 1)
        self.assertTrue(terminal[0]["verified"])
        self.assertEqual(terminal[0]["keys_down"], [])


if __name__ == "__main__":
    unittest.main()
