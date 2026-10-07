"""Emergency cleanup uses existing queries and retains only confirmed lineage.

Real owner threads, synthetic Xlib only. These are ordinary regression tests,
not physical input or performance measurements.
"""
import unittest
import threading

from test_input_owner_v12_key_measurement import KeyMeasurementTests, FakeLease
from executor_v3 import Cancelled, DecisionRequired
from lease import Expired


class CleanupMeasurementTests(unittest.TestCase):
    setUp = KeyMeasurementTests.setUp
    tearDown = KeyMeasurementTests.tearDown
    start_owner = KeyMeasurementTests.start_owner

    def admit(self, keys=("W", "A")):
        owner = self.start_owner()
        lease = FakeLease()
        admissions = {key: owner.call("down", lease, key) for key in keys}
        return owner, lease, admissions

    def cleanup_record(self, owner, lease):
        # The owner may process cancellation before dequeuing this barrier.
        owner.call("release", lease)
        return next(row for row in owner.records
                    if row.get("event") == "owner_release" and
                    any(v["attempts"] for v in row["key_release_attempts"].values()))

    def check_up(self, record, admission, code):
        measured = record["key_release_attempts"][str(code)].get("physical_key_measurement")
        self.assertIsInstance(measured, dict)
        down = admission["physical_key_measurement"]
        self.assertEqual(measured["classification"], "CONFIRMED_PHYSICAL_UP")
        for field in ("owner_id", "intent_token", "key", "actuation_id"):
            self.assertEqual(measured[field], down[field])
        self.assertEqual(measured["identity_status"], "RETIRED")
        self.assertEqual(measured["interval_basis"], "per_key_cleanup_snapshot")
        self.assertIsNone(measured["batch_id"])
        self.assertFalse(measured["grants_input_authority"])
        self.assertFalse(measured["application_consumption_observed"])
        pre, post = measured["pre_sample"], measured["post_sample"]
        self.assertLessEqual(pre["finished_ns"], measured["release_request_ns"])
        self.assertLessEqual(measured["sync_return_ns"], post["started_ns"])
        self.assertEqual(measured["bracket"]["physical_up_interval"],
                         [pre["finished_ns"], post["finished_ns"]])
        self.assertLessEqual(post["finished_ns"], record["verified_ns"])
        return measured

    def wait_for_cleanup(self, owner, lease, trigger, reason):
        recorded = threading.Event()
        original = lease.record_interruption
        def record(row):
            original(row)
            recorded.set()
        lease.record_interruption = record
        trigger()
        self.assertTrue(recorded.wait(1), 'owner watchdog did not record cleanup')
        row = lease.interruptions[0]
        self.assertEqual(row['reason'], reason)
        return row

    def test_cancel_before_explicit_up_retains_both_identities(self):
        owner, lease, admissions = self.admit()
        row = self.wait_for_cleanup(owner, lease, lease.cancel.set, 'cancelled')
        self.assertEqual(row["reason"], "cancelled")
        self.assertTrue(row["verified"])
        self.check_up(row, admissions["W"], 38)
        self.check_up(row, admissions["A"], 39)
        self.assertEqual(self.fake.down, set())
        # Repeated aggregate cleanup must not manufacture a second edge.
        again = owner.call("release", lease)
        self.assertEqual(again["key_release_attempts"], {})

    def test_expiry_cleanup_retains_identity(self):
        owner, lease, admissions = self.admit(("W",))
        row = self.wait_for_cleanup(owner, lease, lambda: setattr(lease, 'deadline', 0), 'expired')
        self.check_up(row, admissions["W"], 38)
        self.assertTrue(row["verified"])

    def test_focus_cleanup_retains_identity(self):
        owner, lease, admissions = self.admit(("W",))
        row = self.wait_for_cleanup(owner, lease, lambda: setattr(self.fake, 'focus', 42), 'focus_changed')
        self.check_up(row, admissions["W"], 38)
        self.assertTrue(row["verified"])

    def test_retry_retains_initial_pre_sample_and_identity(self):
        owner, lease, admissions = self.admit(("W",))
        self.fake.drop_counts[38] = 1
        row = self.cleanup_record(owner, lease)
        measured = self.check_up(row, admissions["W"], 38)
        attempts = row["key_release_attempts"]["38"]["attempts"]
        self.assertEqual(len(attempts), 2)
        self.assertEqual(measured["pre_sample"], attempts[0]["measurement_pre_sample"])
        self.assertEqual(measured["post_sample"], attempts[-1]["measurement_post_sample"])

    def test_partial_failed_cleanup_retains_confirmed_prefix_and_fences_input(self):
        owner, lease, admissions = self.admit()
        self.fake.persistent_drop_codes.add(39)
        with self.assertRaises(RuntimeError):
            owner.call("release", lease)
        row = next(r for r in owner.records if r.get("event") == "owner_release")
        self.assertFalse(row["verified"])
        self.check_up(row, admissions["W"], 38)
        failed = row["key_release_attempts"]["39"].get("physical_key_measurement")
        self.assertIsInstance(failed, dict)
        self.assertEqual(failed["classification"], "KEYMAP_EDGE_UNCONFIRMED")
        self.assertIsNone(failed["actuation_id"])
        presses_before = [x for x in self.fake.trace if x[:2] == ("key_event", 2)]
        with self.assertRaises(RuntimeError):
            owner.call("down", FakeLease("new-intent"), "S")
        self.assertEqual([x for x in self.fake.trace if x[:2] == ("key_event", 2)], presses_before)

    def test_unknown_initial_sample_does_not_become_confirmed(self):
        owner, lease, _ = self.admit(("W",))
        self.fake.fail_queries.add(self.fake.query_count + 1)
        row = self.cleanup_record(owner, lease)
        measured = row["key_release_attempts"]["38"].get("physical_key_measurement")
        self.assertIsInstance(measured, dict)
        self.assertEqual(measured["classification"], "KEYMAP_EDGE_UNCONFIRMED")
        self.assertIsNone(measured["bracket"])
        self.assertTrue(row["verified"])

    def test_already_up_does_not_create_cleanup_edge(self):
        owner, lease, _ = self.admit(("W",))
        self.fake.down.clear()  # External/no longer observed down: no edge claim.
        row = owner.call("release", lease)
        self.assertTrue(row["verified"])
        self.assertEqual(row["key_release_attempts"]["38"]["attempts"], [])
        self.assertNotIn("physical_key_measurement", row["key_release_attempts"]["38"])

    def late_batch(self, reason, trigger, exception):
        owner, lease, _ = self.admit(("W",))
        self.wait_for_cleanup(owner, lease, lambda: trigger(lease), reason)
        events_before = list(self.fake.trace)
        with self.assertRaises(exception):
            owner.call("up_batch", lease, ["W"])
        self.assertEqual(self.fake.trace, events_before, "late batch performed display I/O")

    def test_late_batch_preserves_cancelled_cause_without_io(self):
        self.late_batch("cancelled", lambda lease: lease.cancel.set(), Cancelled)

    def test_late_batch_preserves_expired_cause_without_io(self):
        self.late_batch("expired", lambda lease: setattr(lease, "deadline", 0), Expired)

    def test_late_batch_preserves_focus_cause_without_io(self):
        self.late_batch("focus_changed", lambda lease: setattr(self.fake, "focus", 42), DecisionRequired)

    def test_matching_token_on_different_lease_does_not_claim_cleanup(self):
        owner, lease, _ = self.admit(("W",))
        self.wait_for_cleanup(owner, lease, lease.cancel.set, "cancelled")
        impostor = FakeLease(lease.intent_token)
        impostor.cancel.set()
        with self.assertRaises(ValueError):
            owner.call("up_batch", impostor, ["W"])

    def test_old_lease_does_not_release_new_hold(self):
        owner, lease, _ = self.admit(("W",))
        self.wait_for_cleanup(owner, lease, lease.cancel.set, "cancelled")
        fresh = FakeLease("fresh-intent")
        owner.call("down", fresh, "A")
        with self.assertRaises(ValueError):
            owner.call("up_batch", lease, ["A"])
        self.assertEqual(self.fake.down, {39})

    def test_measurement_off_keeps_cleanup_uninstrumented(self):
        owner = self.start_owner(measure=False)
        lease = FakeLease()
        owner.call("down", lease, "W")
        self.fake.trace.clear()
        row = owner.call("release", lease)
        self.assertNotIn("physical_key_measurement", row["key_release_attempts"]["38"])
        self.assertNotIn("measurement_pre_sample", row["key_release_attempts"]["38"]["attempts"][0])
        self.assertEqual(sum(x[0] == "query_keymap" for x in self.fake.trace), 3)

    def test_measurement_on_adds_no_cleanup_keymap_queries(self):
        owner, lease, admissions = self.admit(("W",))
        self.fake.trace.clear()
        row = self.cleanup_record(owner, lease)
        self.check_up(row, admissions["W"], 38)
        self.assertEqual(sum(x[0] == "query_keymap" for x in self.fake.trace), 3)


if __name__ == "__main__":
    unittest.main()
