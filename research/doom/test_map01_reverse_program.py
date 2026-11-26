"""Finite reverse-door program validation, separate from private scoring."""
import unittest
from map01_reverse_program import reverse_stages

class ReverseProgramTests(unittest.TestCase):
    def test_matched_programs_differ_only_at_reopen_probe(self):
        control=reverse_stages('control');use=reverse_stages('use')
        self.assertEqual([x[0] for x in control],[x[0] for x in use])
        self.assertEqual([i for i,(a,b) in enumerate(zip(control,use)) if a!=b],[9])
        self.assertEqual(control[9][0],'reverse-probe')
        self.assertEqual(control[9][1],[{'op':'coast','duration_ms':120,'sample_ms':100}])
        self.assertEqual(use[9][1],[{'op':'hold','keys':['e'],'duration_ms':120}])
        self.assertEqual(control[-1][0],'reverse-cross')
        self.assertNotIn('reverse-approach',[x[0] for x in control])
        self.assertNotIn('reverse-align',[x[0] for x in control])
    def test_calibration_stops_after_turn_without_probe_or_cross(self):
        control=reverse_stages('control');calibration=reverse_stages('calibrate')
        self.assertEqual(calibration,control[:9])
        self.assertEqual(calibration[-1][0],'reverse-turn-3')
        self.assertTrue(all(not any(step.get('keys')==['e'] for step in steps) for _,steps in calibration))
    def test_east_return_extends_the_use_trial_with_bounded_stages(self):
        stages=reverse_stages('east-return')
        self.assertEqual(stages[:len(reverse_stages('use'))],reverse_stages('use'))
        self.assertEqual(stages[-5:], [
            ('east-turn-1',[{'op':'hold','keys':['Right'],'duration_ms':600}]),
            ('east-turn-2',[{'op':'hold','keys':['Right'],'duration_ms':600}]),
            ('east-turn-3',[{'op':'hold','keys':['Right'],'duration_ms':400}]),
            ('east-advance-1',[{'op':'hold','keys':['Up'],'duration_ms':600}]),
            ('east-advance-2',[{'op':'hold','keys':['Up'],'duration_ms':400}])])
    def test_invalid_arm_and_mutation_cannot_change_next_program(self):
        with self.assertRaises(ValueError):reverse_stages('invalid')
        stages=reverse_stages('use');stages[0][1][0]['duration_ms']=2
        self.assertEqual(reverse_stages('use')[0][1][0]['duration_ms'],1000)
if __name__=='__main__':unittest.main()
