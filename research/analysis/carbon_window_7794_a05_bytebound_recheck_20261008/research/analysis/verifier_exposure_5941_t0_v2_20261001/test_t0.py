import unittest
import runner, audit

class T0Tests(unittest.TestCase):
    def test_population_and_order(self):
        d=runner.generate(); self.assertEqual(len(d["cases"]),66)
        self.assertEqual(audit.audit(d),[])
        self.assertTrue(any(r["truth"]=="FAIL" and r["result"]["raw_quorum_pass"]
                            and not r["result"]["scoped_quorum_pass"] for r in d["cases"]))
    def test_shared_raw_is_not_peer_exposure(self):
        votes=[{"verdict":"PASS","exposure":"none","commit_valid":True},
               {"verdict":"PASS","exposure":"raw_observation","commit_valid":True},
               {"verdict":"PASS","exposure":"none","commit_valid":True}]
        self.assertEqual(audit.derive(votes)["disposition"],"PASS_SCOPED")
    def test_mutations_are_effective_and_rejected(self):
        outcomes=audit.corruption_controls(runner.generate())
        self.assertEqual(set(outcomes.values()),{True})
        self.assertEqual(len(outcomes),6)
    def test_unknown_or_invalid_never_counts(self):
        votes=[{"verdict":"PASS","exposure":"none","commit_valid":True},
               {"verdict":"PASS","exposure":"unknown","commit_valid":True},
               {"verdict":"PASS","exposure":"none","commit_valid":False}]
        self.assertEqual(audit.derive(votes)["disposition"],"UNKNOWN_INDEPENDENCE")

if __name__=="__main__": unittest.main()
