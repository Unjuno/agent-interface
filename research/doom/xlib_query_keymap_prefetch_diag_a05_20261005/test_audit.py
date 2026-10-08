import copy
import unittest

from audit import audit


def complete_raw():
    edges = []
    for label, kind, down, start in (("down", 2, True, 10), ("up", 3, False, 20)):
        edges.append({
            "label": label,
            "expected_key_down": down,
            "observed_key_down": down,
            "inject_started_ns": start,
            "inject_synced_ns": start + 1,
            "query_reply_returned_ns": start + 2,
            "queued_before_select": 1,
            "queued_snapshot_before_select": [{"class": "KeyPress", "type": kind,
                "detail": 38, "window_id": 99, "matches": True}],
            "target_prefetched_before_select": True,
            "socket_readable_after_queue_check": False,
            "pending_events_after_collection": 0,
            "event_rows": [{"class": "KeyPress", "type": kind, "detail": 38,
                            "window_id": 99, "matches": True}],
            "matched_event": {"class": "KeyPress", "type": kind, "detail": 38,
                              "window_id": 99, "matches": True},
        })
    return {
        "schema": "xlib-query-keymap-prefetch-a05-v1",
        "allocation_id": "MAP01-V39-XLIB-QUERY-PREFETCH-A05-20261005-02",
        "candidate_invocations": 1,
        "candidate_complete": True,
        "fixture": {"window_id": 99, "keycode": 38},
        "edges": edges,
        "cleanup": {"xvfb_stopped": True, "xvfb_exit": 0},
    }


class AuditorMutationTests(unittest.TestCase):
    def test_valid_trace_passes(self):
        self.assertEqual(audit(complete_raw())["status"], "PASS_QUEUE_PREFETCH_DIAGNOSTIC")

    def test_socket_readiness_means_no_prefetch_claim(self):
        raw = complete_raw()
        raw["edges"][0]["socket_readable_after_queue_check"] = True
        self.assertFalse(audit(raw)["checks"]["socket_not_readable"])

    def test_missing_internal_queue_receipt_fails(self):
        raw = complete_raw()
        raw["edges"][1]["queued_before_select"] = 0
        self.assertFalse(audit(raw)["checks"]["queue_prefetched"])

    def test_wrong_target_or_edge_fails(self):
        raw = complete_raw()
        raw["edges"][1]["matched_event"]["window_id"] = 100
        self.assertFalse(audit(raw)["checks"]["exact_client_events"])

    def test_noise_event_without_detail_is_preserved(self):
        raw = complete_raw()
        raw["edges"][0]["event_rows"].insert(0, {
            "class": "MappingNotify", "type": 34, "detail": None,
            "window_id": None, "matches": False,
        })
        self.assertEqual(audit(raw)["status"], "PASS_QUEUE_PREFETCH_DIAGNOSTIC")

    def test_target_missing_from_preselect_snapshot_fails(self):
        raw = complete_raw()
        raw["edges"][1]["target_prefetched_before_select"] = False
        raw["edges"][1]["queued_snapshot_before_select"] = []
        self.assertFalse(audit(raw)["checks"]["target_prefetched_before_select"])

    def test_keymap_and_cleanup_mutations_fail(self):
        raw = complete_raw()
        raw["edges"][0]["observed_key_down"] = False
        raw["cleanup"]["xvfb_exit"] = 9
        result = audit(raw)
        self.assertFalse(result["checks"]["keymap_sequence"])
        self.assertFalse(result["checks"]["clean_xvfb"])


if __name__ == "__main__":
    unittest.main()
