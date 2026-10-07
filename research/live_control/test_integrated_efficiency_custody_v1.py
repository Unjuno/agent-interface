import importlib.util,pathlib,sys,tempfile,unittest
from unittest.mock import patch, Mock
W=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(W))
import integrated_efficiency_client_v1 as m
class Close(unittest.TestCase):
 def setUp(self):
  self.out=tempfile.TemporaryDirectory();self.addCleanup(self.out.cleanup);self.c=m.RuntimeClient(pathlib.Path(self.out.name),1);self.c.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.c.temporary.cleanup);self.temp=pathlib.Path(self.c.temporary.name);self.c.journal=self.temp/'journal.jsonl';self.c.journal.write_bytes(b'original checkpoint\n');self.d=pathlib.Path(str(self.c.journal)+'.invalid-response.json');self.d.write_bytes(b'original diagnostic\n')
 def test_process_wait_failure_still_retains_and_keeps_temp(self):
  self.c.process=Mock();self.c.process.poll.return_value=None;failure=TimeoutError('owned child did not exit');self.c.process.wait.side_effect=failure
  with self.assertRaises(TimeoutError) as caught:self.c.close()
  self.assertIs(caught.exception,failure);self.assertEqual((self.c.root/self.d.name).read_bytes(),self.d.read_bytes());self.assertTrue(self.temp.exists());self.assertFalse(self.c.temporary._finalizer.alive)
 def test_stderr_failure_still_retains(self):
  self.c.errors=Mock();failure=OSError('stderr close failure');self.c.errors.close.side_effect=failure
  with self.assertRaises(OSError) as caught:self.c.close()
  self.assertIs(caught.exception,failure);self.assertEqual((self.c.root/self.d.name).read_bytes(),b'original diagnostic\n');self.assertFalse(self.temp.exists())
 def test_two_cleanup_failures_preserve_first_and_note_second(self):
  self.c.process=Mock();self.c.process.poll.return_value=None;failure=RuntimeError('terminate failed');self.c.process.terminate.side_effect=failure;self.c.errors=Mock();self.c.errors.close.side_effect=OSError('stderr failed')
  with self.assertRaises(RuntimeError) as caught:self.c.close()
  self.assertIs(caught.exception,failure);self.assertTrue(any('stderr failed' in n for n in failure.__notes__));self.assertTrue((self.c.root/self.d.name).exists());self.assertTrue(self.temp.exists())
 def test_real_rejection_through_client_context(self):
  import json
  from received_continuation_v1 import start
  from append_checkpoint_v1 import load
  from event_cursor_v5 import EventCursor
  import durable_submit_v4 as d
  self.c.journal.unlink();self.d.unlink();d.initialize(self.c.journal,start('inert-close-session'));sent=[]
  def exchange(session,q,timeout):
   sent.append(q);cursor=EventCursor();cursor.append({'event':'command','command':dict(q['command'],transport_request_id=q['request_id'])});cursor.append({'event':'rejected','reason':'unsupported text'});return cursor.read_until(q['after'],q['events'],timeout=0,action_id=q['action_id'])
  def run(path,request):return d.run(path,request,call=exchange)
  with patch.object(m,'run',run):
   try:self.c.call({'timeout':1,'command':{'op':'submit','steps':[{'op':'text','text':'Value'}]}})
   except ValueError as primary:self.c.__exit__(ValueError,primary,None);self.assertEqual(str(primary),'unresolved reply status')
   else:self.fail('expected unresolved rejection')
  self.assertEqual(len(sent),1);self.assertFalse(self.temp.exists());retained=load(self.c.root/self.c.journal.name);self.assertIsNotNone(retained['pending']);receipt=json.loads((self.c.root/self.d.name).read_text());self.assertEqual(receipt['response']['status'],'unattributed_rejection');self.assertFalse(receipt['replay_allowed'])
 def test_copies_and_reads_back_before_cleanup(self):
  self.c.close();self.assertFalse(self.temp.exists());self.assertEqual((self.c.root/self.d.name).read_bytes(),b'original diagnostic\n');self.assertEqual((self.c.root/self.c.journal.name).read_bytes(),b'original checkpoint\n')
 def test_conflict_preserves_source_and_existing(self):
  target=self.c.root/self.d.name;target.write_bytes(b'prior evidence')
  with self.assertRaises(FileExistsError):self.c.close()
  self.assertTrue(self.temp.exists());self.assertEqual(target.read_bytes(),b'prior evidence');self.assertFalse(self.c.temporary._finalizer.alive)
 def test_context_primary_preserved_on_custody_failure(self):
  primary=ValueError('original failure');(self.c.root/self.d.name).write_bytes(b'conflict');self.c.__exit__(ValueError,primary,None);self.assertEqual(str(primary),'original failure');self.assertTrue(any('client close failed' in n for n in primary.__notes__));self.assertTrue(self.temp.exists())
 def test_no_primary_reports_custody_failure(self):
  (self.c.root/self.d.name).write_bytes(b'conflict')
  with self.assertRaises(FileExistsError):self.c.__exit__(None,None,None)
 def test_matching_retained_files_allow_cleanup(self):
  for p in (self.c.journal,self.d):(self.c.root/p.name).write_bytes(p.read_bytes())
  self.c.close();self.assertFalse(self.temp.exists())
if __name__=='__main__':unittest.main()
