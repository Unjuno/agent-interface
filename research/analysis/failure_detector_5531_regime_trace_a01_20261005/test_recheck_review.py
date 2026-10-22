import unittest

from recheck_review import compare_streams


class ReviewRecheckTests(unittest.TestCase):
    def test_split_streams_must_match_observed_raw_projection(self):
        raw = [{"event": "heartbeat", "sequence": 0}]
        observed = [{"event": "heartbeat", "sequence": 0,
                     "observer_received_monotonic_ns": 101}]
        heartbeat = [{**raw[0], "observer_received_monotonic_ns": 101}]
        self.assertEqual([], compare_streams(raw, observed, heartbeat, []))
        self.assertIn(
            "heartbeat split differs from projected observed raw stream",
            compare_streams(raw, observed, [{**heartbeat[0], "sequence": 9}], []),
        )

    def test_stream_count_mismatch_fails(self):
        self.assertIn(
            "raw and observer event counts differ",
            compare_streams([{"event": "heartbeat"}], [], [], []),
        )


if __name__ == "__main__":
    unittest.main()

class ReconstructedBusyFormulaTests(unittest.TestCase):
    def test_inverse_corrects_the_double_counted_idle_formula(self):
        from recheck_regimes import corrected_busy_bounds, reconstructed_regime
        # I=30, K includes I and is 70, U=20: recorded B=75, actual busy=60/90.
        low, high = corrected_busy_bounds(75.0)
        self.assertLessEqual(low, 100 * (70 + 20 - 30) / (70 + 20))
        self.assertGreaterEqual(high, 100 * (70 + 20 - 30) / (70 + 20))
        self.assertEqual(reconstructed_regime(75.0), "elevated")

    def test_rounded_threshold_boundary_is_not_silently_classified(self):
        from recheck_regimes import reconstructed_regime
        self.assertEqual(reconstructed_regime(20000 / 300), "threshold_ambiguous")
        self.assertEqual(reconstructed_regime(66.666667), "threshold_ambiguous")
        self.assertEqual(reconstructed_regime(66.666668), "elevated")
        self.assertEqual(reconstructed_regime(66.666665), "ordinary")

    def test_post_manifest_path_list_is_not_used_if_worktree_is_mutated(self):
        import hashlib
        from recheck_regimes import authenticate_post_manifest
        sealed = b"sha256  retained.json\n"
        sidecar = (hashlib.sha256(sealed).hexdigest() + "  POST_AUDIT_SHA256SUMS.txt\n").encode()
        ok, errors = authenticate_post_manifest(sealed, sealed, sealed, sidecar, sidecar, sidecar)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

        altered = b"sha256  omitted-critical-file.json\n"
        ok, errors = authenticate_post_manifest(altered, sealed, sealed, sidecar, sidecar, sidecar)
        self.assertFalse(ok)
        self.assertIn("post-audit manifest differs across worktree, index, and HEAD", errors)
        self.assertIn("post-audit manifest does not match its sidecar", errors)
