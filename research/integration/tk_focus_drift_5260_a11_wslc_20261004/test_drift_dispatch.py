import os,unittest
import drift

class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(drift,'dispatch'),'dispatch not implemented')
    def result(self,arm,initial='ADMITTED',observed='OBSERVED_DRIFT'):
        read,write=os.pipe()
        os.set_blocking(read,False)
        try:
            r=drift.dispatch({'status':initial},arm,{'status':observed},'hxy',
                lambda ch:os.write(write,ch.encode()),lambda:os.write(write,b'S'))
            os.close(write);write=None
            return r,os.read(read,100)
        finally:
            os.close(read)
            if write is not None:os.close(write)
    def test_observed_drift_refusal_emits_no_key_or_save(self):
        r,data=self.result('DRIFT_REFUSE')
        self.assertEqual(r['status'],'REFUSED')
        self.assertEqual(data,b'')
    def test_failed_observation_stops_without_any_emission(self):
        r,data=self.result('DRIFT_STALE_CONTROL',observed='STOP')
        self.assertEqual(r['status'],'STOP')
        self.assertEqual(data,b'')
    def test_initial_refusal_never_enters_stale_control(self):
        r,data=self.result('DRIFT_STALE_CONTROL',initial='REFUSED')
        self.assertEqual(r['status'],'STOP')
        self.assertEqual(data,b'')
    def test_stable_and_explicit_stale_control_emit_exactly_once(self):
        for arm in ('STABLE','DRIFT_STALE_CONTROL'):
            r,data=self.result(arm)
            self.assertEqual(r['status'],'EMITTED')
            self.assertEqual(data,b'hxyS')
    def test_unknown_arm_stops_without_emission(self):
        r,data=self.result('wrong')
        self.assertEqual(r['status'],'STOP')
        self.assertEqual(data,b'')

if __name__=='__main__':unittest.main()
