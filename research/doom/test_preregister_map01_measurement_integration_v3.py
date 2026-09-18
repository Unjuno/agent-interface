import hashlib, json, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
PLAN=HERE/'map01_measurement_integration_live_v3_prereg.json'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

class Tests(unittest.TestCase):
    def test_frozen_identity(self):
        p=json.loads(PLAN.read_text(encoding='utf-8'))
        self.assertEqual(p['allocation_id'],'map01-measurement-integration-live-03')
        self.assertEqual(p['base_commit'],'5486ea20b417a80903619a384744cf9ac38d5a52')
        self.assertFalse(p['retry'])
        self.assertEqual(p['model_calls'],0)
        self.assertEqual(p['fixed_probe']['seed'],990614)
    def test_protocol_repair_only(self):
        p=json.loads(PLAN.read_text(encoding='utf-8'))
        self.assertEqual(p['launch_protocol']['ownership_guard'],'formal-allocation-launch-owner-v1')
        self.assertEqual(p['launch_protocol']['run_attempt_required'],1)
        self.assertFalse(p['launch_protocol']['cancel_in_progress'])
        self.assertTrue(p['acceptance']['terminal_score_agreement_pass'])
        self.assertTrue(p['acceptance']['single_formal_probe_execution'])
    def test_unchanged_mechanism_hashes(self):
        p=json.loads(PLAN.read_text(encoding='utf-8'))
        for name, expected in p['unchanged_mechanism_sha256'].items():
            self.assertEqual(sha(REPO/name),expected,name)
        for name, expected in p['canonical_upstream_sha256'].items():
            self.assertEqual(sha(REPO/name),expected,name)
    def test_workflow_hash(self):
        p=json.loads(PLAN.read_text(encoding='utf-8'))
        self.assertEqual(sha(REPO/p['workflow_path']),p['workflow_sha256'])
    def test_consumed_allocation_not_reused(self):
        p=json.loads(PLAN.read_text(encoding='utf-8'))
        self.assertNotEqual(p['allocation_id'],'map01-measurement-integration-live-02')
        self.assertIn('reuse of consumed live-02 allocation',p['prohibited'])

if __name__=='__main__': unittest.main()
