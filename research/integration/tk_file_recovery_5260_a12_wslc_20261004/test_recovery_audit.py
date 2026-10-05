import copy
import unittest
import os
import time
from pipe_transport import PipeSession
from pipe_receipt import encode_frame
from recovery import RecoveryAttempt
from recovery_audit import recovery_errors

def fixture():
    return dict(requested=True,prior={'dispatch':{'status':'REFUSED','reason':'OBSERVED_DRIFT'},
        'drift':{'status':'OBSERVED_DRIFT','frames':[{'sequence':4}]}},
        prior_keys=[],prior_saves=[],recovery=dict(status='EMITTED',reason='NEW_RECOVERY_ADMISSION',
        requested=True,started_ns=100,prior_emissions={'keys':0,'saves':0},
        click={'widget':'target','started_ns':110,'completed_ns':120},
        gate={'status':'ADMITTED','decided_ns':140,'ack':{'sequence':6,'event_ns':130}},
        dispatch_started_ns=150,dispatch_completed_ns=190),
        keys=[{'char':'h','started_ns':160,'completed_ns':170}],
        saves=[{'started_ns':180,'completed_ns':185}])

class RecoveryAuditTests(unittest.TestCase):
    def test_real_pipe_gate_output_is_auditable(self):
        binding=dict(token='construction',pid=17,target_id=42,freeze_sha256='a'*64)
        row=fixture();row['keys']=[];row['saves']=[]
        def key(char):
            started=time.monotonic_ns()
            row['keys'].append(dict(char=char,started_ns=started,completed_ns=time.monotonic_ns()))
        def save():
            started=time.monotonic_ns()
            row['saves'].append(dict(started_ns=started,completed_ns=time.monotonic_ns()))
        with PipeSession() as session:
            def click():
                started=time.monotonic_ns();now=time.monotonic_ns()
                os.write(session.write_fd,encode_frame(dict(binding,schema='issue5260-a09-focus-pipe-v1',
                    kind='FocusIn',widget='target',focus_get='target',sequence=6,event_ns=now,written_ns=now)))
                return dict(widget='target',started_ns=started,completed_ns=time.monotonic_ns())
            row['recovery']=RecoveryAttempt().run(True,row['prior'],0,0,session,binding,
                click,'h',key,save)
        self.assertEqual(row['recovery']['status'],'EMITTED')
        self.assertEqual(recovery_errors(row,'h'),[])

    def test_finite_stage_contract(self):
        self.assertEqual(recovery_errors(fixture(),'h'),[])

    def test_mutations_rejected(self):
        changes=[lambda r:r.update(requested=False),
            lambda r:r['prior_keys'].append({}),
            lambda r:r['recovery']['gate']['ack'].update(sequence=4),
            lambda r:r['recovery']['gate']['ack'].update(event_ns=109),
            lambda r:r['recovery']['click'].update(widget='decoy'),
            lambda r:r['keys'][0].update(started_ns=139),
            lambda r:r['keys'][0].update(char='x'),
            lambda r:r['saves'].append(dict(started_ns=186,completed_ns=187)),
            lambda r:r['recovery'].update(dispatch_completed_ns=True)]
        for change in changes:
            row=copy.deepcopy(fixture());change(row)
            with self.subTest(row=row):self.assertTrue(recovery_errors(row,'h'))

    def test_stopped_recovery_must_have_no_effects(self):
        row=fixture();row['recovery'].update(status='STOP',reason='RECOVERY_NOT_ADMITTED')
        row['keys']=[];row['saves']=[]
        self.assertEqual(recovery_errors(row,'h'),[])
        row['keys']=[{'char':'h'}]
        self.assertIn('stopped_recovery_effect',recovery_errors(row,'h'))

    def test_malformed_is_not_acceptance(self):
        self.assertTrue(recovery_errors({},'h'))

if __name__=='__main__':unittest.main()
