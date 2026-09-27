from __future__ import annotations
import unittest
from fractions import Fraction as F
from clock_bounds import outcome,rat,Invalid

def example():
    scope={'from':'a','to':'b','epoch':'test'}
    return {'scope':scope,'expected_scope':dict(scope),'rate':['1','2'],'offset':['-10','0'],
            'valid_s':['-20','20'],'samples':[{'s':'10','lo':'10','hi':'10'}],
            'release':['11','12'],'deadline':'14'}

class ContractTests(unittest.TestCase):
    def test_exact_projection(self):self.assertEqual(outcome(example())['interval'],['11','14'])
    def test_box_dependency_loss(self):
        r=outcome(example());self.assertEqual(r['status'],'ON_TIME');self.assertEqual(r['marginal']['status'],'UNRESOLVED')
    def test_nominal_false_certainty(self):
        d=example();d['deadline']='13';r=outcome(d)
        self.assertEqual(r['status'],'UNRESOLVED');self.assertEqual(r['nominal']['status'],'ON_TIME')
    def test_open_lower(self):
        d=example();d['deadline']='11';self.assertEqual(outcome(d)['status'],'LATE')
    def test_closed_upper(self):self.assertEqual(outcome(example())['status'],'ON_TIME')
    def test_empty(self):
        d=example();d['release']=['1','1'];self.assertEqual(outcome(d)['status'],'UNKNOWN_INVALID')
    def test_inconsistent(self):
        d=example();d['samples']=[{'s':'0','lo':'0','hi':'0'},{'s':'0','lo':'1','hi':'1'}]
        self.assertEqual(outcome(d)['status'],'UNKNOWN_INCONSISTENT')
    def test_missing(self):
        d=example();d['samples']=[];self.assertEqual(outcome(d)['status'],'UNKNOWN_INVALID')
    def test_nonpositive(self):
        d=example();d['rate']=['0','1'];self.assertEqual(outcome(d)['status'],'UNKNOWN_INVALID')
    def test_horizon(self):
        d=example();d['release']=['19','21'];self.assertEqual(outcome(d)['status'],'UNKNOWN_INVALID')
    def test_scope(self):
        d=example();d['scope']=dict(d['scope'],epoch='new');self.assertEqual(outcome(d)['status'],'UNKNOWN_INVALID')
    def test_bad_numeric(self):
        for x in (True,1,1.0,'1.0','1/0','01','2/2','nan','1e9'):
            with self.subTest(x=x),self.assertRaises(Invalid):rat(x)
    def test_negative_reference_times(self):
        d=example();d.update(rate=['1','1'],offset=['0','0'],samples=[{'s':'0','lo':'0','hi':'0'}],release=['-2','-1'],deadline='-1')
        self.assertEqual(outcome(d)['interval'],['-2','-1'])
    def test_no_authority(self):
        r=outcome(example());self.assertIs(r['grants_input_authority'],False);self.assertIsNone(r['task_success'])
    def test_singleton_clock(self):
        d=example();d.update(rate=['1','1'],offset=['0','0']);self.assertEqual(outcome(d)['interval'],['11','12'])
    def test_rational_clock(self):
        d=example();d.update(rate=['3/2','3/2'],offset=['-5','-5']);self.assertEqual(outcome(d)['interval'],['23/2','13'])
if __name__=='__main__':unittest.main(verbosity=2)
