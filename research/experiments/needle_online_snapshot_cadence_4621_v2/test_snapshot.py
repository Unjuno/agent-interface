import copy
import hashlib
import json
import unittest

import runner


class SnapshotContractTests(unittest.TestCase):
    def valid(self):
        return runner.seal_snapshot({
            "schema": runner.SNAPSHOT_SCHEMA,
            "allocation": runner.ALLOCATION,
            "schedule_version": runner.SCHEDULE_VERSION,
            "seed": 77111,
            "role": "B",
            "base_sha256": "a" * 64,
            "schedule_sha256": "b" * 64,
            "cursor": 4,
            "adapter": {"a": [[0.0]], "b": [[0.0]]},
            "optimizer": {"step": 32, "exp_avg_a": [[0.0]], "exp_avg_sq_a": [[0.0]],
                          "exp_avg_b": [[0.0]], "exp_avg_sq_b": [[0.0]]},
        })

    def test_valid_snapshot_is_accepted(self):
        runner.validate_snapshot(self.valid(), seed=77111, base_sha="a" * 64,
                                  schedule_sha="b" * 64, expected_cursor=4)

    def test_corruption_is_rejected(self):
        state = self.valid()
        state["adapter"]["a"][0][0] = 1.0
        with self.assertRaises(ValueError):
            runner.validate_snapshot(state, 77111, "a" * 64, "b" * 64, 4)

    def test_stale_duplicate_and_skipped_cursor_are_rejected(self):
        for cursor in (3, 4, 6):
            with self.subTest(cursor=cursor):
                state = self.valid()
                state["cursor"] = cursor
                state["snapshot_sha256"] = runner.snapshot_digest(state)
                with self.assertRaises(ValueError):
                    runner.validate_snapshot(state, 77111, "a" * 64, "b" * 64, 5)

    def test_incompatible_identity_is_rejected(self):
        state = self.valid()
        state["role"] = "A"
        state["snapshot_sha256"] = runner.snapshot_digest(state)
        with self.assertRaises(ValueError):
            runner.validate_snapshot(state, 77111, "a" * 64, "b" * 64, 4)


if __name__ == "__main__":
    unittest.main()

