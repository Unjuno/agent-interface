import unittest

from temporal_protocol import Case, Observation, classify, decision, expected, gate, schedule


def frame(fill: int) -> bytes:
    return bytes([fill]) * (64 * 64 * 3)


class ProtocolTests(unittest.TestCase):
    def test_schedule_is_48_balanced_rows_and_rotates(self):
        rows = schedule()
        self.assertEqual(len(rows), 48)
        self.assertEqual([sum(c is case for _, c in rows) for case in Case], [8] * 6)
        self.assertEqual([case for _, case in rows[:6]], list(Case))
        self.assertEqual([case for _, case in rows[6:12]], list(Case)[1:] + list(Case)[:1])

    def test_gate_sees_only_equal_or_different_endpoints(self):
        row = Observation(Case.ABA_2X2, frame(0), frame(1), frame(0), 1)
        got = gate(row)
        self.assertFalse(got["endpoint_changed"])
        self.assertFalse(got["o1_forwards_endpoint"])
        self.assertFalse(got["middle_used_by_candidate"])
        self.assertFalse(got["action_authority"])
        self.assertEqual(got["damage_disposition"], "DAMAGE_OBSERVED")

    def test_repaint_damage_is_not_semantic_change(self):
        row = Observation(Case.REPAINT_A, frame(0), frame(0), frame(0), 1)
        self.assertEqual(classify(row), "DAMAGE_OBSERVED")
        self.assertFalse(gate(row)["endpoint_changed"])

    def test_zero_damage_only_supports_scoped_quiet_statement(self):
        quiet = Observation(Case.QUIET, frame(0), frame(0), frame(0), 0)
        aba = Observation(Case.ABA_1PX, frame(0), frame(1), frame(0), 0)
        self.assertEqual(classify(quiet), "NO_DAMAGE_OBSERVED_SCOPED")
        self.assertEqual(classify(aba), "UNKNOWN")

    def test_stale_identity_source_and_incomplete_coverage_yield_unknown(self):
        repaint = Observation(Case.REPAINT_A, frame(0), frame(0), frame(0), 1)
        self.assertEqual(classify(repaint, identity_valid=False), "UNKNOWN")
        self.assertEqual(classify(repaint, coverage_complete=False), "UNKNOWN")
        self.assertEqual(classify(repaint, source_fresh=False), "UNKNOWN")
        for row in (repaint,):
            self.assertFalse(gate(row)["action_authority"])

    def test_byte_and_identity_validation(self):
        with self.assertRaises(ValueError):
            Observation(Case.QUIET, b"x", b"x", b"x", 0).validate()
        with self.assertRaises(ValueError):
            Observation(Case.QUIET, frame(0), frame(0), frame(0), -1).validate()

    def test_formal_coverage_is_closed_world(self):
        self.assertEqual(decision([]), "HOLD_COVERAGE")
        quiet = Observation(Case.QUIET, frame(0), frame(0), frame(0), 0)
        self.assertNotEqual(decision([quiet] * 48), "PASS_XDAMAGE_TEMPORAL_BOUNDARY_V2_SCOPED")


if __name__ == "__main__":
    unittest.main()
