import unittest

import runner


class T10ConstructionTests(unittest.TestCase):
    def test_trace_cardinality(self):
        rows = runner.build_records()
        self.assertEqual(sum(row["kind"] == "trace" for row in rows), 780)
        self.assertEqual(sum(row["kind"] == "control" for row in rows), 8)

    def test_declared_bound_is_inclusive(self):
        row = next(r for r in runner.build_records()
                   if r.get("case") == "bound-edge-3")
        self.assertEqual((row["candidate_permits"], row["yield_reason"]), (1, None))

    def test_first_observed_breach_stops_before_action(self):
        row = next(r for r in runner.build_records()
                   if r.get("case") == "breach-edge-4")
        self.assertEqual((row["candidate_permits"], row["yield_index"]), (0, 0))

    def test_breach_is_sticky_without_rearm(self):
        row = next(r for r in runner.build_records()
                   if r.get("case") == "no-silent-rearm")
        self.assertEqual((row["candidate_permits"], row["yield_reason"]), (0, "out_of_bound"))

    def test_current_critical_event_overrides_inside_bound(self):
        row = next(r for r in runner.build_records()
                   if r.get("case") == "critical-after-safe")
        self.assertEqual((row["candidate_permits"], row["yield_index"], row["yield_reason"]),
                         (1, 1, "critical_override"))

    def test_generation_change_does_not_rearm(self):
        row = next(r for r in runner.build_records()
                   if r.get("case") == "generation-change")
        self.assertEqual((row["candidate_permits"], row["yield_reason"]),
                         (1, "generation_mismatch"))

    def test_gap_and_duplicate_fail_closed(self):
        rows = {r["case"]: r for r in runner.build_records() if r["kind"] == "control"}
        self.assertEqual(rows["sequence-gap"]["yield_reason"], "sequence_gap")
        self.assertEqual(rows["duplicate-sequence"]["yield_reason"], "sequence_gap")

    def test_every_candidate_post_breach_permit_is_zero(self):
        rows = [r for r in runner.build_records() if r["kind"] == "trace"]
        self.assertTrue(all(r["candidate_post_breach_permits"] == 0 for r in rows))


if __name__ == "__main__":
    unittest.main()

