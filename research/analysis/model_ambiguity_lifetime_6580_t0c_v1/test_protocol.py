import json
import tempfile
import unittest
from pathlib import Path
import auditor
import candidate


class ExhaustiveBranchTests(unittest.TestCase):
    def fixture(self,d):
        p=Path(d)/"raw.json"; candidate.main(p); return p,json.loads(p.read_text())

    def test_exhaustive_candidate_and_independent_audit(self):
        with tempfile.TemporaryDirectory() as d:
            p,obj=self.fixture(d); result=auditor.audit(p)
            self.assertEqual(result["status"],"PASS_METHOD_SCOPED")
            self.assertEqual(result["scenario_rows_seen"],48)
            self.assertEqual(result["branch_rows_seen"],66)

    def test_both_values_of_ambiguous_public_signal(self):
        with tempfile.TemporaryDirectory() as d:
            _,obj=self.fixture(d)
            rows=[r for r in obj["rows"] if r["lifetime"]=="ZERO" and r["phase"]=="PRE_EVENT" and r["evidence"]=="STALE" and r["order"]=="NATURE_FIRST_PUBLIC"]
            self.assertEqual({r["observed_theta"] for r in rows},{0,1})
            self.assertEqual({r["action"] for r in rows},{"A","B"})

    def test_agent_first_ambiguous_support_yields_without_effect(self):
        with tempfile.TemporaryDirectory() as d:
            _,obj=self.fixture(d)
            rows=[r for r in obj["rows"] if r["lifetime"]=="ZERO" and r["evidence"]=="MISSING" and r["order"]=="AGENT_FIRST_REACTIVE"]
            self.assertTrue(all(r["decision"]=="YIELD" and r["action"] is None and not r["reachable_theta"] for r in rows))

    def test_mutations_dropping_or_inverting_theta_one_branch_fail(self):
        with tempfile.TemporaryDirectory() as d:
            p,obj=self.fixture(d)
            drop=json.loads(json.dumps(obj)); drop["rows"].remove(next(r for r in drop["rows"] if r["lifetime"]=="ZERO" and r["evidence"]=="STALE" and r["order"]=="NATURE_FIRST_PUBLIC" and r["observed_theta"]==1))
            invert=json.loads(json.dumps(obj)); next(r for r in invert["rows"] if r["lifetime"]=="ZERO" and r["evidence"]=="STALE" and r["order"]=="NATURE_FIRST_PUBLIC" and r["observed_theta"]==1)["action"]="A"
            for i,bad in enumerate((drop,invert)):
                p.write_text(json.dumps(bad))
                with self.subTest(mutation=i): self.assertEqual(auditor.audit(p)["status"],"FAIL_METHOD")

    def test_negative_control_coverage_and_action_are_audited(self):
        with tempfile.TemporaryDirectory() as d:
            p,obj=self.fixture(d)
            obj["negative_controls"][0]["action"]="A"
            p.write_text(json.dumps(obj))
            self.assertEqual(auditor.audit(p)["status"],"FAIL_METHOD")


if __name__=="__main__": unittest.main()
