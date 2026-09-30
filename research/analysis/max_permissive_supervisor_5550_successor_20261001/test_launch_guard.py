import unittest
from datetime import datetime, timezone

from launch_guard import assess


class LaunchGuardTests(unittest.TestCase):
    def setUp(self):
        self.freeze = {
            "allocation": "successor-03",
            "frozen_main": "abc123",
            "execution_lease": {
                "assigned": True,
                "coordinator_comment_id": "123456",
                "owner": "Unjuno",
                "start_utc": "2026-10-01T16:00:00Z",
                "end_utc": "2026-10-01T16:15:00Z",
                "image_digest": "sha256:abc",
                "platform": "linux/arm64",
            },
        }
        self.now = datetime(2026, 10, 1, 16, 0, tzinfo=timezone.utc)
        self.kwargs = dict(current_main="abc123", image_digest="sha256:abc",
                           platform="linux/arm64", running_containers=[], now=self.now)

    def test_exact_assigned_window_start_is_allowed(self):
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "PASS_PRELAUNCH_GATE")

    def test_missing_assignment_fails_closed(self):
        self.freeze["execution_lease"]["assigned"] = False
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_NO_EXPLICIT_ASSIGNMENT")

    def test_assignment_without_provenance_fails_closed(self):
        del self.freeze["execution_lease"]["coordinator_comment_id"]
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_ASSIGNMENT_PROVENANCE_INCOMPLETE")

    def test_wrong_main_fails_closed(self):
        self.kwargs["current_main"] = "different"
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_MAIN_MISMATCH")

    def test_wrong_digest_or_platform_fails_closed(self):
        self.kwargs["image_digest"] = "sha256:other"
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_IMAGE_OR_PLATFORM_MISMATCH")

    def test_active_container_fails_closed(self):
        self.kwargs["running_containers"] = ["owned-by-other-task"]
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_RESOURCE_OCCUPIED")

    def test_before_window_fails_closed(self):
        self.kwargs["now"] = datetime(2026, 10, 1, 15, 59, 59, tzinfo=timezone.utc)
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_OUTSIDE_ASSIGNED_WINDOW")

    def test_end_boundary_is_exclusive(self):
        self.kwargs["now"] = datetime(2026, 10, 1, 16, 15, tzinfo=timezone.utc)
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_OUTSIDE_ASSIGNED_WINDOW")

    def test_naive_time_is_rejected_by_cli_parser(self):
        from launch_guard import parse_utc
        with self.assertRaises(ValueError):
            parse_utc("2026-10-01T16:00:00")


if __name__ == "__main__":
    unittest.main()
