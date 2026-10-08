import unittest

from audit_raw import audit


def valid_rows():
    return [
        {"event": "fixture", "evidence_mode": "synthetic-host"},
        {"event": "owner_release_request", "occurrence_id": "occ-1", "owner_id": "owner-1",
         "intent_token": "intent-1", "operation": "up", "key": "a", "keycode": 38,
         "event_type": "KeyRelease", "request_ns": 110, "thread_name": "input-owner",
         "grants_input_authority": False},
        {"event": "owner_sync_return", "occurrence_id": "occ-1", "owner_id": "owner-1",
         "intent_token": "intent-1", "operation": "up", "key": "a", "keycode": 38,
         "sync_return_ns": 120, "thread_name": "input-owner", "grants_input_authority": False},
        {"event": "caller_release_receipt", "occurrence_id": "occ-1", "owner_id": "owner-1",
         "intent_token": "intent-1", "operation": "up", "key": "a", "keycode": 38,
         "call_started_ns": 100, "call_returned_ns": 130, "interval_width_ns": 30,
         "x11_release_and_sync_completed_before_return": True,
         "continuous_physical_state_sampled": False, "application_consumption_observed": False,
         "grants_input_authority": False},
        {"event": "fake_key_state", "occurrence_id": "occ-1", "down_before": True,
         "down_after": False, "grants_input_authority": False},
        {"event": "terminal", "owner_stopped": True, "owner_thread_alive": False,
         "formal_x11": False, "container": False, "grants_input_authority": False},
    ]


class AuditTests(unittest.TestCase):
    def test_accepts_nested_identity_bound_synthetic_trace(self):
        self.assertEqual(audit(valid_rows())["decision"], "PASS_SYNTHETIC_OWNER_BRACKET_JOIN_SCOPED")

    def test_rejects_out_of_order_owner_request(self):
        rows = valid_rows()
        rows[1]["request_ns"] = 140
        self.assertIn("caller/owner event order is not nested", audit(rows)["errors"])

    def test_rejects_mismatched_intent(self):
        rows = valid_rows()
        rows[2]["intent_token"] = "other-intent"
        self.assertTrue(any("intent_token" in e for e in audit(rows)["errors"]))

    def test_rejects_missing_sync_return(self):
        rows = [r for r in valid_rows() if r["event"] != "owner_sync_return"]
        self.assertIn("expected exactly one owner sync return", audit(rows)["errors"])

    def test_rejects_duplicate_release_request(self):
        rows = valid_rows()
        rows.append(dict(rows[1]))
        self.assertIn("expected exactly one owner release request", audit(rows)["errors"])

    def test_rejects_key_left_down(self):
        rows = valid_rows()
        rows[4]["down_after"] = True
        self.assertIn("fake key state did not transition down to up", audit(rows)["errors"])

    def test_rejects_authority_or_scope_promotion(self):
        rows = valid_rows()
        rows[3]["grants_input_authority"] = True
        rows[5]["formal_x11"] = True
        self.assertTrue(any("grants input authority" in e for e in audit(rows)["errors"]))
        self.assertTrue(any("mislabeled" in e for e in audit(rows)["errors"]))

    def test_rejects_cross_occurrence_join(self):
        rows = valid_rows()
        rows[2]["occurrence_id"] = "occ-2"
        self.assertIn("occurrence identity is missing or inconsistent", audit(rows)["errors"])


if __name__ == "__main__":
    unittest.main()
