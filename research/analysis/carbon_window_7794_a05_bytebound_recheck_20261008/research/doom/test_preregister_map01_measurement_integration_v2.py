import hashlib,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
PLAN=HERE/'map01_measurement_integration_live_v2_prereg.json'
class Tests(unittest.TestCase):
 def test_frozen_plan_and_source_hashes(self):
  plan=json.loads(PLAN.read_text(encoding='utf-8'))
  self.assertEqual(plan['base_commit'],'7356970b15406c74bd2b404327f39c2e6b546022')
  self.assertEqual(plan['allocation_id'],'map01-measurement-integration-live-02')
  self.assertEqual(plan['model_calls'],0);self.assertIs(plan['retry'],False)
  self.assertEqual(plan['acceptance']['positive_useful_event_count_min'],0)
  self.assertEqual(plan['acceptance']['scorer_missed_sample_periods'],0)
  root=HERE.parents[1]
  for name,digest in plan['source_sha256'].items():
   path=root/name;self.assertTrue(path.is_file(),name);self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest,name)
 def test_latest_retained_dependency_hashes_are_frozen(self):
  plan=json.loads(PLAN.read_text(encoding='utf-8'))
  expected={
   'research/doom/session_map01_v12.py':'92658baccea4c412196ecfa613a5f8ef8e6d0fb674762bcde5968222c31aba7f',
   'research/doom/main_thread_scorer_polling_v1.py':'0a82819748603b77726d3d7053da7f6cba5cf0a0d5bcd9a79f4272554cf6af0a',
   'research/doom/independent_progress_clock_v2.py':'3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613',
   'research/live_control/input_transition_owner_v3.py':'5ffdbb3679451fefdc3836917d43d924f0f43c8082d21327207ecefbd87f5be6',
   'research/doom/doom_retained_input_backend_v3.py':'cad7de4769e574f78663e8351a8c2f8c714d51dfa7f9c41bcfb9716f06bef309',
   'research/doom/analyze_map01_direct_retained_input_v1.py':'163a32ce20516bdfc034eb4c6659141e53e3ef11b8526372042fb5e9d509e63a',
   'research/doom/map01_telemetry_session_v1.py':'0234712e1f2d4972b8cbcf4934b10b5b9581b2625e0a3bc4e2845f1e74897ef2'}
  self.assertEqual(plan['canonical_upstream_sha256'],expected)
if __name__=='__main__':unittest.main()
