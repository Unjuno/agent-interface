import threading,time,unittest
from PIL import Image
from research.live_control.calc_bounded_proposal_v1 import BoundedProposal

class BoundedProposalTests(unittest.TestCase):
 def test_completed_result_is_detached_and_one_shot(self):
  returned={'point':[1,2]};worker=BoundedProposal(lambda n,i:returned,timeout_ms=200,cancelled=lambda:False)
  value=worker({'sequence':1},Image.new('RGB',(4,4)))
  self.assertEqual(value,{'point':[1,2]});value['point'][0]=99
  self.assertEqual(returned['point'],[1,2]);self.assertIsNone(worker({},Image.new('RGB',(4,4))))
 def test_timeout_discards_late_result_and_refuses_reuse(self):
  entered=threading.Event();release=threading.Event()
  def slow(_,__):entered.set();release.wait(2);return {'point':[1,2]}
  worker=BoundedProposal(slow,timeout_ms=30,cancelled=lambda:False)
  started=time.monotonic();result=worker({},Image.new('RGB',(4,4)))
  self.assertTrue(entered.is_set());self.assertIsNone(result);self.assertLess(time.monotonic()-started,1.0)
  self.assertTrue(worker.snapshot()['retired']);self.assertIsNone(worker({},Image.new('RGB',(4,4))))
  release.set();worker.thread.join(1);self.assertFalse(worker.thread.is_alive())
 def test_cancel_before_or_during_wait_discards_result(self):
  release=threading.Event();entered=threading.Event();cancel=threading.Event()
  def slow(_,__):entered.set();release.wait(2);return {'point':[1,2]}
  worker=BoundedProposal(slow,timeout_ms=500,cancelled=cancel.is_set)
  result=[];thread=threading.Thread(target=lambda:result.append(worker({},Image.new('RGB',(4,4)))))
  thread.start();self.assertTrue(entered.wait(1));cancel.set();thread.join(1)
  self.assertFalse(thread.is_alive());self.assertEqual(result,[None]);release.set();worker.thread.join(1)
 def test_cancel_before_dispatch_never_starts_worker(self):
  called=[];worker=BoundedProposal(lambda n,i:called.append(True),timeout_ms=30,cancelled=lambda:True)
  self.assertIsNone(worker({},Image.new('RGB',(4,4))))
  self.assertEqual(called,[]);self.assertIsNone(worker.thread);self.assertTrue(worker.snapshot()['retired'])
 def test_deadline_expiring_during_snapshot_copy_does_not_start_worker(self):
  calls=[]
  class SlowImage:
   def copy(self):time.sleep(.04);return object()
  worker=BoundedProposal(lambda n,i:calls.append(True),timeout_ms=10,cancelled=lambda:False)
  self.assertIsNone(worker({},SlowImage()))
  self.assertEqual(calls,[]);self.assertIsNone(worker.thread);self.assertTrue(worker.snapshot()['retired'])
 def test_cancellation_during_snapshot_copy_does_not_start_worker(self):
  cancel=threading.Event();calls=[]
  class CancelOnCopy:
   def copy(self):cancel.set();return object()
  worker=BoundedProposal(lambda n,i:calls.append(True),timeout_ms=500,cancelled=cancel.is_set)
  self.assertIsNone(worker({},CancelOnCopy()))
  self.assertEqual(calls,[]);self.assertIsNone(worker.thread);self.assertTrue(worker.snapshot()['retired'])
 def test_callback_failure_is_unavailable_without_retry(self):
  def fail(_,__):raise ValueError('inert')
  worker=BoundedProposal(fail,timeout_ms=300,cancelled=lambda:False)
  self.assertIsNone(worker({},Image.new('RGB',(4,4))))
  self.assertIsNone(worker({},Image.new('RGB',(4,4))))