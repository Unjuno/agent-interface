"""Literal finite poll/input evidence; not a GUI result."""
import copy
import unittest
from test_input_a12 import recovery_row
try:
    from input_audit_a12 import recovery_input_errors
except ImportError:
    recovery_input_errors=None

FIXTURE={'ack_timeout_ms':500,'drift_timeout_ms':500,'ack_max_age_ms':50,'payload':'h'}
def complete_row():
    row=recovery_row();g=row['ready']['geometry']
    g.update(target_root_x=100,target_root_y=200,target_width=100,target_height=20)
    ack=dict(token='new',pid=17,target_id=42,freeze_sha256='a'*64,
        schema='issue5260-a09-focus-pipe-v1',sequence=5,kind='FocusIn',widget='target',
        focus_get='target',event_ns=175,written_ns=176)
    row['pipe']['reads'].extend([{'status':'DATA','started_ns':174,'completed_ns':177},
        {'status':'EAGAIN','started_ns':177,'completed_ns':178}])
    row['pipe']['frames'].append({'value':copy.deepcopy(ack),'seen_ns':177})
    row['injection']['key_requests'][0]['char']='h'
    row['injection']['post_admission']['recovery']=dict(status='EMITTED',
        reason='NEW_RECOVERY_ADMISSION',requested=True,prior_emissions={'keys':0,'saves':0},
        started_ns=170,click={'widget':'target','started_ns':171,'completed_ns':172,'x':150,'y':210},
        gate={'status':'ADMITTED','started_ns':173,'deadline_ns':500000173,'decided_ns':179,
            'reason':'CURRENT_TARGET_RECEIPT','ack':copy.deepcopy(ack),'state':copy.deepcopy(ack),
            'samples':[{'checked_ns':179,'state':copy.deepcopy(ack),'seen_ns':177,
                'errors':[],'read_attempts':4}]},dispatch_started_ns=179,dispatch_completed_ns=195)
    return row

class RecoveryInputTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(recovery_input_errors,'recovery input audit missing')
    def test_literal_new_gate_and_requests_accept_without_mutation(self):
        row=complete_row();original=copy.deepcopy(row)
        self.assertEqual(recovery_input_errors(row,FIXTURE,'a'*64),[])
        self.assertEqual(row,original)
    def test_missing_poll_and_wrong_click_rejected(self):
        for mutate in [lambda r:r['injection']['post_admission']['recovery']['gate']['samples'].clear(),
                lambda r:r['injection']['post_admission']['recovery']['click'].update(x=151),
                lambda r:r['injection']['post_admission'].update(total_emissions={'keys':2,'saves':1})]:
            row=complete_row();mutate(row)
            with self.subTest(row=row):self.assertTrue(recovery_input_errors(row,FIXTURE,'a'*64))
    def test_old_sequence_cannot_transfer_even_with_new_clock(self):
        row=complete_row();gate=row['injection']['post_admission']['recovery']['gate']
        for value in [gate['ack'],gate['state'],gate['samples'][0]['state'],row['pipe']['frames'][-1]['value']]:
            value['sequence']=3
        self.assertIn('new_sequence',recovery_input_errors(row,FIXTURE,'a'*64))

if __name__=='__main__':unittest.main()
