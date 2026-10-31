"""Bounded shared-file retry: inject PermissionError without external GUI."""
import unittest
from unittest.mock import patch
import exchange_io

class Clock:
 def __init__(self):self.t=0.0
 def now(self):return self.t
 def sleep(self,seconds):self.t+=seconds

class RetryTests(unittest.TestCase):
 def test_transient_permission_failures_retry_same_read(self):
  clock=Clock();calls=[];events=[]
  def read():
   calls.append(1)
   if len(calls)<3:raise PermissionError('injected')
   return b'expected'
  result=exchange_io.retry_permission(read,stage='request_read',clock=clock.now,sleep=clock.sleep,timeout=.1,interval=.02,observe=events.append)
  self.assertEqual(result,b'expected');self.assertEqual(len(calls),3);self.assertEqual([e['attempt'] for e in events],[1,2]);self.assertEqual(clock.t,.04)
 def test_persistent_denial_stops_at_deadline(self):
  clock=Clock();calls=[]
  def denied():calls.append(1);raise PermissionError('injected')
  with self.assertRaises(PermissionError):exchange_io.retry_permission(denied,stage='image_read',clock=clock.now,sleep=clock.sleep,timeout=.05,interval=.02)
  self.assertLessEqual(clock.t,.05);self.assertEqual(len(calls),4)
 def test_other_errors_are_not_retried(self):
  calls=[]
  def bad():calls.append(1);raise ValueError('invalid data')
  with self.assertRaises(ValueError):exchange_io.retry_permission(bad,stage='request_read')
  self.assertEqual(len(calls),1)
 def test_model_call_not_repeated_by_publication_retry(self):
  clock=Clock();calls=[];publications=[]
  def model():calls.append(1);return b'answer'
  result=model()
  def publish():
   publications.append(result)
   if len(publications)==1:raise PermissionError('injected')
   return 'published'
  self.assertEqual(exchange_io.retry_permission(publish,stage='response_publish',clock=clock.now,sleep=clock.sleep,timeout=.1,interval=.01),'published')
  self.assertEqual(len(calls),1);self.assertEqual(publications,[b'answer',b'answer'])
if __name__=='__main__':unittest.main()
