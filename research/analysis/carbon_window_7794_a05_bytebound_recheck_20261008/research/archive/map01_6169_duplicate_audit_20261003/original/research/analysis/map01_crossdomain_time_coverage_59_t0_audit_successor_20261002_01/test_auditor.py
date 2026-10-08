import unittest
from auditor import counts_match_report, observer_report_matches, observer_summary

class SuccessorConstructionTests(unittest.TestCase):
    def test_v38_one_score_is_expected_raw_cardinality(self):
        candidate = {"domains": [{"domain":"doom_v38","event_counts":{"post_control_score":1}}]}
        self.assertTrue(counts_match_report(candidate, {"doom_v38":{"post_control_score":1}}))
        candidate["domains"][0]["event_counts"]["post_control_score"] = 0
        self.assertFalse(counts_match_report(candidate, {"doom_v38":{"post_control_score":1}}))

    def test_candidate_raw_count_drift_is_rejected(self):
        candidate = {"domains": [{"domain":"openttd","event_counts":{"terminal":2}}]}
        self.assertFalse(counts_match_report(candidate, {"openttd":{"terminal":1}}))

    def test_transition_witness_and_total_observer_count_are_separate(self):
        states = [{"tiles":[{"id":1,"road":False,"owner":-1}]},
                  {"tiles":[{"id":1,"road":True,"owner":0}]}]
        summary = observer_summary(states)
        self.assertEqual((summary["transition_witness_records"],summary["raw_total_records"],summary["transition_indices"]),(1,2,[1]))
        self.assertTrue(observer_report_matches({"observer_records":1,"observer_record_count":2,"observer_transition_indices":[1]},summary))
        self.assertFalse(observer_report_matches({"observer_records":1,"observer_record_count":1,"observer_transition_indices":[2]},summary))

if __name__ == "__main__":
    unittest.main()
