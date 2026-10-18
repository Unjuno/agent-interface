import unittest,subprocess,sys,time,json,pathlib
import runtime.guarded_win32_v1.test_late_state as fixtures

class PendingCase(unittest.TestCase):
 def test_real_live_child_blocks_new_preparation_until_terminal(self):
  b,o,s,raw,e=fixtures.Cases('test_exact_expiry_consumes_without_capture').fixture();p=s.prepare('button',[1,1]);child=None
  class PendingVerifier:
   receipt=None
   def __call__(self,*args):
    nonlocal child
    child=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(60)'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    self.receipt={'reason':'termination_unconfirmed','process':child,'pid':child.pid,'exit':child.poll()}
    return None
  verifier=PendingVerifier()
  try:
   r=s.execute(p['authorization'],verify_effect=verifier,effect_deadline_ns=time.monotonic_ns()+2000000000)
   self.assertIsNone(child.poll());self.assertIsNone(r['task_success']);count=b._capture_hdc.call_count
   with self.assertRaisesRegex(ValueError,'verifier still active'):s.prepare('button',[1,1])
   self.assertEqual(b._capture_hdc.call_count,count);self.assertEqual(s.execute(p['authorization'])['error'],'AUTHORIZATION_CONSUMED_OR_UNKNOWN')
   s.recover_input()
   with self.assertRaisesRegex(ValueError,'verifier still active'):s.prepare('button',[1,1])
   child.kill();child.communicate(timeout=3);self.assertIsNotNone(child.returncode)
   self.assertTrue(s.verifier_idle());self.assertIsNone(s.pending_verifier)
   self.assertEqual(e,[['move','fixture',3,3],['release']])
   pathlib.Path('pending-raw.json').write_text(json.dumps({'child_pid':child.pid,'actual_terminal_exit':child.returncode,'effect_unknown':r['task_success'] is None,'no_extra_capture_or_input':True,'recovery_did_not_clear_live_child':True,'last_verifier_exit':s.last_verifier_exit},indent=2),encoding='utf-8')
  finally:
   if child is not None:
    if child.poll() is None:child.kill()
    child.communicate(timeout=3)

if __name__=='__main__':unittest.main()
