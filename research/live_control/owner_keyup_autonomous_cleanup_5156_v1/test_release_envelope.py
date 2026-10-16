import unittest

from release_envelope import ReleaseCaptureError, record_release_envelopes
from audit import audit
from source_audit import classify
import json
from pathlib import Path
from tempfile import TemporaryDirectory


class FakeClock:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


class ReleaseEnvelopeTests(unittest.TestCase):
    def test_one_key_explicit_release_bracket(self):
        records = record_release_envelopes(
            display="display", owned_keys=[("a", 38)], owner_id="owner-1",
            intent_token="intent-1", reason="explicit_up", trigger_class="explicit_up",
            key_release=lambda _d, _code: None, sync=lambda _d: None,
            clock_ns=FakeClock([1, 2, 3]),
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["shared_sync_returned_ns"], 3)

    def test_two_owned_keys_keep_order_and_share_one_sync_boundary(self):
        calls = []
        records = record_release_envelopes(
            display="display",
            owned_keys=[("a", 38), ("b", 56)],
            owner_id="owner-1",
            intent_token="intent-1",
            reason="cancelled",
            trigger_class="owner_loop",
            key_release=lambda d, code: calls.append(("release", d, code)),
            sync=lambda d: calls.append(("sync", d)),
            clock_ns=FakeClock([10, 20, 30, 40, 50]),
        )

        self.assertEqual(calls, [
            ("release", "display", 38),
            ("release", "display", 56),
            ("sync", "display"),
        ])
        self.assertEqual(records, [
            {
                "event": "owner_key_release_bracket",
                "schema": "owner-key-release-bracket-v1",
                "owner_id": "owner-1",
                "intent_token": "intent-1",
                "reason": "cancelled",
                "trigger_class": "owner_loop",
                "key": "a",
                "keycode": 38,
                "request_started_ns": 10,
                "request_returned_ns": 20,
                "shared_sync_returned_ns": 50,
                "grants_input_authority": False,
                "physical_key_up_claimed": False,
            },
            {
                "event": "owner_key_release_bracket",
                "schema": "owner-key-release-bracket-v1",
                "owner_id": "owner-1",
                "intent_token": "intent-1",
                "reason": "cancelled",
                "trigger_class": "owner_loop",
                "key": "b",
                "keycode": 56,
                "request_started_ns": 30,
                "request_returned_ns": 40,
                "shared_sync_returned_ns": 50,
                "grants_input_authority": False,
                "physical_key_up_claimed": False,
            },
        ])

    def test_sync_error_never_returns_successful_release_records(self):
        calls = []

        def fail_sync(_display):
            calls.append("sync")
            raise OSError("sync failed")

        with self.assertRaises(ReleaseCaptureError) as caught:
            record_release_envelopes(
                display="display",
                owned_keys=[("a", 38)],
                owner_id="owner-1",
                intent_token="intent-1",
                reason="expired",
                trigger_class="owner_loop",
                key_release=lambda d, code: calls.append(("release", d, code)),
                sync=fail_sync,
                clock_ns=FakeClock([10, 20]),
            )

        self.assertEqual(calls, [("release", "display", 38), "sync"])
        self.assertEqual(caught.exception.stage, "sync")
        self.assertEqual(caught.exception.completed_records, [])

    def test_inverted_monotonic_bracket_never_returns_successful_record(self):
        with self.assertRaises(ReleaseCaptureError) as caught:
            record_release_envelopes(
                display="display",
                owned_keys=[("a", 38)],
                owner_id="owner-1",
                intent_token="intent-1",
                reason="stop_requested",
                trigger_class="owner_stop",
                key_release=lambda _d, _code: None,
                sync=lambda _d: None,
                clock_ns=FakeClock([20, 10, 30]),
            )

        self.assertEqual(caught.exception.stage, "clock_order")
        self.assertEqual(caught.exception.completed_records, [])

    def test_empty_owned_set_still_flushes_once_without_fabricating_edges(self):
        calls = []
        records = record_release_envelopes(
            display="display",
            owned_keys=[],
            owner_id="owner-1",
            intent_token=None,
            reason="thread_exit",
            trigger_class="thread_finalizer",
            key_release=lambda d, code: calls.append((d, code)),
            sync=lambda d: calls.append(("sync", d)),
            clock_ns=FakeClock([10]),
        )

        self.assertEqual(records, [])
        self.assertEqual(calls, [("sync", "display")])

    def test_request_failure_has_no_success_receipt(self):
        def fail_release(_display, _code):
            raise OSError("request failed")

        with self.assertRaises(ReleaseCaptureError) as caught:
            record_release_envelopes(
                display="display", owned_keys=[("a", 38)], owner_id="owner-1",
                intent_token="intent-1", reason="expired", trigger_class="owner_loop",
                key_release=fail_release, sync=lambda _d: None, clock_ns=FakeClock([10]),
            )
        self.assertEqual(caught.exception.stage, "key_release")
        self.assertEqual(caught.exception.completed_records, [])

    def test_auditor_rejects_temporal_and_claim_corruption(self):
        row = {
            "event": "owner_key_release_bracket", "schema": "owner-key-release-bracket-v1",
            "owner_id": "o", "intent_token": "i", "reason": "cancel",
            "trigger_class": "owner_loop", "key": "a", "keycode": 38,
            "request_started_ns": 10, "request_returned_ns": 20,
            "shared_sync_returned_ns": 30, "grants_input_authority": False,
            "physical_key_up_claimed": False,
        }
        with TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.assertEqual(audit(path), [])
            row["shared_sync_returned_ns"] = 5
            row["physical_key_up_claimed"] = True
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            errors = audit(path)
        self.assertIn("row_0:time_order", errors)
        self.assertIn("row_0:overclaim", errors)

    def test_frozen_auditor_corruption_matrix(self):
        nominal = {
            "event": "owner_key_release_bracket", "schema": "owner-key-release-bracket-v1",
            "owner_id": "o", "intent_token": "i", "reason": "cancel",
            "trigger_class": "owner_loop", "key": "a", "keycode": 38,
            "request_started_ns": 10, "request_returned_ns": 20,
            "shared_sync_returned_ns": 30, "grants_input_authority": False,
            "physical_key_up_claimed": False,
        }
        mutations = {
            "missing_identity": lambda row: row.pop("owner_id"),
            "wrong_event": lambda row: row.update(event="not_a_release"),
            "wrong_schema": lambda row: row.update(schema="unknown"),
            "empty_reason": lambda row: row.update(reason=""),
            "inverted_clock": lambda row: row.update(shared_sync_returned_ns=5),
            "authority_claim": lambda row: row.update(grants_input_authority=True),
            "physical_edge_claim": lambda row: row.update(physical_key_up_claimed=True),
            "bad_keycode": lambda row: row.update(keycode="38"),
        }
        with TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            for name, mutate in mutations.items():
                with self.subTest(mutation=name):
                    row = dict(nominal)
                    mutate(row)
                    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
                    self.assertTrue(audit(path), name)

    def test_autonomous_cancel_expiry_focus_stop_and_finalizer_labels(self):
        cases = [
            ("cancelled", "owner_cancel"),
            ("expired", "owner_expiry"),
            ("focus_changed", "owner_focus_invalidation"),
            ("stop_requested", "owner_stop"),
            ("thread_exit", "thread_finalizer"),
        ]
        for reason, trigger in cases:
            with self.subTest(reason=reason):
                records = record_release_envelopes(
                    display="display", owned_keys=[("a", 38)], owner_id="owner-1",
                    intent_token="intent-1", reason=reason, trigger_class=trigger,
                    key_release=lambda _d, _code: None, sync=lambda _d: None,
                    clock_ns=FakeClock([10, 20, 30]),
                )
                self.assertEqual(records[0]["reason"], reason)
                self.assertEqual(records[0]["trigger_class"], trigger)

    def test_pinned_owner_callsite_static_classification(self):
        here = Path(__file__).resolve().parent
        source_dir = here.parent
        result = classify(source_dir / "input_owner_v10.py", source_dir / "input_transition_owner_v3.py")
        self.assertTrue(result["ok"], result)
        self.assertEqual([c["class"] for c in result["callsites"]], [
            "owner_stop", "owner_lease_cleanup",
            "queued_explicit_release_or_close", "conditional_thread_finalizer",
        ])


if __name__ == "__main__":
    unittest.main()
