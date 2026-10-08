import copy,unittest
try:
    from drift_audit import phase_errors
except ImportError:
    phase_errors=None

def row():
    binding=dict(token='new',pid=17,target_id=42,freeze_sha256='a'*64)
    ack=dict(binding,schema='issue5260-a09-focus-pipe-v1',sequence=1,kind='FocusIn',
             widget='target',focus_get='target',event_ns=80,written_ns=81)
    frames=[dict(binding,schema='issue5260-a09-focus-pipe-v1',sequence=2,
        kind='FocusOut',widget='target',focus_get='other',event_ns=120,written_ns=121),
        dict(binding,schema='issue5260-a09-focus-pipe-v1',sequence=3,
        kind='FocusIn',widget='decoy',focus_get='other',event_ns=130,written_ns=131)]
    return dict(mode='DRIFT_REFUSE',token='new',app_pid=17,
        ready={'geometry':{'target_id':42,'decoy_root_x':10,'decoy_root_y':20,
            'decoy_width':100,'decoy_height':20}},
        injection={'gate':{'status':'ADMITTED','ack':ack,'decided_ns':100},
            'key_requests':[],'save_requests':[],
            'post_admission':{'intervention':{'started_ns':110,'completed_ns':115,
                'widget':'decoy','x':60,'y':30},'dispatch_started_ns':150,
                'dispatch_completed_ns':160,'dispatch':{'status':'REFUSED','reason':'OBSERVED_DRIFT'},
                'drift':{'started_ns':116,'deadline_ns':500000116,'decided_ns':145,
                    'status':'OBSERVED_DRIFT','reason':'BOUND_TARGET_OUT_DECOY_IN',
                    'frames':copy.deepcopy(frames),'samples':[{'checked_ns':145,
                        'read_attempts':2,'frames':copy.deepcopy(frames),'errors':[]}]}},},
        pipe={'reads':[{'status':'DATA','started_ns':117,'completed_ns':140},
            {'status':'EAGAIN','started_ns':141,'completed_ns':142}],
            'frames':[{'value':f,'seen_ns':140} for f in frames]},
        app={'events':[{'kind':f['kind'],'widget':f['widget'],'sequence':f['sequence'],
                        'monotonic_ns':f['event_ns']} for f in frames]})

FIXTURE={'drift_timeout_ms':500,'ack_max_age_ms':50}
class AuditTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(phase_errors,'independent phase audit missing')
    def test_literal_bound_refusal_accepts(self):
        self.assertEqual(phase_errors(row(),FIXTURE,'a'*64),[])
    def test_candidate_label_cannot_hide_refused_key_or_save(self):
        for field in ('key_requests','save_requests'):
            r=row();r['injection'][field].append({})
            self.assertIn('refused_emission',phase_errors(r,FIXTURE,'a'*64))
    def test_wrong_focus_identity_and_pre_intervention_event_refused(self):
        for mutation in (lambda f:f.update(pid=18),lambda f:f.update(event_ns=109)):
            r=row();mutation(r['pipe']['frames'][0]['value'])
            self.assertTrue(phase_errors(r,FIXTURE,'a'*64))
    def test_deleted_or_boolean_poll_refused(self):
        r=row();r['injection']['post_admission']['drift']['samples']=[]
        self.assertIn('poll_custody',phase_errors(r,FIXTURE,'a'*64))
        r=row();r['injection']['post_admission']['drift']['samples'][0]['read_attempts']=True
        self.assertIn('poll_custody',phase_errors(r,FIXTURE,'a'*64))
    def test_app_focus_event_must_match_received_frame(self):
        r=row();r['app']['events'][0]['monotonic_ns']=119
        self.assertIn('app_drift_binding',phase_errors(r,FIXTURE,'a'*64))
    def test_dispatch_before_observation_refused(self):
        r=row();r['injection']['post_admission']['dispatch_started_ns']=144
        self.assertIn('phase_clock',phase_errors(r,FIXTURE,'a'*64))

if __name__=='__main__':unittest.main()
