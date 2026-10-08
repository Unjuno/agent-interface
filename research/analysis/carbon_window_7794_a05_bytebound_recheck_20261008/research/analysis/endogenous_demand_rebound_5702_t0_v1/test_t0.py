import copy
import unittest

import audit
import candidate


class EndogenousDemandReboundTests(unittest.TestCase):
    def test_fixed_workload_cost_improves_without_extensive_margin(self):
        raw = candidate.build()
        summaries = {(x["case_id"], x["route"]): x for x in raw["summaries"]}
        slow = summaries[("no_rebound", "slow")]
        fast = summaries[("no_rebound", "fast")]
        self.assertEqual((slow["started"], fast["started"]), (2, 2))
        self.assertEqual((slow["completed"], fast["completed"]), (1, 1))
        self.assertEqual((slow["unknown_started"], fast["unknown_started"]), (1, 1))
        self.assertLess(fast["resource_spend"], slow["resource_spend"])

    def test_beneficial_expansion_control(self):
        s = {(x["case_id"], x["route"]): x for x in candidate.build()["summaries"]}
        self.assertGreater(s[("beneficial_expansion", "fast")]["verified_net_useful_value"],
                           s[("beneficial_expansion", "slow")]["verified_net_useful_value"])

    def test_adverse_mix_control_preserves_offered_denominator(self):
        raw = candidate.build()
        rows = [r for r in raw["rows"] if r["case_id"] == "adverse_mix"]
        self.assertEqual(sum(r["offered"] for r in rows), 8)
        summaries = {(x["case_id"], x["route"]): x for x in raw["summaries"]}
        self.assertLess(summaries[("adverse_mix", "fast")]["verified_net_useful_value"],
                        summaries[("adverse_mix", "slow")]["verified_net_useful_value"])

    def test_forbidden_high_value_row_never_starts(self):
        self.assertTrue(all(not r["started"] for r in candidate.build()["rows"] if not r["safe"]))

    def test_independent_auditor_and_eight_controls(self):
        result = audit.audit(candidate.build())
        self.assertEqual((result["status"], result["corruption_controls_passed"], result["errors"]),
                         ("PASS", 8, []))

    def test_auditor_rejects_unmatched_opportunity_denominator(self):
        raw = candidate.build()
        raw["rows"].pop()
        self.assertEqual(audit.audit(raw)["status"], "FAIL")

    def test_candidate_cli_emits_json(self):
        import json
        import subprocess
        import sys
        from pathlib import Path
        output = subprocess.check_output([sys.executable, str(Path(candidate.__file__))], text=True)
        self.assertEqual(json.loads(output)["schema"], "endogenous-demand-rebound-5702-t0-v1")

    def test_raw_only_auditor_cli(self):
        import json
        import subprocess
        import sys
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "candidate.json"
            raw.write_text(json.dumps(candidate.build()), encoding="utf-8")
            output = subprocess.check_output([sys.executable, str(Path(audit.__file__)), str(raw)], text=True)
        self.assertEqual(json.loads(output)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
