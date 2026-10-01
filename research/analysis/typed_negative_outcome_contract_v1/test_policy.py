import unittest
from policy import classify
class T(unittest.TestCase):
 def test_current_success(self):
  e={'freshness':'CURRENT','completeness':'COMPLETE','contradictory':False,'family':'SUCCEEDED','retry_context':'REQUIRES_CHANGE'}
  self.assertEqual(classify(e)['label'],'SUCCEEDED')
 def test_stale_unknown(self):
  e={'freshness':'STALE','completeness':'COMPLETE','contradictory':False,'family':'IMPOSSIBLE_UNDER_CONSTRAINTS','retry_context':'REQUIRES_CHANGE'}
  self.assertEqual(classify(e)['label'],'FAILED_UNKNOWN')
 def test_incomplete_unknown(self):
  e={'freshness':'CURRENT','completeness':'INCOMPLETE','contradictory':False,'family':'TARGET_NOT_FOUND','retry_context':'REQUIRES_CHANGE'}
  self.assertEqual(classify(e)['label'],'FAILED_UNKNOWN')
 def test_contradictory_unknown(self):
  e={'freshness':'CURRENT','completeness':'COMPLETE','contradictory':True,'family':'SUCCEEDED','retry_context':'REQUIRES_CHANGE'}
  self.assertEqual(classify(e)['label'],'FAILED_UNKNOWN')
 def test_blocked_retry_context(self):
  e={'freshness':'CURRENT','completeness':'COMPLETE','contradictory':False,'family':'BLOCKED','retry_context':'IDENTICAL_RETRY_VALID'}
  self.assertTrue(classify(e)['retryable'])
if __name__=='__main__': unittest.main(verbosity=2)
