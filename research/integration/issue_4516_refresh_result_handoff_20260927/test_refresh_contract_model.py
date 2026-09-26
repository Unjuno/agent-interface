import unittest


MAX_HORIZON_NS = 30_000_000_000
REQUIRED_MARGIN_NS = 5_000_000_000


def admit_refresh(now_ns, deadline_ns, probe_durations_ns):
    if len(probe_durations_ns) != 3:
        raise ValueError("exactly three clock probes required")
    translated_now = now_ns + sum(probe_durations_ns)
    remaining = deadline_ns - translated_now
    if remaining <= 0:
        return "rejected_expired", remaining
    if deadline_ns - now_ns > MAX_HORIZON_NS:
        return "rejected_over_30s", remaining
    if remaining < REQUIRED_MARGIN_NS:
        return "hold_margin_below_5s", remaining
    return "accepted", remaining


def valid_observe_terminal(terminal):
    release = terminal.get("release", {})
    return (terminal.get("status") == "completed" and
            release.get("verified") is True and
            release.get("keys_down") == [] and
            release.get("buttons_down") == [])


class RefreshLeaseContractModelTests(unittest.TestCase):
    def test_15_second_refresh_survives_three_clock_probes(self):
        status, remaining = admit_refresh(
            1_000, 15_000_001_000, [10_000_000] * 3)
        self.assertEqual(status, "accepted")
        self.assertGreaterEqual(remaining, REQUIRED_MARGIN_NS)

    def test_expired_refresh_rejects(self):
        status, _ = admit_refresh(2_000, 1_000, [1, 1, 1])
        self.assertEqual(status, "rejected_expired")

    def test_horizon_over_30_seconds_rejects(self):
        status, _ = admit_refresh(
            1_000, 31_000_001_000, [10_000_000] * 3)
        self.assertEqual(status, "rejected_over_30s")

    def test_post_probe_margin_below_five_seconds_holds(self):
        status, _ = admit_refresh(0, 5_000_000_000, [1, 1, 1_001])
        self.assertEqual(status, "hold_margin_below_5s")

    def test_only_completed_verified_empty_release_is_accepted(self):
        self.assertTrue(valid_observe_terminal({
            "status": "completed", "release": {
                "verified": True, "keys_down": [], "buttons_down": []}}))
        self.assertFalse(valid_observe_terminal({
            "status": "completed", "release": {
                "verified": False, "keys_down": [], "buttons_down": []}}))
        self.assertFalse(valid_observe_terminal({
            "status": "completed", "release": {
                "verified": True, "keys_down": ["w"], "buttons_down": []}}))
        self.assertFalse(valid_observe_terminal({
            "status": "running_action_invalidation", "release": {
                "verified": True, "keys_down": [], "buttons_down": []}}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
