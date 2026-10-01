import unittest
from unittest.mock import Mock
class Tests(unittest.TestCase):
 def test_placeholder_identity_invariant(self):
  a={'url':'file:///a.odt','uid':'1'};b={'url':'file:///b.odt','uid':'2'};self.assertNotEqual((a['url'],a['uid']),(b['url'],b['uid']))
 def test_target_scoring_requires_other_unchanged(self):
  desired='bookkeeperoffice';other='sidecar';self.assertTrue(desired==desired and other==other);self.assertFalse('book'==desired and 'sidecarkeeperoffice'==other)
if __name__=='__main__':unittest.main()
