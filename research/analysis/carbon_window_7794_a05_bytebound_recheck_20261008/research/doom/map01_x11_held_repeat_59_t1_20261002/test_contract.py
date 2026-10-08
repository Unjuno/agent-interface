"""Construction and anti-mutation tests for the independent evidence audit."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("held_repeat_audit", ROOT / "audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
FIXTURE = json.loads((ROOT / "fixture.json").read_text())
FREEZE = {"image_digest": AUDIT.IMAGE}


def sample(label, phase, focus, down, ts, code=25):
    bits = bytearray(32)
    if down:
        bits[code // 8] |= 1 << (code % 8)
    return {"label": label, "phase": phase, "focus_window_id": focus,
        "expected_focus_window_id": focus, "keycode": code,
        "key_down": down, "bitmap_hex": bits.hex(), "observed_ns": ts}


def record():
    code, aid, bid = 25, 100, 200
    samples = [sample("positive_pre", "positive", aid, False, 1),
        sample("positive_held", "positive", aid, True, 2),
        sample("positive_post", "positive", aid, False, 3),
        sample("transfer_pre", "transfer", aid, False, 4),
        sample("transfer_a_held", "transfer", aid, True, 5),
        sample("transfer_b_held", "transfer", bid, True, 6),
        sample("transfer_b_end", "transfer", bid, True, 7),
        sample("transfer_post", "transfer", bid, False, 8)]
    events = [{"phase": "positive_held", "type": 2, "detail": code,
        "window_id": aid, "received_ns": 20},
        {"phase": "positive_held", "type": 2, "detail": code,
        "window_id": aid, "received_ns": 30},
        {"phase": "transfer_a_held", "type": 2, "detail": code,
        "window_id": aid, "received_ns": 50},
        {"phase": "transfer_b_held", "type": 2, "detail": code,
        "window_id": bid, "received_ns": 70}]
    return {"schema": "issue59-x11-held-repeat-raw-v1",
        "allocation_id": FIXTURE["allocation_id"], "main_sha": FIXTURE["main_sha"],
        "image_digest": AUDIT.IMAGE, "candidate_invocations": 1, "retries": 0,
        "xvfb_tcp_enabled": False, "xvfb_exit_code": 0,
        "xvfb_socket_removed": True, "xvfb_lock_removed": True,
        "xvfb_stderr": "", "keycode": code, "window_a_id": aid,
        "window_b_id": bid, "repeat_control": {"global_auto_repeat": 1},
        "samples": samples, "events": events,
        "a_received_initial_transfer_press": True,
        "transfer_b_start_ns": 60, "transfer_observe_end_ns": 80,
        "transfer_release_action_ns": 81}


class ContractTests(unittest.TestCase):
    def test_b_repeat_yields_scoped_pass(self):
        self.assertEqual(AUDIT.disposition(record(), FIXTURE, FREEZE, False)[0],
            "PASS_X11_HELD_REPEAT_REACHES_NEW_FOCUS")

    def test_no_b_repeat_is_scientific_fail_not_pass(self):
        raw = record()
        raw["events"] = [e for e in raw["events"] if e["phase"] != "transfer_b_held"]
        self.assertEqual(AUDIT.disposition(raw, FIXTURE, FREEZE, False)[0],
            "FAIL_X11_HELD_REPEAT_NOT_OBSERVED_IN_BOUNDED_WINDOW")

    def test_bad_full_bitmap_is_rejected(self):
        raw = record(); raw["samples"][5]["bitmap_hex"] = "00"
        self.assertTrue(any("bitmap" in e for e in AUDIT.errors_for(raw, FIXTURE, FREEZE, False)))

    def test_focus_identity_mutation_is_rejected(self):
        raw = record(); raw["samples"][5]["focus_window_id"] = raw["window_a_id"]
        self.assertTrue(any("focus" in e for e in AUDIT.errors_for(raw, FIXTURE, FREEZE, False)))

    def test_missing_positive_repeat_is_stop(self):
        raw = record(); raw["events"] = [e for e in raw["events"] if e["phase"] != "positive_held"]
        self.assertEqual(AUDIT.disposition(raw, FIXTURE, FREEZE, False)[0], "STOP_OR_AUDIT_ERROR")


if __name__ == "__main__":
    unittest.main(verbosity=2)
