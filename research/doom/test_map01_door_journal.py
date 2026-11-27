import unittest,threading
from map01_door_journal import DoorEventJournal

class DummyContract:
 def __init__(self, fail=False):self.calls=[];self.fail=fail
 def completed(self,identifier,terminal,accepted,events):
  self.calls.append((identifier,terminal,accepted,events))
  if self.fail:raise ValueError('bad release')

class DummyExecutor:
 def __init__(self,active=None):
  self.lock=threading.RLock();self.active=active;self.admission_publication_errors={};self.terminal_publication_errors={};self.release_publication_errors={}

class DoorJournalTests(unittest.TestCase):
 def test_terminal_does_not_validate_inside_emit(self):
  j=DoorEventJournal();j.begin('a',100);c=DummyContract()
  j.record({'event':'accepted','id':'a'});j.record({'event':'terminal','id':'a'})
  self.assertEqual(j.complete_if_idle('a',c,DummyExecutor(active=('a',)),lambda:50),'WAIT')
  self.assertEqual(c.calls,[])
  self.assertEqual(j.complete_if_idle('a',c,DummyExecutor(),lambda:50),'DONE')
  self.assertEqual(len(c.calls),1)
 def test_record_is_a_snapshot_and_duplicate_terminal_holds(self):
  j=DoorEventJournal();j.begin('a',100);c=DummyContract()
  accepted={'event':'accepted','id':'a','nested':{'value':1}}
  j.record(accepted);accepted['nested']['value']=2
  j.record({'event':'terminal','id':'a'})
  self.assertEqual(j.complete_if_idle('a',c,DummyExecutor(),lambda:50),'DONE')
  self.assertEqual(c.calls[0][2]['nested']['value'],1)
  k=DoorEventJournal();k.begin('a',100);k.record({'event':'accepted','id':'a'})
  k.record({'event':'terminal','id':'a'});k.record({'event':'terminal','id':'a'})
  self.assertEqual(k.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:50),'HOLD')
 def test_validation_failure_is_sticky_and_blocks_next_operation(self):
  j=DoorEventJournal();j.begin('a',100);c=DummyContract(fail=True)
  j.record({'event':'accepted','id':'a'});j.record({'event':'terminal','id':'a'})
  self.assertEqual(j.complete_if_idle('a',c,DummyExecutor(),lambda:50),'HOLD')
  self.assertEqual(j.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:50),'HOLD')
  self.assertFalse(j.ready)
 def test_completed_evidence_is_a_snapshot_and_failure_is_sticky(self):
  j=DoorEventJournal();j.begin('a',100)
  j.record({'event':'accepted','id':'a','nested':{'value':1}})
  j.record({'event':'terminal','id':'a'})
  self.assertEqual(j.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:50),'DONE')
  accepted,terminal=j.completion('a')
  accepted['nested']['value']=8
  self.assertEqual(j.completion('a')[0]['nested']['value'],1)
  j.fail('uncertain dispatch');self.assertFalse(j.ready)
  self.assertEqual(j.failure,'uncertain dispatch')
  with self.assertRaises(ValueError):j.begin('b',200)
 def test_completed_last_observation_is_exact_snapshot(self):
  j=DoorEventJournal();j.begin('a',100)
  j.record({'event':'accepted','id':'a'})
  j.record({'event':'observation','id':'a','sequence':1,'nested':{'value':1}})
  j.record({'event':'observation','id':'a','sequence':2,'nested':{'value':2}})
  j.record({'event':'terminal','id':'a'})
  self.assertEqual(j.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:50),'DONE')
  row=j.latest_observation('a');self.assertEqual(row['sequence'],2)
  row['nested']['value']=3;self.assertEqual(j.latest_observation('a')['nested']['value'],2)
 def test_late_or_duplicate_events_cannot_be_ignored(self):
  j=DoorEventJournal();j.begin('a',100);c=DummyContract()
  j.record({'event':'accepted','id':'a'});j.record({'event':'terminal','id':'a'})
  self.assertEqual(j.complete_if_idle('a',c,DummyExecutor(),lambda:50),'DONE')
  j.record({'event':'input_admission','id':'a'})
  self.assertFalse(j.ready)
 def test_unknown_operation_and_publication_error_hold(self):
  j=DoorEventJournal();j.begin('a',100)
  j.record({'event':'input_admission','id':'unregistered'})
  self.assertFalse(j.ready)
  k=DoorEventJournal();k.begin('a',100)
  executor=DummyExecutor(active=('a',));executor.terminal_publication_errors['a']={'status':'delivery_unknown'}
  self.assertEqual(k.complete_if_idle('a',DummyContract(),executor,lambda:50),'HOLD')
 def test_wait_has_absolute_bound_and_idle_without_terminal_holds(self):
  j=DoorEventJournal();j.begin('a',100);j.record({'event':'accepted','id':'a'})
  self.assertEqual(j.complete_if_idle('a',DummyContract(),DummyExecutor(active=('a',)),lambda:99),'WAIT')
  self.assertEqual(j.complete_if_idle('a',DummyContract(),DummyExecutor(active=('a',)),lambda:100),'HOLD')
  k=DoorEventJournal();k.begin('a',100);k.record({'event':'accepted','id':'a'})
  self.assertEqual(k.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:50),'HOLD')
 def test_blocked_executor_lock_never_blocks_deadline(self):
  j=DoorEventJournal();j.begin('a',100);executor=DummyExecutor(active=('a',))
  acquired=threading.Event();release=threading.Event()
  def hold_lock():
   with executor.lock:
    acquired.set();release.wait(3)
  thread=threading.Thread(target=hold_lock);thread.start()
  self.assertTrue(acquired.wait(1))
  try:
   self.assertEqual(j.complete_if_idle('a',DummyContract(),executor,lambda:99),'WAIT')
   self.assertEqual(j.complete_if_idle('a',DummyContract(),executor,lambda:100),'HOLD')
  finally:
   release.set();thread.join(2)
 def test_unknown_key_hold_and_unverified_release_are_sticky(self):
  for event in ({'event':'keys_held','id':'other'},
                {'event':'input_release_unverified','id':'a'}):
   with self.subTest(event=event):
    j=DoorEventJournal();j.begin('a',100);j.record(event)
    self.assertFalse(j.ready)
    self.assertEqual(j.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:50),'HOLD')
 def test_unknown_release_publication_and_late_lock_acquisition_hold(self):
  j=DoorEventJournal();j.begin('a',100)
  j.record({'event':'accepted','id':'a'})
  j.record({'event':'terminal','id':'a','input_release_publication':{'status':'delivery_unknown'}})
  self.assertEqual(j.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:50),'HOLD')
  k=DoorEventJournal();k.begin('a',100)
  k.record({'event':'accepted','id':'a'});k.record({'event':'terminal','id':'a'})
  clocks=iter((99,100))
  self.assertEqual(k.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:next(clocks)),'HOLD')
 def test_completion_check_cannot_finish_after_deadline(self):
  j=DoorEventJournal();j.begin('a',100)
  j.record({'event':'accepted','id':'a'});j.record({'event':'terminal','id':'a'})
  clock_values=iter((90,95,100))
  self.assertEqual(j.complete_if_idle('a',DummyContract(),DummyExecutor(),lambda:next(clock_values)),'HOLD')
  self.assertFalse(j.ready)
 def test_real_executor_blocked_terminal_sink_does_not_block_supervision(self):
  import time
  from executor_v13 import Executor
  from test_executor_v13 import Backend
  terminal_started=threading.Event();unblock=threading.Event()
  journal=DoorEventJournal();journal.begin('a',100)
  def emit(row):
   journal.record(row)
   if row.get('event')=='terminal':
    terminal_started.set();unblock.wait(3)
  executor=Executor(Backend(),emit)
  try:
   executor.submit('a',[{'op':'hold'}],1,time.perf_counter_ns()+5_000_000_000)
   self.assertTrue(terminal_started.wait(2))
   self.assertEqual(journal.complete_if_idle('a',DummyContract(),executor,lambda:99),'WAIT')
   self.assertEqual(journal.complete_if_idle('a',DummyContract(),executor,lambda:100),'HOLD')
  finally:
   unblock.set();executor.close()
 def test_overflow_fails_closed_without_raising_from_emit(self):
  j=DoorEventJournal(max_events=1);j.begin('a',100);j.record({'event':'accepted','id':'a'})
  j.record({'event':'terminal','id':'a'})
  self.assertFalse(j.ready)
if __name__=='__main__':unittest.main()
