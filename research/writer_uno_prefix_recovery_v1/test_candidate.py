import unittest,time
from candidate import *
class T(unittest.TestCase):
 def o(self,text='book',uid='u1',url='file:///a'):return Observation(url,uid,text,time.monotonic_ns())
 def test_fresh(self):self.assertTrue(precheck_bound(self.o(),desired='bookkeeperoffice',target_url='file:///a',current_row={'url':'file:///a','uid':'u1','text':'book'},now_ns=time.monotonic_ns(),max_age_ns=1_000_000_000).accepted)
 def test_uid(self):self.assertEqual(precheck_bound(self.o(),desired='bookkeeperoffice',target_url='file:///a',current_row={'url':'file:///a','uid':'u2','text':'book'},now_ns=time.monotonic_ns(),max_age_ns=1_000_000_000).error,'STALE_DOCUMENT_ID')
 def test_wrong_doc(self):self.assertEqual(precheck_bound(self.o(url='file:///b'),desired='bookkeeperoffice',target_url='file:///a',current_row={'url':'file:///a','uid':'u1','text':'book'},now_ns=time.monotonic_ns(),max_age_ns=1_000_000_000).error,'WRONG_DOCUMENT')
 def test_stale_text(self):self.assertEqual(precheck_bound(self.o(),desired='bookkeeperoffice',target_url='file:///a',current_row={'url':'file:///a','uid':'u1','text':'boox'},now_ns=time.monotonic_ns(),max_age_ns=1_000_000_000).error,'STALE_TEXT')
 def test_focus(self):self.assertEqual(final_focus_guard(10,11,11),'FOCUS_MISMATCH')
if __name__=='__main__':unittest.main()
