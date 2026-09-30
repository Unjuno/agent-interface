import unittest
import experiment as e

class ExperimentTests(unittest.TestCase):
    def test_seed_replay_is_deterministic(self):
        self.assertEqual(e.draw_episode("healthy_heavy_tail", 99), e.draw_episode("healthy_heavy_tail", 99))
    def test_invalid_and_stale_decoys_do_not_clear_suspicion(self):
        ep={"response_tick":None,"restart_tick":None,"host_a_witness":False,"host_b_witness":False,
            "decoys":[{"tick":3,"kind":"SEMANTICALLY_INVALID","generation":1},{"tick":5,"kind":"STALE_RESPONSE","generation":0}]}
        out=e.run_candidate(ep,2)
        self.assertEqual(out["final"],"SUSPECTED_UNAVAILABLE")
        self.assertEqual(out["decoys_ignored"],2)
        self.assertEqual(out["false_reactivation"],0)
    def test_distinct_domain_quorum_required(self):
        ep={"response_tick":None,"restart_tick":None,"host_a_witness":True,"host_b_witness":False,"decoys":[]}
        self.assertNotEqual(e.run_candidate(ep,2)["final"],"FAILED")
    def test_independent_witnesses_fail_at_bound(self):
        ep={"response_tick":None,"restart_tick":None,"host_a_witness":True,"host_b_witness":True,"decoys":[]}
        out=e.run_candidate(ep,2)
        self.assertEqual(out["final"],"FAILED")
        self.assertEqual(out["failed_tick"],6)
    def test_late_response_cannot_reactivate_terminal_failure(self):
        ep={"response_tick":7,"restart_tick":None,"host_a_witness":True,"host_b_witness":True,"decoys":[]}
        out=e.run_candidate(ep,2)
        self.assertEqual(out["final"],"FAILED")
        self.assertEqual(out["false_reactivation"],1)
    def test_current_valid_response_clears_suspicion(self):
        ep={"response_tick":8,"restart_tick":None,"host_a_witness":False,"host_b_witness":False,"decoys":[]}
        self.assertEqual(e.run_candidate(ep,4)["final"],"AUTHORIZED")
    def test_restart_and_new_generation_response_recover(self):
        ep={"response_tick":12,"restart_tick":10,"host_a_witness":False,"host_b_witness":False,"decoys":[]}
        self.assertEqual(e.run_candidate(ep,4)["final"],"AUTHORIZED")

if __name__ == "__main__":
    unittest.main()
