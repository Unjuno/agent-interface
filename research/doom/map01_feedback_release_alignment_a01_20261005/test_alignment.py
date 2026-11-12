import unittest

from alignment import owner_keyup_bracket, temporal_relation, useful_onset_bounds


def sample(start, finish, kills):
    return {"sample_started_ns": start, "sample_finished_ns": finish,
            "payload": {"kill_count": kills}}


def release(start, finish):
    return {
        "event": "input_release_transition",
        "owner_thread_keyup_verified": True,
        "physical_verification_authoritative": False,
        "owner_thread_keyup_receipt": {
            "server_sync_completed": True,
            "physical_verification_authoritative": False,
            "owner_keyrelease_started_ns": start,
            "owner_sync_returned_ns": finish,
        },
    }


class AlignmentTests(unittest.TestCase):
    def test_bounds_onset_by_sample_windows(self):
        self.assertEqual(useful_onset_bounds(sample(10, 12, 0), sample(20, 23, 1),
                                             field="kill_count"), (10, 23))

    def test_requires_positive_transition(self):
        with self.assertRaisesRegex(ValueError, "positive transition"):
            useful_onset_bounds(sample(10, 12, 1), sample(20, 23, 1), field="kill_count")

    def test_rejects_overlapping_sample_windows(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            useful_onset_bounds(sample(10, 21, 0), sample(20, 23, 1), field="kill_count")

    def test_requires_integer_timestamps(self):
        row = sample(10, 12, 0)
        row["sample_started_ns"] = True
        with self.assertRaisesRegex(ValueError, "integer"):
            useful_onset_bounds(row, sample(20, 23, 1), field="kill_count")

    def test_reads_owner_sync_bracket(self):
        self.assertEqual(owner_keyup_bracket(release(30, 35)), (30, 35))

    def test_rejects_unverified_or_authoritative_release(self):
        row = release(30, 35)
        row["owner_thread_keyup_verified"] = False
        with self.assertRaisesRegex(ValueError, "not verified"):
            owner_keyup_bracket(row)
        row = release(30, 35)
        row["owner_thread_keyup_receipt"]["physical_verification_authoritative"] = True
        with self.assertRaisesRegex(ValueError, "explicitly false"):
            owner_keyup_bracket(row)

    def test_classifies_clear_ordering(self):
        self.assertEqual(temporal_relation((10, 20), (30, 35)),
                         "useful_outcome_observed_before_keyup_request")
        self.assertEqual(temporal_relation((40, 50), (30, 35)),
                         "useful_outcome_observed_after_keyup_sync")

    def test_keeps_overlap_unresolved(self):
        self.assertEqual(temporal_relation((20, 40), (30, 35)),
                         "temporally_overlapping_or_unresolved")


if __name__ == "__main__":
    unittest.main(verbosity=2)
