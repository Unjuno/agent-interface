import json
import unittest
from pathlib import Path

import auditor
import candidate

FIXTURE=json.loads((Path(__file__).parent/"fixture.json").read_text())


class CurveTests(unittest.TestCase):
    def test_raw_denominator_reconstructs(self):
        raw=candidate.run(FIXTURE)
        self.assertEqual(auditor.inspect(FIXTURE,raw)["errors"],[])

    def test_setup_delta_and_learning_crossing(self):
        raw=candidate.run(FIXTURE)
        audit=auditor.inspect(FIXTURE,raw)
        crossings={r["scenario"]:r["first_comparable_wall_break_even_prefix"] for r in audit["crossings"]}
        self.assertEqual(crossings["zero_delta"],0)
        self.assertIsNone(crossings["setup_dominates"])
        self.assertEqual(crossings["learning_crosses_at_5"],5)
        self.assertIsNone(crossings["unsupported_host"])

    def test_failures_and_unsupported_do_not_become_success(self):
        raw=candidate.run(FIXTURE)
        audit=auditor.inspect(FIXTURE,raw)
        self.assertEqual(audit["setup_failures"],1)
        self.assertEqual(audit["wrong_or_unverified_attempts"],1)
        self.assertEqual(audit["route_ineligible_attempts"],1)
        self.assertEqual(audit["unsupported_host_successes"],0)

    def test_change_repair_is_included(self):
        raw=candidate.run(FIXTURE)
        row=next(r for r in raw if r["scenario"]=="app_change_repair" and r["route"]=="guarded" and r["prefix"]==3)
        self.assertEqual(row["wall_s"],38)
        self.assertEqual(row["active_s"],20)

    def test_no_followup_keeps_setup_cost(self):
        raw=candidate.run(FIXTURE)
        row=next(r for r in raw if r["scenario"]=="no_followup" and r["route"]=="guarded" and r["prefix"]==0)
        self.assertEqual(row["cumulative_wall_s"],40)
        self.assertEqual(row["verified_count"],0)

    def test_corruption_controls(self):
        raw=candidate.run(FIXTURE)
        for kind in ("drop_setup_failure","attempt_as_success","unsupported_success","drop_setup_cost","repair_free"):
            with self.subTest(kind=kind):
                self.assertTrue(auditor.inspect(FIXTURE,auditor.corrupt(raw,kind))["errors"])


if __name__=="__main__": unittest.main()
