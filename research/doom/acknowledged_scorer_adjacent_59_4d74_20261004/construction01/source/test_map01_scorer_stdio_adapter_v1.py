import json,os,tempfile,threading,time,unittest
from pathlib import Path
from independent_progress_clock_v2 import ProgressSample
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin,ScorerFileSink
class Tests(unittest.TestCase):
 def test_pipe_wait_samples_and_wakes_on_command(self):
  r,w=os.pipe();stream=os.fdopen(r,'r');owner=threading.get_ident();counter=[0]
  with tempfile.TemporaryDirectory() as tmp:
   sink=ScorerFileSink(Path(tmp))
   def sample():counter[0]+=1;return ProgressSample(counter[0]*1_000_000,0,0,False,False,False)
   adapter=MainThreadScorerStdin(stream,sample,sink,sample_hz=50)
   def writer():time.sleep(.055);os.write(w,b'{"op":"finish"}\n');os.close(w)
   t=threading.Thread(target=writer);t.start();start=time.perf_counter();line=next(adapter);elapsed=time.perf_counter()-start;t.join();stream.close()
   self.assertIn('finish',line);self.assertGreaterEqual(adapter.samples,3);self.assertLess(elapsed,.12);self.assertEqual(adapter.owner_thread,owner)
 def test_scorer_files_never_mark_controller_visible(self):
  with tempfile.TemporaryDirectory() as tmp:
   sink=ScorerFileSink(Path(tmp));sample=ProgressSample(1,0,0,False,False,False)
   sink({'scheduled_ns':1,'sample_started_ns':1,'sample_finished_ns':2,'start_lateness_ns':0,'missed_periods_before':0,'payload':sample})
   row=json.loads((Path(tmp)/'scorer-samples.jsonl').read_text().strip());self.assertIs(row['controller_visible'],False);self.assertEqual(row['payload']['schema'],'independent-progress-sample-v2')
 def test_event_clock_v2_composes_with_receipts(self):
  with tempfile.TemporaryDirectory() as tmp:
   sink=ScorerFileSink(Path(tmp))
   for s in [ProgressSample(1,0,0,False,False,False),ProgressSample(2,1,0,False,False,False)]:sink({'scheduled_ns':s.sample_ns,'sample_started_ns':s.sample_ns,'sample_finished_ns':s.sample_ns,'start_lateness_ns':0,'missed_periods_before':0,'payload':s})
   event=json.loads((Path(tmp)/'scorer-events.jsonl').read_text().strip());self.assertEqual(event['kind'],'KILL_COUNT_INCREASE');self.assertEqual(event['schema'],'independent-progress-event-v2');self.assertIs(event['controller_visible'],False)
 def test_terminal_repeat_allowed_but_mutation_fails(self):
  with tempfile.TemporaryDirectory() as tmp:
   sink=ScorerFileSink(Path(tmp));base={'scheduled_ns':1,'sample_started_ns':1,'sample_finished_ns':1,'start_lateness_ns':0,'missed_periods_before':0}
   sink({**base,'payload':ProgressSample(1,0,0,False,False,False)});sink({**base,'scheduled_ns':2,'payload':ProgressSample(2,0,0,True,False,True)});sink({**base,'scheduled_ns':3,'payload':ProgressSample(3,0,0,True,False,True)})
   with self.assertRaisesRegex(ValueError,'terminal scorer state mutated'):sink({**base,'scheduled_ns':4,'payload':ProgressSample(4,1,0,True,False,True)})
 def test_non_progress_payload_fails_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   sink=ScorerFileSink(Path(tmp))
   with self.assertRaises(TypeError):sink({'payload':None})
if __name__=='__main__':unittest.main()
