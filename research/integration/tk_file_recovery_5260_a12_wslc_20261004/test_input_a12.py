import copy
import unittest
from phase_fixture import row,FIXTURE
try:
    from input_audit_a12 import prior_errors
except ImportError:
    prior_errors=None

def recovery_row():
    value=row();value['mode']='DRIFT_RECOVER'
    prior=copy.deepcopy(value['injection']['post_admission'])
    value['injection']['post_admission']={'prior':prior,'prior_emissions':{'keys':0,'saves':0},
        'total_emissions':{'keys':1,'saves':1},'recovery':{'started_ns':170}}
    value['injection']['key_requests']=[{'request_started_ns':180,'sync_returned_ns':181}]
    value['injection']['save_requests']=[{'request_started_ns':190,'sync_returned_ns':191}]
    value['app']['events'].extend([{'kind':'KeyPress','monotonic_ns':182},
        {'kind':'Save','monotonic_ns':192}])
    return value

class PriorTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(prior_errors,'prior phase projection missing')
    def test_later_effect_does_not_rewrite_prior_refusal(self):
        value=recovery_row();original=copy.deepcopy(value)
        self.assertEqual(prior_errors(value,FIXTURE,'a'*64),[])
        self.assertEqual(value,original)
    def test_early_key_request_or_application_effect_rejected(self):
        for mutate in [lambda r:r['injection']['key_requests'][0].update(request_started_ns=159),
                lambda r:r['app']['events'][-2].update(monotonic_ns=159),
                lambda r:r['injection']['post_admission'].update(prior_emissions={'keys':1,'saves':0}),
                lambda r:r['injection']['post_admission']['recovery'].update(started_ns=159)]:
            value=recovery_row();mutate(value)
            with self.subTest(value=value):self.assertTrue(prior_errors(value,FIXTURE,'a'*64))
    def test_missing_drift_poll_still_rejected_after_projection(self):
        value=recovery_row();value['injection']['post_admission']['prior']['drift']['samples']=[]
        self.assertIn('poll_custody',prior_errors(value,FIXTURE,'a'*64))

if __name__=='__main__':unittest.main()
