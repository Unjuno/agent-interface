import json,tempfile,unittest
from pathlib import Path
from exchange_wait import wait_response,HostFailure

class Clock:
 def __init__(self):self.value=0
 def now(self):return self.value
 def sleep(self,amount):self.value+=amount

class WaitTests(unittest.TestCase):
 def test_host_failure_stops_before_response_deadline(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'failure.json').write_text(json.dumps({'kind':'host_failed','error_type':'PermissionError','completed_calls':5}));clock=Clock()
   with self.assertRaises(HostFailure) as error:wait_response(p/'response.json',p/'failure.json',timeout=120,clock=clock.now,sleep=clock.sleep)
   self.assertLess(clock.value,1);self.assertEqual(error.exception.error_type,'PermissionError');self.assertEqual(error.exception.completed_calls,5)
 def test_response_wins_when_both_are_already_published(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'failure.json').write_text('{}');(p/'response.json').write_text('{"ok":true}')
   self.assertEqual(wait_response(p/'response.json',p/'failure.json'),{'ok':True})
 def test_malformed_failure_signal_stops_without_success(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'failure.json').write_text('{bad}')
   with self.assertRaises(HostFailure):wait_response(p/'response.json',p/'failure.json')
 def test_no_signal_keeps_original_finite_timeout(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);clock=Clock()
   with self.assertRaises(TimeoutError):wait_response(p/'response.json',p/'failure.json',timeout=.1,interval=.03,clock=clock.now,sleep=clock.sleep)
   self.assertAlmostEqual(clock.value,.1)
if __name__=='__main__':unittest.main()
