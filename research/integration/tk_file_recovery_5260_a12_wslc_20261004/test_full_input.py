import copy
import unittest
from test_recovery_input import complete_row
try:
    from input_audit_a12 import input_errors
except ImportError:
    input_errors=None

FIXTURE={'ack_timeout_ms':500,'drift_timeout_ms':500,'ack_max_age_ms':50,
    'payload':'hxy','inter_key_gap_ms':0,'save_delay_after_last_key_ms':0}
def full_row():
    row=complete_row();inj=row['injection'];phase=inj['post_admission']
    g=row['ready']['geometry'];g.update(save_root_x=200,save_root_y=300,save_width=50,save_height=20)
    ack=copy.deepcopy(inj['gate']['ack'])
    row['pipe']['reads'][:0]=[{'status':'DATA','started_ns':82,'completed_ns':85},
        {'status':'EAGAIN','started_ns':94,'completed_ns':95}]
    row['pipe']['frames'].insert(0,{'value':copy.deepcopy(ack),'seen_ns':85})
    inj.update(click_widget='target',click_started_ns=60,click_sync_returned_ns=65,x=150,y=210,
        gate={'status':'ADMITTED','ack':copy.deepcopy(ack),'state':copy.deepcopy(ack),
            'started_ns':70,'decided_ns':100,'deadline_ns':500000070,'reason':'CURRENT_TARGET_RECEIPT',
            'samples':[{'checked_ns':100,'read_attempts':2,'state':copy.deepcopy(ack),'seen_ns':85,'errors':[]}]})
    phase['prior']['drift']['samples'][0]['read_attempts']=4
    phase['recovery']['gate']['samples'][0]['read_attempts']=6
    inj['key_requests']=[dict(index=i,char=char,keycode=i+1,request_started_ns=180+2*i,
        sync_returned_ns=181+2*i) for i,char in enumerate('hxy')]
    inj['save_requests'][0].update(x=225,y=310)
    phase['total_emissions']={'keys':3,'saves':1}
    row['app']['events']=[e for e in row['app']['events'] if e['kind'] not in ('KeyPress','Save')]
    row['app']['events'].extend([dict(kind='KeyPress',widget='target',char=char,monotonic_ns=181+2*i)
        for i,char in enumerate('hxy')]+[dict(kind='Save',widget='target',monotonic_ns=192)])
    row['app'].update(ended_ns=300,first_key_widget='target',first_key_ns=182,
        final_target='hxy',final_decoy='',saved_text='hxy',save_count=1)
    return row

class FullInputTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(input_errors,'full input join missing')
    def test_prior_initial_recovery_and_effects_join(self):
        row=full_row();original=copy.deepcopy(row)
        self.assertEqual(input_errors(row,FIXTURE,'a'*64),[])
        self.assertEqual(row,original)
    def test_each_join_is_required(self):
        mutations=[lambda r:r['injection']['gate']['samples'].clear(),
            lambda r:r['injection']['post_admission']['prior']['drift']['samples'].clear(),
            lambda r:r['injection']['post_admission']['recovery']['gate']['samples'].clear(),
            lambda r:r['app'].update(final_target='wrong'),
            lambda r:r['injection']['post_admission'].update(prior_emissions={'keys':True,'saves':0})]
        for mutate in mutations:
            row=full_row();mutate(row)
            with self.subTest(row=row):self.assertTrue(input_errors(row,FIXTURE,'a'*64))

    def test_stable_arm_requires_no_recovery_and_explained_counts(self):
        row=full_row();row['mode']='STABLE';phase=row['injection']['post_admission']
        phase.update(recovery=None,prior_emissions={'keys':3,'saves':1},
            prior={'intervention':None,'drift':None,'dispatch_started_ns':101,
                'dispatch_completed_ns':195,'dispatch':{'status':'EMITTED','reason':'STABLE'}})
        self.assertEqual(input_errors(row,FIXTURE,'a'*64),[])
        phase['recovery']={'status':'EMITTED'}
        self.assertIn('unexpected_recovery',input_errors(row,FIXTURE,'a'*64))

    def test_refusal_arm_has_no_effects_despite_initial_admission(self):
        row=full_row();row['mode']='DRIFT_REFUSE';inj=row['injection'];phase=inj['post_admission']
        inj.update(key_requests=[],save_requests=[])
        phase.update(recovery=None,prior_emissions={'keys':0,'saves':0},total_emissions={'keys':0,'saves':0})
        row['app']['events']=[e for e in row['app']['events'] if e['kind'] not in ('KeyPress','Save')]
        row['app'].update(saved_text=None,save_count=0,final_target='',final_decoy='')
        for key in ('first_key_widget','first_key_ns'):row['app'].pop(key)
        self.assertEqual(input_errors(row,FIXTURE,'a'*64),[])
        row['app']['events'].append({'kind':'Save','monotonic_ns':250})
        self.assertTrue(input_errors(row,FIXTURE,'a'*64))

if __name__=='__main__':unittest.main()
