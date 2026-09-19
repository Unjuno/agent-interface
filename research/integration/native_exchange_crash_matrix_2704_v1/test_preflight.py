import tempfile
import unittest
from pathlib import Path

from preflight import LOSS_POINTS, audit_row, plan_case


class CrashMatrixPreflightTests(unittest.TestCase):
    def test_all_registered_loss_points_are_explicit_and_non_replayable(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = [plan_case(Path(directory), point) for point in LOSS_POINTS]
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["loss_point"] for row in rows}, set(LOSS_POINTS))
        self.assertTrue(all(row["replay_allowed"] is False for row in rows))
        self.assertTrue(all(row["authority_granted"] is False for row in rows))

    def test_unknown_emission_is_not_silently_completed(self):
        with tempfile.TemporaryDirectory() as directory:
            row = audit_row(plan_case(Path(directory), "during_owner_wait"),
                            emitted=True, reply_committed=False)
        self.assertEqual(row["outcome"], "emission_unknown")
        with self.assertRaises(ValueError):
            audit_row(plan_case(Path(directory), "during_owner_wait"),
                      emitted=False, reply_committed=True)


if __name__ == "__main__":
    unittest.main()
