import unittest,subprocess,sys
from policy import classify,classify_complete

def event(seq, kind, value=0, source='object-A'):
    return {'seq': seq, 'kind': kind, 'value': value, 'source': source}

class Events(unittest.TestCase):
    def test_missing_tail_with_declared_count_is_unknown(self):
        self.assertEqual(classify_complete([event(0,'ACTION'),event(1,'EFFECT')],3),'UNKNOWN')
    def test_known_complete_prefix_can_be_pending(self):
        self.assertEqual(classify_complete([event(0,'ACTION')],1),'PENDING')
    def test_boolean_expected_count_is_unknown(self):
        self.assertEqual(classify_complete([event(0,'ACTION')],True),'UNKNOWN')
    def test_optimized_auditor_stops_before_any_pass(self):
        from pathlib import Path
        p=subprocess.run([sys.executable,'-B','-O','-c','import auditor'],cwd=Path(__file__).parent,capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('STOP_OPTIMIZED_AUDITOR_UNSUPPORTED',p.stderr)
    def test_empty_is_not_run(self): self.assertEqual(classify([]), 'NOT_RUN')
    def test_prediction_is_not_observed_success(self):
        self.assertEqual(classify([event(0,'PREDICT')]), 'NOT_RUN')
    def test_accepted_action_without_effect_is_pending(self):
        self.assertEqual(classify([event(0,'ACTION')]), 'PENDING')
    def test_verified_effect_is_success(self):
        self.assertEqual(classify([event(0,'ACTION'),event(1,'EFFECT')]), 'SUCCESS')
    def test_late_delivery_restores_source_order(self):
        self.assertEqual(classify([event(2,'REVERT'),event(1,'EFFECT'),event(0,'ACTION')]), 'SUCCESS_THEN_REVERT')
    def test_failed_action_is_not_completion(self):
        self.assertEqual(classify([event(0,'ACTION'),event(1,'FAIL')]), 'FAILED')
    def test_gap_does_not_reconstruct_success(self):
        self.assertEqual(classify([event(0,'ACTION'),event(2,'EFFECT')]), 'UNKNOWN')
    def test_other_source_does_not_verify_effect(self):
        self.assertEqual(classify([event(0,'ACTION'),event(1,'EFFECT',source='object-B')]), 'UNKNOWN')
    def test_duplicate_sequence_is_unknown(self):
        self.assertEqual(classify([event(0,'ACTION'),event(0,'EFFECT')]), 'UNKNOWN')
    def test_boolean_sequence_is_not_integer_identity(self):
        self.assertEqual(classify([event(False,'ACTION')]), 'UNKNOWN')
    def test_effect_without_action_is_unknown(self):
        self.assertEqual(classify([event(0,'EFFECT')]), 'UNKNOWN')

if __name__ == '__main__': unittest.main()
