import unittest
try:
    from drift import drift_errors
except ImportError:
    drift_errors=None

class DriftTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(drift_errors,'drift validation not implemented')
        self.binding=dict(token='new',pid=17,target_id=42,freeze_sha256='a'*64)
        self.frames=[dict(self.binding,schema='issue5260-a09-focus-pipe-v1',
            sequence=2,kind='FocusOut',widget='target',focus_get='other',
            event_ns=120,written_ns=121),dict(self.binding,
            schema='issue5260-a09-focus-pipe-v1',sequence=3,kind='FocusIn',
            widget='decoy',focus_get='other',event_ns=130,written_ns=131)]
    def test_bound_post_admission_out_then_decoy_in_accepts(self):
        self.assertEqual(drift_errors(self.frames,self.binding,1,110,140),[])
    def test_pre_intervention_event_refused(self):
        self.frames[0]['event_ns']=109
        self.assertIn('drift_order',drift_errors(self.frames,self.binding,1,110,140))
    def test_wrong_pid_and_boolean_sequence_refused(self):
        self.frames[1]['pid']=18
        self.assertIn('binding',drift_errors(self.frames,self.binding,1,110,140))
        self.frames[1]['pid']=17
        self.frames[1]['sequence']=True
        self.assertIn('types',drift_errors(self.frames,self.binding,1,110,140))
    def test_missing_and_reversed_transition_refused(self):
        self.assertIn('transition_count',drift_errors(self.frames[:1],self.binding,1,110,140))
        self.assertIn('transition_kind',drift_errors(self.frames[::-1],self.binding,1,110,140))
    def test_future_clock_refused(self):
        self.frames[1]['written_ns']=141
        self.assertIn('drift_order',drift_errors(self.frames,self.binding,1,110,140))

    def test_non_array_transition_evidence_returns_rejection(self):
        # Removing collection validation must expose malformed evidence here.
        for frames in (None,17,{'out':self.frames[0],'in':self.frames[1]}):
            with self.subTest(frames=frames):
                self.assertIn('malformed',drift_errors(frames,self.binding,1,110,140))

    def test_boolean_binding_pid_cannot_authorize_integer_pid(self):
        self.binding['pid']=True
        for frame in self.frames:frame['pid']=1
        self.assertIn('binding_types',drift_errors(self.frames,self.binding,1,110,140))

if __name__=='__main__':unittest.main()
