import copy
import unittest
import core

class DecisionTests(unittest.TestCase):
    def rows(self, n=5, pooled=True, pressure=True):
        cells=[]
        for pair in range(6):
            for arm in ('quiet','loaded'):
                delay=2_000_000 if arm=='loaded' and pair<n else 0
                if not pooled and pair==5 and arm=='quiet': delay=30_000_000
                cells.append({'pair':pair,'arm':arm,'delays':[delay]*16,'throttle_count':int(arm=='loaded' and pressure),'throttle_usec':int(arm=='loaded' and pressure)})
        return cells
    def test_requires_five_pairs(self):
        self.assertEqual(core.decision(self.rows(4))['status'],'HOLD_NOT_SUPPORTED')
    def test_five_exact_boundary_support(self):
        cells=self.rows(5)
        for c in cells:
            if c['arm']=='loaded' and c['pair']<5: c['delays']=[1_000_000]*16
        self.assertEqual(core.decision(cells)['status'],'SUPPORT_IMPOSED_LOAD_ONLY')
    def test_pooled_required(self):
        cells=self.rows(5)
        for c in cells:
            if c['arm']=='quiet': c['delays']=[0]*8+[10_000_000]*8
            elif c['pair']<5: c['delays']=[0]*8+[14_000_000]*8
        self.assertEqual(core.decision(cells)['status'],'HOLD_NOT_SUPPORTED')
    def test_pressure_required(self):
        self.assertEqual(core.decision(self.rows(6,True,False))['status'],'HOLD_NOT_SUPPORTED')
    def test_duplicate_pair_arm_rejected(self):
        with self.assertRaises(ValueError): core.decision(self.rows()+[self.rows()[0]])
    def test_bool_clock_rejected(self):
        with self.assertRaises(ValueError): core.integer(True)
    def test_counter_raw_negative_rejected(self):
        with self.assertRaises(ValueError): core.parse_cpu('usage_usec -1\n')
    def test_duplicate_counter_rejected(self):
        with self.assertRaises(ValueError): core.parse_cpu('usage_usec 1\nusage_usec 2\n')
    def test_incomplete_budget_rejected(self):
        cells=self.rows(); cells[0]['delays']=cells[0]['delays'][:-1]
        with self.assertRaises(ValueError): core.decision(cells)

if __name__=='__main__': unittest.main()
