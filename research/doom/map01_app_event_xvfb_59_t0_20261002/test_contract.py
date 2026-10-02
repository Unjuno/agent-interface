"""Small preformal checks for the independent X11 evidence contract."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("issue59_audit", ROOT / "audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


def sample(scenario, label, focus, code, down, tick):
    bits = bytearray(32)
    if down:
        bits[code // 8] |= 1 << (code % 8)
    return {"scenario": scenario, "label": label, "focus_window_id": focus,
            "expected_focus_window_id": focus, "keycode": code,
            "key_down": down, "bitmap_hex": bits.hex(), "observed_ns": tick}


def valid_record():
    aid, bid, code = 101, 202, 25
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    fixture_hash = AUDIT.hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest()
    freeze_hash = AUDIT.hashlib.sha256((ROOT / "FREEZE.json").read_bytes()).hexdigest()
    samples = [
        sample("stable_focus_positive_control", "pre_down", aid, code, False, 1),
        sample("stable_focus_positive_control", "post_down", aid, code, True, 2),
        sample("stable_focus_positive_control", "post_up", aid, code, False, 3),
        sample("focus_transfer_while_key_down", "pre_down", aid, code, False, 4),
        sample("focus_transfer_while_key_down", "post_down_a_focused", aid, code, True, 5),
        sample("focus_transfer_while_key_down", "still_down_b_focused", bid, code, True, 6),
        sample("focus_transfer_while_key_down", "post_up_b_focused", bid, code, False, 7),
    ]
    events = [
        {"scenario": "stable_focus_positive_control", "type": 2,
         "detail": code, "window_id": aid},
        {"scenario": "stable_focus_positive_control", "type": 3,
         "detail": code, "window_id": aid},
        {"scenario": "focus_transfer_while_key_down", "type": 2,
         "detail": code, "window_id": aid},
    ]
    return {"schema": "issue59-x11-app-delivery-raw-v1",
            "allocation_id": FIXTURE["allocation_id"],
            "source_main_sha": FIXTURE["main_sha"],
            "image_digest": AUDIT.EXPECTED_IMAGE,
            "freeze_sha256": freeze_hash,
            "candidate_sha256": freeze["candidate_sha256"],
            "fixture_sha256": fixture_hash,
            "candidate_invocations": 1, "retries": 0,
            "xvfb_tcp_enabled": False,
            "xvfb_exit_code_after_controlled_terminate": 0,
            "xvfb_socket_removed": True, "xvfb_lock_removed": True,
            "xvfb_stderr_fatal": False,
            "window_a_id": aid, "window_b_id": bid, "keycode": code,
            "samples": samples, "application_events": events,
            "actions": [
                {"scenario": "stable_focus_positive_control", "ordinal": 1,
                 "action": "set_focus", "window_id": aid,
                 "started_ns": 1, "sync_returned_ns": 2},
                {"scenario": "stable_focus_positive_control", "ordinal": 2,
                 "action": "fake_key", "event_type": 2, "keycode": code,
                 "started_ns": 3, "sync_returned_ns": 4},
                {"scenario": "stable_focus_positive_control", "ordinal": 3,
                 "action": "fake_key", "event_type": 3, "keycode": code,
                 "started_ns": 5, "sync_returned_ns": 6},
                {"scenario": "focus_transfer_while_key_down", "ordinal": 4,
                 "action": "set_focus", "window_id": aid,
                 "started_ns": 7, "sync_returned_ns": 8},
                {"scenario": "focus_transfer_while_key_down", "ordinal": 5,
                 "action": "fake_key", "event_type": 2, "keycode": code,
                 "started_ns": 9, "sync_returned_ns": 10},
                {"scenario": "focus_transfer_while_key_down", "ordinal": 6,
                 "action": "set_focus", "window_id": bid,
                 "started_ns": 11, "sync_returned_ns": 12},
                {"scenario": "focus_transfer_while_key_down", "ordinal": 7,
                 "action": "fake_key", "event_type": 3, "keycode": code,
                 "started_ns": 13, "sync_returned_ns": 14},
            ],
            "b_keypress_count_while_down": 0,
            "event_checks": {"a_positive_keypress": True,
                              "a_positive_keyrelease": True,
                              "a_transfer_keypress": True}}


class EvidenceContractTests(unittest.TestCase):
    def test_full_bitmap_bit_decodes(self):
        row = sample("s", "l", 1, 25, True, 1)
        self.assertTrue(AUDIT.key_bit(row))

    def test_valid_positive_and_focus_transfer_contract(self):
        freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
        self.assertEqual(AUDIT.validate(valid_record(), FIXTURE, freeze), [])

    def test_global_down_does_not_turn_into_b_app_delivery(self):
        record = valid_record()
        record["application_events"].append({
            "scenario": "focus_transfer_while_key_down", "type": 2,
            "detail": record["keycode"], "window_id": record["window_b_id"]})
        self.assertTrue(any("B received" in e
                            for e in AUDIT.validate(record, FIXTURE,
                                json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8")))))

    def test_bitmap_corruption_is_rejected(self):
        record = valid_record()
        record["samples"][5]["bitmap_hex"] = "00"
        self.assertTrue(any("bitmap" in e
                            for e in AUDIT.validate(record, FIXTURE,
                                json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8")))))

    def test_focus_identity_mismatch_is_rejected(self):
        record = valid_record()
        record["samples"][5]["focus_window_id"] = record["window_a_id"]
        self.assertTrue(any("focus" in e
                            for e in AUDIT.validate(record, FIXTURE,
                                json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8")))))


if __name__ == "__main__":
    unittest.main(verbosity=2)
