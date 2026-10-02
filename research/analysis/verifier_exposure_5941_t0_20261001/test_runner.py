import unittest
import runner

class Tests(unittest.TestCase):
    def test_exposed_vote_not_counted(self):
        row={"votes":[{"verdict":"PASS","exposure":"none","commit_valid":True},
                      {"verdict":"PASS","exposure":"peer_verdict","commit_valid":True},
                      {"verdict":"FAIL","exposure":"none","commit_valid":True}]}
        self.assertEqual(runner.evaluate(row)["disposition"],"UNKNOWN_INDEPENDENCE")
    def test_shared_raw_is_not_peer_exposure(self):
        row={"votes":[{"verdict":"PASS","exposure":"none","commit_valid":True},
                      {"verdict":"PASS","exposure":"raw_observation","commit_valid":True},
                      {"verdict":"PASS","exposure":"none","commit_valid":True}]}
        self.assertEqual(runner.evaluate(row)["disposition"],"PASS_SCOPED")
    def test_unknown_and_invalid_commit_excluded(self):
        row={"votes":[{"verdict":"PASS","exposure":"none","commit_valid":True},
                      {"verdict":"PASS","exposure":"unknown","commit_valid":True},
                      {"verdict":"PASS","exposure":"none","commit_valid":False}]}
        self.assertEqual(runner.evaluate(row)["disposition"],"UNKNOWN_INDEPENDENCE")
    def test_frozen_population(self): self.assertEqual(len(runner.cases()),66)

if __name__=="__main__": unittest.main()
