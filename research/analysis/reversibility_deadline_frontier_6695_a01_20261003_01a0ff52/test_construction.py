import copy,unittest
import candidate,auditor
class Construction(unittest.TestCase):
    def case(self,**kw):
        c=dict(id='private-control',prep_ms=2,signal_ms=2,edit_ms=1,deadline_ms=4,signal='B',correction_route=True,proposal='A');c.update(kw);return c
    def test_exact_deadline_and_short(self):
        c=self.case(); self.assertTrue(candidate.simulate(c,'STAGE_THEN_CORRECT')['committed'])
        self.assertFalse(candidate.simulate(self.case(deadline_ms=3),'STAGE_THEN_CORRECT')['committed'])
    def test_stage_can_help_and_hurt(self):
        c=self.case();self.assertEqual(candidate.simulate(c,'STAGE_THEN_CORRECT')['ready_ms'],4);self.assertEqual(candidate.simulate(c,'WAIT_THEN_PREPARE')['ready_ms'],5)
        c=self.case(prep_ms=1,signal_ms=1,edit_ms=2);self.assertGreater(candidate.simulate(c,'STAGE_THEN_CORRECT')['ready_ms'],candidate.simulate(c,'WAIT_THEN_PREPARE')['ready_ms'])
    def test_no_correction_and_no_information(self):
        for c in (self.case(correction_route=False),self.case(signal='UNKNOWN')):
            self.assertEqual(candidate.simulate(c,'STAGE_THEN_CORRECT')['target'],'A')
    def test_oracle_matches_private_controls(self):
        for c in (self.case(),self.case(prep_ms=0,signal_ms=0,edit_ms=0),self.case(correction_route=False),self.case(signal='UNKNOWN')):
            for a in candidate.POLICIES:self.assertEqual(auditor.canonical(candidate.simulate(c,a)),auditor.canonical(auditor.derive(c,a)))
    def test_corruptions_rejected(self):
        c=self.case();base=[candidate.simulate(c,a) for a in candidate.POLICIES]
        mutations=[]
        for key,value in [('ready_ms',3),('target','A'),('committed',1)]:
            x=copy.deepcopy(base);x[2][key]=value;mutations.append(x)
        x=copy.deepcopy(base);x[2]['events'].pop(1);mutations.append(x)
        x=copy.deepcopy(base);x[2]['events'][-1]['at_ms']=5;mutations.append(x)
        mutations.extend([base[:-1],base+[copy.deepcopy(base[0])]])
        for rows in mutations:
            with self.subTest(rows=rows):self.assertTrue(auditor.audit([c],{c['id']:'B'},rows)['errors'])
    def test_uninformative_oracle_blindness(self):
        c=self.case(signal='UNKNOWN')
        # Distinct scorer truth is absent from the candidate interface.
        self.assertNotIn('truth',c)
        for a in candidate.POLICIES:self.assertEqual(candidate.simulate(c,a),candidate.simulate(copy.deepcopy(c),a))
if __name__=='__main__':unittest.main()
