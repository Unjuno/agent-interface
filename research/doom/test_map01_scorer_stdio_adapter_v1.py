import json,os,tempfile,threading,time,unittest
from pathlib import Path
from independent_progress_clock_v2 import ProgressSample
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin,ScorerFileSink

def verified_release(release_ns=0, *, keycodes=None):
 return {'event':'input_release_transition','operation':'up','id':'program-1','step':2,
  'key':'d','owner_id':'owner-1','intent_token':'token-1',
  'owner_transition_verified':True,'owner_thread_keyup_verified':True,
  'owner_thread_keyup_verified_after_batch':True,
  'owner_identity_matches_after_batch':True,
  'intent_token_matches_after_batch':True,
  'owned_keycodes_after_batch':[] if keycodes is None else keycodes,
  'release_call_returned_ns':release_ns,
  'owner_thread_keyup_receipt':{'event':'owner_explicit_keyup','operation':'up',
   'owner_id':'owner-1','intent_token':'token-1','server_sync_completed':True}}

class Tests(unittest.TestCase):
 def test_post_release_tail_samples_until_neutral_without_reading_commands(self):
  class Clock:
   def __init__(self):self.ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def __init__(self,c):self.c=c;self.waits=[];self.reads=0
   def clock_ns(self):return self.c.now()
   def wait_readable(self,fd,timeout):self.waits.append((fd,timeout));self.c.ns+=round(timeout*1e9);return False
  clock=Clock();loop=Loop(clock);values=iter([{'right':1},{'right':0}]);rows=[];commands=[]
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:7})(),
      lambda:next(values),rows.append,loop=loop)
  adapter.command_handler=lambda value:commands.append(value)
  release=clock.ns
  result=adapter.sample_tail(release_receipt=verified_release(release),max_duration_ns=50,
      max_samples=5,stop_when=lambda sample:sample['right']==0)
  self.assertEqual(result['disposition'],'STOP_CONDITION_OBSERVED')
  self.assertEqual(result['termination'],'predicate')
  self.assertEqual(result['tail_samples'],2)
  self.assertTrue(all(row['post_release_tail'] for row in rows))
  self.assertEqual([row['release_returned_ns'] for row in rows],[release,release])
  self.assertEqual([row['intent_token'] for row in rows],['token-1','token-1'])
  self.assertEqual(commands,[]);self.assertEqual(loop.reads,0)

 def test_post_release_tail_deadline_is_censored(self):
  class Clock:
   def __init__(self):self.ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def __init__(self,c):self.c=c
   def clock_ns(self):return self.c.now()
   def wait_readable(self,fd,timeout):self.c.ns+=round(timeout*1e9);return False
  clock=Clock();rows=[];loop=Loop(clock)
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:9})(),
      lambda:{'right':1},rows.append,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=25,
      max_samples=5,stop_when=lambda sample:sample['right']==0)
  self.assertEqual(result['disposition'],'CENSORED')
  self.assertEqual(result['termination'],'deadline')
  self.assertFalse(result['deadline_overrun'])
  self.assertLessEqual(result['ended_ns'],result['deadline_ns'])
  self.assertEqual(result['tail_samples'],3)

 def test_post_release_tail_sample_cap_is_censored(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def __init__(self,c):self.c=c
   def clock_ns(self):return self.c.now()
   def wait_readable(self,fd,timeout):self.c.ns+=round(timeout*1e9);return False
  clock=Clock();loop=Loop(clock);adapter=MainThreadScorerStdin(
      type('Stream',(),{'fileno':lambda _self:9})(),lambda:1,lambda _row:None,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=100,
      max_samples=2,stop_when=lambda _sample:False)
  self.assertEqual(result['termination'],'sample_cap')
  self.assertEqual(result['disposition'],'CENSORED')
  self.assertEqual(result['tail_samples'],2)

 def test_post_release_tail_does_not_start_sample_beyond_deadline(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def __init__(self,c):self.c=c
   def clock_ns(self):return self.c.now()
   def wait_readable(self,fd,timeout):self.c.ns+=round(timeout*1e9);return False
  clock=Clock();loop=Loop(clock);calls=[]
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:9})(),
      lambda:calls.append(clock.ns) or 1,lambda _row:None,loop=loop)
  adapter.next_sample_ns=30
  result=adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=25,
      max_samples=5,stop_when=lambda _sample:False)
  self.assertEqual(result['tail_samples'],0)
  self.assertEqual(result['termination'],'deadline')
  self.assertEqual(calls,[])

 def test_post_release_tail_returns_before_sampling_when_command_is_ready_at_entry(self):
  class Clock:
   ns=100
   def now(self):return self.ns
  class Loop:
   period_ns=10
   max_buffer_bytes=1024
   def __init__(self,c):self.c=c;self.chunks=[b'{"op":"finish"}\n'];self.waits=0;self.reads=0
   def clock_ns(self):return self.c.now()
   def wait_readable(self,*_args):self.waits+=1;return bool(self.chunks)
   def read_fn(self,_fd,_size):self.reads+=1;return self.chunks.pop(0)
  clock=Clock();loop=Loop(clock);rows=[];samples=[]
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      lambda:samples.append(clock.ns) or 1,rows.append,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(100),
      max_duration_ns=25,max_samples=5,stop_when=lambda _sample:False)
  self.assertEqual(result['termination'],'command_ready')
  self.assertEqual(result['disposition'],'CENSORED')
  self.assertEqual(result['tail_samples'],0)
  self.assertEqual(samples,[])
  self.assertEqual(rows,[])
  self.assertEqual(loop.reads,0)
  self.assertEqual(next(adapter),'{"op":"finish"}')
  self.assertEqual(adapter.commands,1)

 def test_post_release_tail_returns_when_command_is_ready_then_adapter_resumes(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   max_buffer_bytes=1024
   def __init__(self,c):self.c=c;self.chunks=[b'{"op":"finish"}\n']
   def clock_ns(self):return self.c.now()
   def wait_readable(self,_fd,timeout):
    return timeout>0 and bool(self.chunks)
   def read_fn(self,_fd,_size):return self.chunks.pop(0)
  clock=Clock();loop=Loop(clock);rows=[]
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      lambda:1,rows.append,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(0),
      max_duration_ns=25,max_samples=5,stop_when=lambda _sample:False)
  self.assertEqual(result['termination'],'command_ready')
  self.assertEqual(result['disposition'],'CENSORED')
  self.assertEqual(len(rows),1)
  self.assertIs(rows[0]['post_release_tail'],True)
  self.assertEqual(next(adapter),'{"op":"finish"}')
  self.assertEqual(adapter.commands,1)

 def test_post_release_tail_polls_after_callback_overrun_before_next_sample(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   max_buffer_bytes=1024
   def __init__(self,c):self.c=c;self.ready=False;self.polls=[];self.reads=0
   def clock_ns(self):return self.c.now()
   def wait_readable(self,_fd,timeout):
    self.polls.append(timeout)
    return self.ready
   def read_fn(self,_fd,_size):
    self.reads+=1
    return b'{"op":"finish"}\n'
  clock=Clock();loop=Loop(clock);samples=[];rows=[]
  def slow_sample():
   samples.append(clock.ns)
   clock.ns=25
   loop.ready=True
   return {'right':1}
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      slow_sample,rows.append,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(0),
      max_duration_ns=100,max_samples=5,stop_when=lambda _sample:False)
  self.assertEqual(result['termination'],'command_ready')
  self.assertEqual(result['disposition'],'CENSORED')
  self.assertEqual(result['tail_samples'],1)
  self.assertEqual(samples,[0])
  self.assertEqual(len(rows),1)
  self.assertEqual(loop.polls,[0,0])
  self.assertEqual(loop.reads,0)
  self.assertEqual(next(adapter),'{"op":"finish"}')
  self.assertEqual(adapter.commands,1)

 def test_command_ready_during_callback_deadline_overrun_preempts_next_scorer_sample(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   max_buffer_bytes=1024
   def __init__(self,c):self.c=c;self.ready=False;self.reads=0
   def clock_ns(self):return self.c.now()
   def wait_readable(self,_fd,_timeout):return self.ready
   def read_fn(self,_fd,_size):
    self.reads+=1
    return b'{"op":"finish"}\n'
  clock=Clock();loop=Loop(clock);samples=[];rows=[]
  def slow_sample():
   samples.append(clock.ns)
   if len(samples)==1:
    clock.ns=125
    loop.ready=True
   return {'right':1}
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      slow_sample,rows.append,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(0),
      max_duration_ns=100,max_samples=5,stop_when=lambda _sample:False)
  self.assertEqual(result['termination'],'command_ready')
  self.assertTrue(result['deadline_overrun'])
  self.assertEqual(result['tail_samples'],1)
  self.assertEqual(samples,[0])
  self.assertEqual(next(adapter),'{"op":"finish"}')
  self.assertEqual(samples,[0])
  self.assertEqual(adapter.commands,1)
  self.assertEqual(loop.reads,1)

 def test_post_release_tail_wait_overshoot_is_censored_without_sample(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def __init__(self,c):self.c=c
   def clock_ns(self):return self.c.now()
   def wait_readable(self,fd,timeout):self.c.ns=30;return False
  clock=Clock();calls=[];loop=Loop(clock)
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      lambda:calls.append(clock.ns) or 1,lambda _row:None,loop=loop)
  adapter.next_sample_ns=10
  result=adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=25,
      max_samples=5,stop_when=lambda _sample:False)
  self.assertEqual(result['termination'],'deadline')
  self.assertEqual(result['tail_samples'],0)
  self.assertEqual(calls,[])

 def test_post_release_tail_getter_overrun_is_censored_even_if_neutral(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def __init__(self,c):self.c=c
   def clock_ns(self):return self.c.now()
   def wait_readable(self,fd,timeout):self.c.ns+=round(timeout*1e9);return False
  clock=Clock();loop=Loop(clock)
  def slow_neutral():clock.ns=30;return {'right':0}
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      slow_neutral,lambda _row:None,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=25,
      max_samples=5,stop_when=lambda sample:sample['right']==0)
  self.assertEqual(result['disposition'],'CENSORED')
  self.assertEqual(result['termination'],'deadline_overrun')
  self.assertTrue(result['deadline_overrun'])
  self.assertFalse(result['stop_condition_met'])

 def test_post_release_tail_sink_overrun_is_censored(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def __init__(self,c):self.c=c
   def clock_ns(self):return self.c.now()
   def wait_readable(self,fd,timeout):self.c.ns+=round(timeout*1e9);return False
  clock=Clock();loop=Loop(clock)
  def slow_sink(_row):clock.ns=30
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      lambda:{'right':0},slow_sink,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=25,
      max_samples=5,stop_when=lambda sample:sample['right']==0)
  self.assertEqual(result['termination'],'deadline_overrun')
  self.assertFalse(result['stop_condition_met'])

 def test_post_release_tail_predicate_overrun_is_censored(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def __init__(self,c):self.c=c
   def clock_ns(self):return self.c.now()
   def wait_readable(self,fd,timeout):self.c.ns+=round(timeout*1e9);return False
  clock=Clock();loop=Loop(clock)
  def slow_predicate(_sample):clock.ns=30;return True
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      lambda:{'right':0},lambda _row:None,loop=loop)
  result=adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=25,
      max_samples=5,stop_when=slow_predicate)
  self.assertEqual(result['termination'],'deadline_overrun')
  self.assertFalse(result['stop_condition_met'])

 def test_post_release_tail_rejects_invalid_bounds_and_pre_release_start(self):
  class Clock:
   def now(self):return 4
  class Loop:
   period_ns=10
   def clock_ns(self):return 4
   def wait_readable(self,*_args):return False
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      lambda:1,lambda _row:None,loop=Loop())
  for kwargs in (
      {'release_receipt':verified_release(True),'max_duration_ns':10,'max_samples':1},
      {'release_receipt':verified_release(0),'max_duration_ns':-1,'max_samples':1},
      {'release_receipt':verified_release(0),'max_duration_ns':10,'max_samples':0},
  ):
   with self.assertRaises(ValueError):adapter.sample_tail(**kwargs)
  with self.assertRaisesRegex(ValueError,'before verified release'):
   adapter.sample_tail(release_receipt=verified_release(5),max_duration_ns=10,max_samples=1)

 def test_post_release_tail_rejects_unverified_or_nonempty_release(self):
  class Loop:
   period_ns=10
   def clock_ns(self):return 0
   def wait_readable(self,*_args):return False
  adapter=MainThreadScorerStdin(type('Stream',(),{'fileno':lambda _self:0})(),
      lambda:1,lambda _row:None,loop=Loop())
  invalid=[None,{},
   {**verified_release(),'owner_thread_keyup_verified':False},
   {**verified_release(),'owner_thread_keyup_verified_after_batch':False},
   verified_release(keycodes=[40]),
   {**verified_release(),'owner_thread_keyup_receipt':{
    'event':'owner_explicit_keyup','operation':'up','owner_id':'owner-1',
    'intent_token':'other-token','server_sync_completed':True}},
  ]
  for receipt in invalid:
   with self.subTest(receipt=receipt),self.assertRaises(ValueError):
    adapter.sample_tail(release_receipt=receipt,max_duration_ns=10,max_samples=1)

 def test_post_release_tail_requires_quiescent_command_stream(self):
  class Clock:
   ns=0
   def now(self):return self.ns
  class Loop:
   period_ns=10
   def clock_ns(self):return 0
   def wait_readable(self,fd,timeout):return False
  stream=type('Stream',(),{'fileno':lambda _self:0})()
  adapter=MainThreadScorerStdin(stream,lambda:1,lambda _row:None,loop=Loop())
  adapter.buffer.extend(b'queued\n')
  with self.assertRaisesRegex(RuntimeError,'empty command buffer'):
   adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=10,max_samples=1)
  adapter.buffer.clear();adapter.eof=True
  with self.assertRaisesRegex(RuntimeError,'after command EOF'):
   adapter.sample_tail(release_receipt=verified_release(0),max_duration_ns=10,max_samples=1)

 @unittest.skipIf(os.name=='nt','select() cannot wait on anonymous pipes on Windows')
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
