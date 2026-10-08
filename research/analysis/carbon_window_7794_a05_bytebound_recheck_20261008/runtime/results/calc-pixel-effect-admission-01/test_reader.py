import json,subprocess,sys,tempfile,unittest
from pathlib import Path
reader=Path(__file__).with_name('read_stage-v2.py')
class ReaderTests(unittest.TestCase):
 def invoke(self,rows,wanted):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);(p/'primary-stream.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
   return subprocess.run([sys.executable,str(reader),directory,str(wanted)],capture_output=True,text=True)
 def test_consumed_error_is_returned_without_poll_or_replay(self):
  row={'status':'command_error','command_id':2,'command_method':'review','replay_allowed':False,'state':{'next_id':3,'stopped':'invalid review'}}
  p=self.invoke([row],2);self.assertEqual(p.returncode,0)
  r=json.loads(p.stdout);self.assertEqual(r['status'],'command_failed');self.assertEqual(r['command'],row)
  self.assertIs(r['wait_same_handle'],False);self.assertIs(r['resend_allowed'],False)
 def test_pre_admission_id_is_not_inferred_from_next_id(self):
  row={'status':'command_error','command_id':9,'command_method':'observe','state':{'next_id':1}}
  p=self.invoke([row],9);r=json.loads(p.stdout);self.assertEqual(r['status'],'command_failed')
  self.assertEqual(r['command']['command_id'],9)
 def test_legacy_error_is_unattributed_not_waiting_or_assigned_to_command(self):
  row={'status':'command_error','error':'old failure','state':{'next_id':3}}
  p=self.invoke([row],2);r=json.loads(p.stdout)
  self.assertEqual(r['status'],'stream_error_correlation_unavailable');self.assertEqual(r['errors'],[row])
  self.assertIs(r['wait_same_handle'],False);self.assertIs(r['resend_allowed'],False)
 def test_duplicate_error_identity_refuses_ambiguous_record(self):
  row={'status':'command_error','command_id':2}
  p=self.invoke([row,row],2);self.assertNotEqual(p.returncode,0)
 def test_absent_record_retains_wait_same_handle_without_resend(self):
  p=self.invoke([],2);r=json.loads(p.stdout);self.assertEqual(r['status'],'command_not_yet_observed')
  self.assertIs(r['wait_same_handle'],True);self.assertIs(r['resend_allowed'],False)
if __name__=='__main__':unittest.main()
