import copy
import json
import unittest
from pathlib import Path
from decision import evaluate

F=json.loads(Path(__file__).with_name('fixture.json').read_text())
def rows():
    data=[{**s,'stable_ids':([] if s['kind']=='dark' else [1]),'boundary_hits':0,'unknown_frames':0} for s in F['cases']]
    for r in data:
        if r['kind']=='pulse' and r['schedule']=='fixed' and r['phase']==0: r['stable_ids']=[]
    return data

class Decision(unittest.TestCase):
    def test_both_diversified_strictly_improve_every_width_fixed_blind(self):
        got=evaluate(F,rows(),'PASS_TRANSFER_SCOPED')
        self.assertEqual(got['status'],'PASS_NATIVE_PHASE_EFFECT_SCOPED')
        self.assertEqual(got['qualified_all_miss_episodes'],{'fixed':3,'irregular':0,'rotated':0})
    def test_boundary_and_unknown_never_promote(self):
        for key in ('boundary_hits','unknown_frames'):
            data=rows();data[3][key]=1
            with self.subTest(key=key): self.assertEqual(evaluate(F,data,'PASS_TRANSFER_SCOPED')['status'],'HOLD_SOURCE_BOUNDARY_AMBIGUITY')
    def test_one_diversified_tie_is_not_benefit(self):
        data=rows()
        for r in data:
            if r['kind']=='pulse' and r['schedule']=='rotated' and r['phase']==0:r['stable_ids']=[]
        self.assertEqual(evaluate(F,data,'PASS_TRANSFER_SCOPED')['status'],'HOLD_BENEFIT_NOT_ESTABLISHED')
    def test_fixed_blind_required_at_all_three_widths(self):
        data=rows()
        for r in data:
            if r['kind']=='pulse' and r['schedule']=='fixed' and r['width_ms']==30:r['stable_ids']=[1]
        self.assertEqual(evaluate(F,data,'PASS_TRANSFER_SCOPED')['status'],'HOLD_BENEFIT_NOT_ESTABLISHED')
    def test_historical_gate_is_not_discarded(self):
        self.assertEqual(evaluate(F,rows(),'HOLD_BENEFIT_NOT_ESTABLISHED')['status'],'HOLD_BENEFIT_NOT_ESTABLISHED')
    def test_missing_duplicate_reordered_or_false_count_rejected(self):
        data=rows();changed=copy.deepcopy(data);changed[3]['boundary_hits']=False
        for invalid in (data[:-1],data[:-1]+[data[0]],list(reversed(data)),changed):
            with self.assertRaises(ValueError):evaluate(F,invalid,'PASS_TRANSFER_SCOPED')
    def test_nested_offsets_and_impossible_frame_accounting_rejected(self):
        for offsets in ([False]*4,[0.0]*4):
            data=rows();data[0]['offsets']=offsets
            with self.assertRaises(ValueError):evaluate(F,data,'PASS_TRANSFER_SCOPED')
        data=rows();data[3]['stable_ids']=list(range(1,9));data[3]['boundary_hits']=1
        with self.assertRaises(ValueError):evaluate(F,data,'PASS_TRANSFER_SCOPED')

if __name__=='__main__':unittest.main()
