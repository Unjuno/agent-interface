"""Real OS pipe phase wiring; not GUI hypothesis evidence."""
import os
import time
import unittest
from pipe_transport import PipeSession
from pipe_receipt import encode_frame
try:
    from recovery_phase import run_phase
except ImportError:
    run_phase=None

class PhaseTests(unittest.TestCase):
    def exercise(self,mode):
        self.assertIsNotNone(run_phase,'phase wiring missing')
        binding=dict(token='construction',pid=17,target_id=42,freeze_sha256='a'*64)
        keys=[];saves=[];clicks=[]
        with PipeSession() as session:
            def publish(sequence,kind,widget,focus):
                now=time.monotonic_ns()
                os.write(session.write_fd,encode_frame(dict(binding,schema='issue5260-a09-focus-pipe-v1',
                    sequence=sequence,event_ns=now,written_ns=now,kind=kind,widget=widget,focus_get=focus)))
            def intervene():
                started=time.monotonic_ns()
                publish(3,'FocusOut','target','other');publish(4,'FocusIn','decoy','other')
                return dict(widget='decoy',started_ns=started,completed_ns=time.monotonic_ns())
            def recover_click():
                started=time.monotonic_ns();clicks.append(started)
                publish(5,'FocusOut','decoy','other');publish(6,'FocusIn','target','target')
                return dict(widget='target',started_ns=started,completed_ns=time.monotonic_ns())
            result=run_phase({'status':'ADMITTED','ack':{'sequence':2}},mode,
                session,binding,intervene,recover_click,'hxy',keys.append,lambda:saves.append('Save'),
                timeout_ns=5_000_000,poll_ns=100_000,max_age_ns=50_000_000)
        return result,keys,saves,clicks

    def test_recovery_preserves_refusal_then_new_admission(self):
        result,keys,saves,clicks=self.exercise('DRIFT_RECOVER')
        self.assertEqual(result['prior']['dispatch'],{'status':'REFUSED','reason':'OBSERVED_DRIFT'})
        self.assertEqual(result['recovery']['gate']['ack']['sequence'],6)
        self.assertEqual(result['recovery']['status'],'EMITTED')
        self.assertEqual(keys,['h','x','y']);self.assertEqual(saves,['Save']);self.assertEqual(len(clicks),1)

    def test_refuse_arm_never_recovers_or_emits(self):
        result,keys,saves,clicks=self.exercise('DRIFT_REFUSE')
        self.assertIsNone(result['recovery'])
        self.assertEqual(keys,[]);self.assertEqual(saves,[]);self.assertEqual(clicks,[])

    def test_stable_arm_does_not_intervene_or_recover(self):
        result,keys,saves,clicks=self.exercise('STABLE')
        self.assertIsNone(result['prior']['intervention']);self.assertIsNone(result['recovery'])
        self.assertEqual(keys,['h','x','y']);self.assertEqual(saves,['Save']);self.assertEqual(clicks,[])

if __name__=='__main__':unittest.main()
