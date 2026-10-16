"""Deterministic protocol-construction controls; no X11 or input is used."""
import unittest

from release_protocol_v2 import ProtocolError, validate_receipt, validate_stream


def explicit(seq=1, key="Down", request="req-1", start=100, owner_start=110,
             owner_end=120, returned=130, before=True, after=False):
    return {
        "schema": "owner-keyup-release-v2", "release_kind": "explicit_client_up",
        "operation": "up", "request_id": request, "release_reason": None,
        "owner_id": "owner-a", "intent_token": "intent-a", "key": key,
        "owner_sequence": seq, "caller_started_ns": start,
        "owner_release_started_ns": owner_start, "owner_sync_returned_ns": owner_end,
        "caller_returned_ns": returned, "owned_before": before,
        "owned_after": after, "grants_input_authority": False,
    }


def autonomous(seq=1, key="Down", reason="cancelled", start=110, end=120):
    return {
        "schema": "owner-keyup-release-v2", "release_kind": "autonomous_cleanup",
        "operation": None, "request_id": None, "release_reason": reason,
        "owner_id": "owner-a", "intent_token": "intent-a", "key": key,
        "owner_sequence": seq, "owner_release_started_ns": start,
        "owner_sync_returned_ns": end, "owned_before": True, "owned_after": False,
        "grants_input_authority": False,
    }


class ReleaseProtocolTests(unittest.TestCase):
    def test_explicit_single_key_release_has_nested_owner_bracket(self):
        row = explicit()
        self.assertIs(validate_receipt(row), row)

    def test_two_key_explicit_release_order_is_preserved(self):
        rows = [explicit(1, "Down", "batch-1", 100, 110, 120, 130),
                explicit(2, "space", "batch-1", 131, 140, 150, 160)]
        result = validate_stream(rows)
        self.assertEqual((result["explicit_receipts"], result["autonomous_receipts"]), (2, 0))

    def test_partial_cancel_records_only_the_admitted_key_as_autonomous(self):
        rows = [autonomous(1, "Down", "cancelled")]
        result = validate_stream(rows)
        self.assertEqual(result["receipt_count"], 1)
        self.assertEqual(rows[0]["key"], "Down")  # unadmitted `space` has no receipt

    def test_autonomous_release_is_not_falsely_wrapped_by_later_caller(self):
        row = autonomous()
        row["caller_started_ns"] = 90
        row["caller_returned_ns"] = 200
        with self.assertRaisesRegex(ProtocolError, "fabricated caller bracket"):
            validate_receipt(row)

    def test_unknown_autonomous_reason_fails_closed(self):
        row = autonomous(reason="mystery")
        with self.assertRaisesRegex(ProtocolError, "reason missing or unknown"):
            validate_receipt(row)

    def test_stale_explicit_up_cannot_claim_physical_release(self):
        with self.assertRaisesRegex(ProtocolError, "owned-to-empty"):
            validate_receipt(explicit(before=False))

    def test_owner_timestamp_inversion_is_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "owner timestamps inverted"):
            validate_receipt(explicit(owner_start=121, owner_end=120))

    def test_explicit_bracket_must_nest_in_its_exact_caller(self):
        with self.assertRaisesRegex(ProtocolError, "escapes explicit caller"):
            validate_receipt(explicit(owner_start=131, owner_end=140, returned=135))

    def test_owner_sequence_must_increase(self):
        with self.assertRaisesRegex(ProtocolError, "stream order is not increasing"):
            validate_stream([explicit(2), explicit(1, "space", "req-2")])

    def test_duplicate_explicit_receipt_identity_is_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "duplicate explicit release identity"):
            validate_stream([explicit(1), explicit(2)])

    def test_owner_errors_are_not_mislabeled_as_release_receipts(self):
        row = explicit()
        row["owner_sync_returned_ns"] = None
        with self.assertRaisesRegex(ProtocolError, "owner release bracket missing"):
            validate_receipt(row)

    def test_authority_flag_cannot_be_promoted(self):
        row = autonomous()
        row["grants_input_authority"] = True
        with self.assertRaisesRegex(ProtocolError, "authority flag"):
            validate_receipt(row)


if __name__ == "__main__":
    unittest.main(verbosity=2)
