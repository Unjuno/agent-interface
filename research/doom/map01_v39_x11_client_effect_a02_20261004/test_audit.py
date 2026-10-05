"""Mutation controls for app event and counter evidence."""
import unittest

from audit import validate


def sample(occurrence, stage, down, start, code=25):
    bitmap = bytearray(32)
    if down:
        bitmap[code // 8] |= 1 << (code % 8)
    return {"occurrence_id": occurrence, "stage": stage, "sample_started_ns": start,
            "sample_finished_ns": start + 1, "bitmap_length": 32,
            "bitmap_hex": bytes(bitmap).hex(), "keycode": code, "key_down": down,
            "source": "independent Xlib Display.query_keymap",
            "physical_key_up_claimed": False}


def fixture():
    code, window, owner = 25, 100, "owner-x"
    cycles = []
    for i, occ in enumerate(("a", "b")):
        b = 1000 + i * 1000
        token = "a02:" + occ
        admission = {"event": "input_admission", "admitted_ns": b + 11,
                     "input_ack_ns": b + 12}
        cycles.append({
            "occurrence_id": occ, "key": "w", "keycode": code,
            "intent_token": token, "owner_id": owner,
            "pre_down": sample(occ, "pre_down", False, b),
            "down_started_ns": b + 10, "admission": admission,
            "down_returned_ns": b + 13,
            "owner_after_down": {"owner_id": owner, "owned_keycodes": [code]},
            "post_down": sample(occ, "post_down", True, b + 14),
            "client_keypress": {"event_type": 2, "keycode": code,
                "window_id": window, "send_event": False, "received_ns": b + 16},
            "app_counter_after_press": i + 1,
            "up_started_ns": b + 17, "up_result": None,
            "up_returned_ns": b + 18,
            "owner_release_result": {"event": "owner_release", "verified": True,
                "keys_down": [], "buttons_down": []},
            "owner_release_returned_ns": b + 19,
            "client_keyrelease": {"event_type": 3, "keycode": code,
                "window_id": window, "send_event": False, "received_ns": b + 20},
            "post_up": sample(occ, "post_up", False, b + 21),
            "owner_after_up": {"owner_id": owner, "owned_keycodes": []},
        })
    raw = {"schema": "v39-x11-client-effect-a02-v1", "source_sha256": "a" * 64,
        "xvfb_running_before_stop": True, "xvfb_returncode_after_stop": -15,
        "cleanup_errors": [], "app_counter_final": 2, "keycode": code,
        "window_id": window, "initial_owner_state": {"owner_id": owner,
            "focus": window, "owned_keycodes": []}, "cycles": cycles,
        "owner_records": [{"event": "owner_release", "reason": "release",
            "verified": True, "keys_down": [], "buttons_down": []} for _ in range(2)] +
            [{"event": "owner_release", "reason": "close", "verified": True,
              "keys_down": [], "buttons_down": []}]}
    return raw, {"input_owner_v10_sha256": "a" * 64}


class AuditTests(unittest.TestCase):
    def test_complete_focused_client_effect_passes(self):
        raw, freeze = fixture()
        self.assertEqual(validate(raw, freeze), [])

    def test_counter_without_received_press_fails(self):
        raw, freeze = fixture()
        raw["cycles"][0]["client_keypress"]["window_id"] += 1
        self.assertTrue(any("client keypress identity" in e for e in validate(raw, freeze)))

    def test_reordered_admission_fails(self):
        raw, freeze = fixture()
        raw["cycles"][0]["admission"]["admitted_ns"] = 5000
        raw["cycles"][0]["admission"]["input_ack_ns"] = 5001
        self.assertTrue(any("chronology" in e for e in validate(raw, freeze)))

    def test_duplicate_press_count_fails(self):
        raw, freeze = fixture()
        raw["cycles"][1]["app_counter_after_press"] = 1
        self.assertTrue(any("counter" in e for e in validate(raw, freeze)))

    def test_unverified_owner_release_fails(self):
        raw, freeze = fixture()
        raw["cycles"][0]["owner_release_result"]["verified"] = False
        self.assertTrue(any("release not verified" in e for e in validate(raw, freeze)))


if __name__ == "__main__":
    unittest.main()
