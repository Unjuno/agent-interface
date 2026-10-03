import unittest,threading
from types import SimpleNamespace
from runtime.backends.win32_v1.backend import Win32Backend
from runtime.guarded_win32_v1.bridge import MoveBridge

class Cases(unittest.TestCase):
 def fixture(self,release):
  b=object.__new__(Win32Backend);b.emissions=0;b.release_all=release
  o=SimpleNamespace(backend=b,target='fixture')
  return MoveBridge(o,lambda intent:None,lambda:False)
 def test_no_recovery_no_release(self):
  calls=[];s=self.fixture(lambda:calls.append('release'));r=s.recover_input();self.assertEqual(r['error'],'INPUT_RECOVERY_NOT_REQUIRED');self.assertEqual(calls,[])
 def test_verified_once_invalidates_pending(self):
  calls=[]
  def release():calls.append('release');return {'verified':True,'keys_down':[],'buttons_down':[]}
  s=self.fixture(release);s.session.recovery_required=True;s.permits['old']={'unused':True};r=s.recover_input()
  self.assertEqual(calls,['release']);self.assertEqual(r['status'],'input_recovered');self.assertIsNone(r['task_success']);self.assertFalse(r['replay_allowed']);self.assertFalse(s.session.recovery_required);self.assertEqual(s.execute('old')['error'],'AUTHORIZATION_CONSUMED_OR_UNKNOWN')
 def test_unverified_stays_quarantined(self):
  calls=[]
  def release():calls.append('release');return {'verified':False,'keys_down':['A'],'buttons_down':[]}
  s=self.fixture(release);s.session.recovery_required=True;r=s.recover_input();self.assertEqual(r['status'],'recovery_failed');self.assertTrue(s.session.recovery_required);self.assertEqual(calls,['release'])
 def test_cleanup_exception_stays_quarantined(self):
  calls=[]
  def release():calls.append('release');raise RuntimeError('inert release error')
  s=self.fixture(release);s.session.recovery_required=True;r=s.recover_input();self.assertEqual(r['status'],'recovery_failed');self.assertTrue(s.session.recovery_required);self.assertEqual(calls,['release']);self.assertFalse(s.lock.locked())
 def test_concurrent_execution_and_recovery_refused(self):
  entered=threading.Event();finish=threading.Event();results=[];calls=[]
  def release():
   calls.append('release');entered.set()
   if not finish.wait(5):raise RuntimeError('test release barrier expired')
   return {'verified':True,'keys_down':[],'buttons_down':[]}
  s=self.fixture(release);s.session.recovery_required=True
  worker=threading.Thread(target=lambda:results.append(s.recover_input()))
  worker.start()
  try:
   self.assertTrue(entered.wait(5));self.assertEqual(s.execute('unused')['error'],'OPERATION_ACTIVE');r=s.recover_input();self.assertEqual(r['error'],'OPERATION_ACTIVE');self.assertFalse(r['release_attempted']);self.assertEqual(calls,['release'])
  finally:finish.set();worker.join(5)
  self.assertFalse(worker.is_alive());self.assertEqual(results[0]['status'],'input_recovered');self.assertFalse(s.lock.locked())

if __name__=='__main__':unittest.main()
