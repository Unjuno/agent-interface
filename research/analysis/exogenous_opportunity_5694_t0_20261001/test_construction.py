import json
import unittest

import audit
import candidate

FIXTURE_BYTES = candidate.FIXTURE.read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)


class OpportunityTests(unittest.TestCase):
    def test_every_case_retains_its_exogenous_denominator(self):
        rows = [row for case in FIXTURE["cases"]
                for row in candidate.run_case(case, FIXTURE["deadline_ticks"])]
        self.assertEqual(len(rows), 41)
        self.assertEqual(len({r["opportunity_id"] for r in rows}), 41)

    def test_busy_stall_witness_does_not_change_completed_cycle_p95(self):
        outputs = {}
        for case in FIXTURE["cases"][:2]:
            cr = candidate.run_case(case, FIXTURE["deadline_ticks"])
            outputs[case["case_id"]] = audit.metrics(cr, case)
        self.assertEqual(outputs["no_stall"]["completed_p95_ticks"], 2)
        self.assertEqual(outputs["busy_silent"]["completed_p95_ticks"], 2)
        self.assertEqual(outputs["no_stall"]["coverage"], 1.0)
        self.assertEqual(outputs["busy_silent"]["coverage"], 0.6)

    def test_safe_stop_and_unknown_clock_are_not_useful_or_timed(self):
        safe = candidate.run_case(FIXTURE["cases"][2], 4)
        unknown = candidate.run_case(FIXTURE["cases"][5], 4)
        self.assertEqual(sum(r["outcome"] == "SAFE_STOP" for r in safe), 4)
        self.assertTrue(all(r["latency_ticks"] is None for r in unknown))

    def test_deadline_expiry_and_serial_overlap(self):
        expiry = candidate.run_case(FIXTURE["cases"][3], 4)
        overlap = candidate.run_case(FIXTURE["cases"][4], 4)
        self.assertTrue(all(r["outcome"] == "LATE" for r in expiry))
        self.assertEqual(sum(r["outcome"] == "LATE" for r in overlap), 3)

    def test_auditor_rejects_four_corruptions(self):
        rows = [{"type": "header", "schema": "exogenous-opportunity-5694-raw-v1",
                 "allocation": audit.ALLOCATION,
                 "fixture_sha256": __import__("hashlib").sha256(FIXTURE_BYTES).hexdigest(),
                 "case_count": len(FIXTURE["cases"])}]
        for case in FIXTURE["cases"]:
            rows.extend(candidate.run_case(case, FIXTURE["deadline_ticks"]))
        result = audit.audit(FIXTURE, FIXTURE_BYTES, rows)
        self.assertFalse(result["errors"])
        self.assertEqual(result["corruption_controls_rejected"], 4)


if __name__ == "__main__":
    unittest.main()
