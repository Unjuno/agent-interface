import copy,unittest
from gate_audit import gate_errors
from effect_audit import effect_errors
from test_drift_audit import row

FIXTURE={'payload':'hxy','ack_timeout_ms':500,'ack_max_age_ms':50,
         'inter_key_gap_ms':20,'save_delay_after_last_key_ms':250}

def complete():
    r=row();inj=r['injection'];gate=inj['gate'];ack=gate['ack']
    inj.update(click_widget='target',x=60,y=30,click_started_ns=50,click_sync_returned_ns=60)
    gate.update(started_ns=70,deadline_ns=500000070,state=copy.deepcopy(ack),
        reason='CURRENT_TARGET_RECEIPT',samples=[dict(checked_ns=100,
            read_attempts=2,state=copy.deepcopy(ack),seen_ns=90,errors=[])])
    r['pipe']['reads'][:0]=[dict(status='DATA',started_ns=75,completed_ns=90),
        dict(status='EAGAIN',started_ns=91,completed_ns=92)]
    r['pipe']['frames'].insert(0,dict(value=copy.deepcopy(ack),seen_ns=90))
    r['injection']['post_admission']['drift']['samples'][0]['read_attempts']=4
    r['ready']['geometry'].update(target_root_x=10,target_root_y=20,
        target_width=100,target_height=20,save_root_x=10,save_root_y=50,
        save_width=40,save_height=20)
    r['app'].update(save_count=0,saved_text=None,final_target='',final_decoy='',ended_ns=1000000000)
    return r

class InitialEffectTests(unittest.TestCase):
    def test_initial_admission_valid_even_when_later_drift_refuses_keys(self):
        self.assertEqual(gate_errors(complete(),FIXTURE,'a'*64),[])
    def test_zero_effect_refusal_is_derived_from_arm_not_initial_admission(self):
        self.assertEqual(effect_errors(complete(),FIXTURE),[])
    def test_receipt_pid_boolean_and_early_admission_refused(self):
        for mutate in (lambda g:g['ack'].update(pid=True),
                       lambda g:g.update(decided_ns=59)):
            r=complete();mutate(r['injection']['gate'])
            self.assertTrue(gate_errors(r,FIXTURE,'a'*64))
    def test_refusal_cannot_hide_field_save_or_received_key(self):
        mutations=[lambda a:a.update(final_decoy='h'),lambda a:a.update(save_count=1),
                   lambda a:a['events'].append({'kind':'KeyPress','char':'h'})]
        for mutate in mutations:
            r=complete();mutate(r['app'])
            self.assertTrue(effect_errors(r,FIXTURE))

if __name__=='__main__':unittest.main()
