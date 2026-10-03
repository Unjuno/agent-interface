import unittest
import audit
from test_initial_effect_a11 import complete,FIXTURE

class WiringTests(unittest.TestCase):
    def test_independent_expected_schedule_has_six_three_arm_idle_rows(self):
        rows=audit.expected_rows({'seed':52611026,'replicates_per_cell':2})
        self.assertEqual(len(rows),6)
        self.assertEqual({r['mode'] for r in rows},{'STABLE','DRIFT_STALE_CONTROL','DRIFT_REFUSE'})
        self.assertEqual({r['load'] for r in rows},{'idle'})
    def test_combined_initial_phase_effect_and_poll_checks_accept_literal(self):
        self.assertTrue(hasattr(audit,'input_checks'),'audit integration missing')
        fixture={**FIXTURE,'drift_timeout_ms':500}
        self.assertEqual(audit.input_checks(complete(),fixture,'a'*64),[])
    def test_combined_audit_cannot_skip_refused_effect_or_drift_clock(self):
        self.assertTrue(hasattr(audit,'input_checks'),'audit integration missing')
        fixture={**FIXTURE,'drift_timeout_ms':500}
        r=complete();r['app']['final_decoy']='h'
        self.assertIn('refusal_effect',audit.input_checks(r,fixture,'a'*64))
        r=complete();r['injection']['post_admission']['dispatch_started_ns']=144
        self.assertIn('phase_clock',audit.input_checks(r,fixture,'a'*64))

if __name__=='__main__':unittest.main()
