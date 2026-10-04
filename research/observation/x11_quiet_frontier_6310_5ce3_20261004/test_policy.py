import unittest
from policy import classify
class PolicyTests(unittest.TestCase):
    def test_quiet_positive(self):
        self.assertEqual(classify(True,True,[]),{'historical':'QUIET_AS_OF_FRONTIER','authority':False})
    def test_observed_change(self):
        self.assertEqual(classify(True,True,[{'type':10}])['historical'],'CHANGE_OBSERVED')
    def test_missing_subscription(self):
        self.assertEqual(classify(False,True,[])['historical'],'UNKNOWN_NO_COVERAGE')
    def test_missing_barrier(self):
        self.assertEqual(classify(True,False,[])['historical'],'UNKNOWN_NO_COVERAGE')
    def test_non_boolean_coverage(self):
        self.assertEqual(classify(1,True,[])['historical'],'UNKNOWN_NO_COVERAGE')
    def test_no_authority_even_quiet(self):
        self.assertIs(classify(True,True,[])['authority'],False)
if __name__=='__main__':unittest.main()
