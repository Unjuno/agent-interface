import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT.parents[2] / "research" / "live_control"))
for name in ("candidate","audit"):
    spec=importlib.util.spec_from_file_location(name,ROOT/f"{name}.py")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    globals()[name]=mod
FIXTURE=json.loads((ROOT/"fixture.json").read_text())


class TestWakeFenceConstruction(unittest.TestCase):
    def test_candidate_reconciles_with_independent_oracle(self):
        raw={"rows":[]}
        for scenario in FIXTURE["scenarios"]:
            raw["rows"].extend(candidate.evaluate(scenario,FIXTURE["ttl_ns"]))
        result=audit.audit(FIXTURE,raw)
        self.assertEqual(result["status"],"PASS_METHOD_SCOPED")
        self.assertEqual(result["rows_expected"],24)

    def test_long_gap_separates_relative_and_suspend_aware_clocks(self):
        rows=candidate.evaluate(next(s for s in FIXTURE["scenarios"] if s["id"]=="long_wake"),FIXTURE["ttl_ns"])
        self.assertEqual(rows[0]["outcome"],"LIVE")
        self.assertEqual(rows[1]["outcome"],"EXPIRED")
        self.assertEqual(rows[2]["outcome"],"BLOCK_STALE_GENERATION")

    def test_unknown_wake_never_admits_and_release_requires_ack(self):
        s=next(s for s in FIXTURE["scenarios"] if s["id"]=="missed_notice_held")
        row=candidate.evaluate(s,FIXTURE["ttl_ns"])[2]
        self.assertEqual(row["outcome"],"UNKNOWN_WAKE_COVERAGE")
        self.assertEqual(row["first_action"],"SUPPRESS_UNKNOWN_WAKE")
        self.assertTrue(row["release_requested"])
        self.assertFalse(row["release_ack_observed"])

    def test_exact_current_lease_deadline_is_expired(self):
        s=next(s for s in FIXTURE["scenarios"] if s["id"]=="awake_expiry")
        self.assertEqual(candidate.evaluate(s,FIXTURE["ttl_ns"])[0]["outcome"],"EXPIRED")


if __name__=="__main__":
    unittest.main()
