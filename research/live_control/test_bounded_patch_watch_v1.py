import threading,time,unittest
from research.live_control.bounded_patch_watch_v1 import BoundedPatchWatch

class Probe:
 def __init__(self, values, held=None):
  self.values=list(values);self.held_values=list(held or [True]*(len(values))+[False]);self.closed=False
 def held(self):return self.held_values.pop(0) if self.held_values else False
 def capture(self):
  value=self.values.pop(0)
  if isinstance(value,Exception):raise value
  return value,{'id':len(self.values)}
 def close(self):self.closed=True

class WatchTests(unittest.TestCase):
 def start(self,probe,cancels,**kwargs):
  watch=BoundedPatchWatch(open_probe=lambda:probe,reference=bytes(192),token='unique-1',cancel=lambda token:cancels.append(token) or {'status':'cancel_requested','release_confirmed':False},interval_s=.001,deadline_s=.2,max_samples=10,**kwargs);watch.start();return watch
 def test_change_requests_one_scoped_cancel_and_does_not_claim_release(self):
  p=Probe([bytes(192),bytes([255])*192]);calls=[];w=self.start(p,calls);r=w.join(1)
  self.assertEqual(r['status'],'change_detected');self.assertEqual(calls,['unique-1']);self.assertEqual(len(r['samples']),2);self.assertFalse(r['cancel']['release_confirmed']);self.assertTrue(p.closed)
 def test_held_end_never_claims_release_or_requests_cancel(self):
  p=Probe([bytes(192)],held=[True,False]);calls=[];r=self.start(p,calls).join(1)
  self.assertEqual(r['status'],'held_ended');self.assertEqual(calls,[]);self.assertFalse(r['release_verified']);self.assertTrue(p.closed)
 def test_capture_error_requests_cancel_but_keeps_effect_unknown(self):
  p=Probe([OSError('capture')]);calls=[];r=self.start(p,calls).join(1)
  self.assertEqual(r['status'],'monitor_error');self.assertEqual(calls,['unique-1']);self.assertEqual(r['error_type'],'OSError');self.assertFalse(r['release_verified'])
 def test_sample_budget_requests_cancel_when_held(self):
  p=Probe([bytes(192)]*12);calls=[];r=self.start(p,calls).join(1)
  self.assertEqual(r['status'],'budget_exhausted');self.assertEqual(calls,['unique-1']);self.assertEqual(len(r['samples']),10)
 def test_slow_held_query_does_not_capture_after_deadline(self):
  class Slow(Probe):
   def held(self):time.sleep(.25);return True
   def capture(self):self.fail_capture=True;return bytes(192),{}
  p=Slow([]);p.fail_capture=False;calls=[];r=self.start(p,calls).join(1)
  self.assertEqual(r['status'],'budget_exhausted');self.assertFalse(p.fail_capture);self.assertEqual(calls,['unique-1'])
 def test_late_capture_is_not_accepted_as_fresh(self):
  class Slow(Probe):
   def capture(self):time.sleep(.25);return bytes(192),{}
  p=Slow([],held=[True]);calls=[];r=self.start(p,calls).join(1)
  self.assertEqual(r['status'],'budget_exhausted');self.assertEqual(calls,['unique-1']);self.assertEqual(len(r['samples']),1)
 def test_invalid_capture_requests_cancel(self):
  p=Probe([b'short']);calls=[];r=self.start(p,calls).join(1)
  self.assertEqual(r['status'],'monitor_error');self.assertEqual(r['error_type'],'ValueError');self.assertEqual(calls,['unique-1'])
 def test_cancel_timestamp_brackets_callback_and_remains_distinct_from_release(self):
  p=Probe([bytes([255])*192]);times=[]
  def cancel(token):
   times.append(time.monotonic_ns());return {'status':'cancel_requested','release_confirmed':False}
  w=BoundedPatchWatch(open_probe=lambda:p,reference=bytes(192),token='time-token',cancel=cancel,interval_s=.001,deadline_s=.2,max_samples=10);w.start();r=w.join(1)
  self.assertLessEqual(r['samples'][-1]['capture_ended_ns'],r['cancel_started_ns']);self.assertLessEqual(r['cancel_started_ns'],times[0]);self.assertLessEqual(times[0],r['cancel_finished_ns']);self.assertLessEqual(r['cancel_finished_ns'],r['finished_ns']);self.assertFalse(r['release_verified'])
 def test_cancel_exception_still_retains_timestamps_and_unknown_release(self):
  p=Probe([OSError('capture')])
  def cancel(token):raise OSError('cancel')
  w=BoundedPatchWatch(open_probe=lambda:p,reference=bytes(192),token='time-token',cancel=cancel,interval_s=.001,deadline_s=.2,max_samples=10);w.start();r=w.join(1)
  self.assertEqual(r['status'],'monitor_error');self.assertEqual(r['cancel_error_type'],'OSError');self.assertLessEqual(r['cancel_started_ns'],r['cancel_finished_ns']);self.assertFalse(r['release_verified'])
 def test_duplicate_start_rejected(self):
  p=Probe([bytes(192)],held=[False,False]);calls=[];w=self.start(p,calls)
  with self.assertRaises(RuntimeError):w.start()
  w.join(1)
 def test_old_token_cannot_cancel_a_new_bridge_scope(self):
  from runtime.guarded_x11_v1.bridge import NativeHandleBridge
  bridge=NativeHandleBridge.__new__(NativeHandleBridge);bridge._target_queries=object();bridge._cancel_lock=threading.Lock();bridge._cancel_ticket=None;bridge._used_cancel_tokens=set();bridge.active=('owned',);bridge.review_required=False
  probe=Probe([bytes([255])*192]);
  with bridge.cancellation_scope('first'):
   watch=BoundedPatchWatch(open_probe=lambda:probe,reference=bytes(192),token='first',cancel=bridge.request_cancel,interval_s=.001,deadline_s=.2,max_samples=10);watch.start();result=watch.join(1);self.assertEqual(result['cancel']['status'],'cancel_requested')
  bridge.review_required=False
  with bridge.cancellation_scope('second'):
   self.assertEqual(bridge.request_cancel('first')['status'],'not_active');self.assertFalse(bridge._cancel_requested());self.assertFalse(bridge.review_required)
  with self.assertRaises(RuntimeError):
   with bridge.cancellation_scope('first'):pass
 def test_blocked_capture_join_returns_running_not_false_success(self):
  gate=threading.Event()
  class Blocked(Probe):
   def capture(self):gate.wait();return bytes(192),{}
  p=Blocked([],held=[True,False]);calls=[];w=self.start(p,calls);time.sleep(.02);r=w.join(.01)
  self.assertEqual(r['status'],'running');gate.set();self.assertEqual(w.join(1)['status'],'held_ended')

if __name__=='__main__':unittest.main()
