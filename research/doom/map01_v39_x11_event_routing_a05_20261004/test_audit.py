"""Mutation controls for A05 client event evidence."""
import copy
import unittest

from audit import validate


def sample(stage, down, start, code=25):
    bits = bytearray(32)
    if down:
        bits[code // 8] |= 1 << (code % 8)
    return {"stage": stage, "sample_started_ns": start, "sample_finished_ns": start + 1,
            "bitmap_length": 32, "bitmap_hex": bytes(bits).hex(), "keycode": code,
            "key_down": down, "source": "independent Xlib Display.query_keymap",
            "physical_key_up_claimed": False}


def fixture():
    code, window = 25, 100
    direct = {"occurrence_id": "direct", "method": "direct XTEST control",
              "counter_before": 0, "pre_down": sample("pre_down", False, 10),
              "down_started_ns": 12, "down_returned_ns": 13,
              "post_down": sample("post_down", True, 14),
              "client_events_after_down": [{"event_type": 2, "keycode": code,
                 "window_id": window, "send_event": False, "received_ns": 16,
                 "target_match": True}],
              "counter_after_down": 1, "up_started_ns": 17, "up_returned_ns": 18,
              "client_events_after_up": [{"event_type": 3, "keycode": code,
                 "window_id": window, "send_event": False, "received_ns": 19,
                 "target_match": True}],
              "post_up": sample("post_up", False, 20), "counter_after_up": 1}
    owner = {"occurrence_id": "owner", "method": "InputOwner v10", "intent_token": "a05:owner",
             "owner_id": "owner-1", "counter_before": 1,
             "pre_down": sample("pre_down", False, 30), "down_started_ns": 32,
             "admission": {"event": "input_admission", "key": "w", "admitted_ns": 33,
                           "input_ack_ns": 34}, "down_returned_ns": 35,
             "owner_after_down": {"owner_id": "owner-1", "owned_keycodes": [code]},
             "post_down": sample("post_down", True, 36),
             "client_events_after_down": [{"event_type": 2, "keycode": code,
                 "window_id": window, "send_event": False, "received_ns": 38,
                 "target_match": True}], "counter_after_down": 2,
             "up_started_ns": 40, "up_result": None, "up_returned_ns": 41,
             "release_result": {"event": "owner_release", "verified": True,
                 "keys_down": [], "buttons_down": []},
             "client_events_after_up": [{"event_type": 3, "keycode": code,
                 "window_id": window, "send_event": False, "received_ns": 43,
                 "target_match": True}], "post_up": sample("post_up", False, 44),
             "owner_after_up": {"owner_id": "owner-1", "owned_keycodes": []},
             "counter_after_up": 2, "release_returned_ns": 42}
    owner["client_events_after_up"][0]["received_ns"] = 42
    owner["post_up"]["sample_started_ns"] = 44
    raw = {"schema": "v39-x11-event-routing-a05-v1", "candidate_invocations": 1,
           "candidate_complete": True, "failure": None, "source_sha256": "a"*64,
           "xvfb_running_before_stop": True, "xvfb_returncode_after_stop": -15,
           "cleanup_errors": [], "keycode": code, "window_id": window,
           "focus_id": window,
           "routes": {"direct_xtest": direct, "input_owner_v10": owner},
           "owner_records": [
               {"event": "owner_release", "reason": "release", "verified": True,
                "keys_down": [], "buttons_down": []},
               {"event": "owner_release", "reason": "close", "verified": True,
                "keys_down": [], "buttons_down": []}], "app_counter_final": 2}
    return raw, {"input_owner_v10_sha256": "a"*64}


class AuditTests(unittest.TestCase):
    def test_valid_route_pair_passes(self):
        raw, freeze = fixture()
        self.assertEqual(validate(raw, freeze), [])

    def test_missing_client_press_fails(self):
        raw, freeze = fixture()
        raw["routes"]["input_owner_v10"]["client_events_after_down"] = []
        self.assertTrue(any("press/release" in e for e in validate(raw, freeze)))

    def test_wrong_window_fails(self):
        raw, freeze = fixture()
        raw["routes"]["direct_xtest"]["client_events_after_down"][0]["window_id"] += 1
        self.assertTrue(any("press/release" in e for e in validate(raw, freeze)))

    def test_duplicate_client_events_fail(self):
        raw, freeze = fixture()
        row = copy.deepcopy(raw["routes"]["direct_xtest"]["client_events_after_down"][0])
        raw["routes"]["direct_xtest"]["client_events_after_down"].append(row)
        self.assertTrue(any("exactly two" in e for e in validate(raw, freeze)))

    def test_misordered_owner_admission_fails(self):
        raw, freeze = fixture()
        raw["routes"]["input_owner_v10"]["admission"]["admitted_ns"] = 900
        self.assertTrue(any("admission chronology" in e for e in validate(raw, freeze)))

    def test_owner_release_mismatch_fails(self):
        raw, freeze = fixture()
        raw["routes"]["input_owner_v10"]["release_result"]["verified"] = False
        self.assertTrue(any("release not verified" in e for e in validate(raw, freeze)))


if __name__ == "__main__":
    unittest.main()
