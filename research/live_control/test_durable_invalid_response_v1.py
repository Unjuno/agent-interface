import importlib.util,pathlib,sys,json,tempfile,unittest,hashlib
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from received_continuation_v1 import start
from append_checkpoint_v1 import load
from event_cursor_v5 import EventCursor
import durable_submit_v4 as m
class Custody(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=pathlib.Path(self.tmp.name)/'journal';m.initialize(self.p,start('inert-q10-session'));self.requests=[]
 def invoke(self,reply=None,command=True):
  def exchange(session,q,timeout):
   self.requests.append(q)
   if reply is not None:return reply
   c=EventCursor();c.append({'event':'command','command':dict(q['command'],transport_request_id=q['request_id'])});c.append({'event':'rejected','reason':'unsupported text'})
   return c.read_until(q['after'],q['events'],timeout=0,action_id=q['action_id'])
  request={'timeout':1}
  if command:request['command']={'op':'submit','steps':[{'op':'text','text':'Value'}]}
  with self.assertRaisesRegex(ValueError,'unresolved reply status') as error:m.run(self.p,request,call=exchange)
  state=load(self.p);self.assertEqual(state['continuation']['cursor'],0);self.assertEqual(state['pending']['write_state'],'may_have_been_sent');self.assertFalse(state['pending']['echo_seen']);return error.exception
 def side(self):return pathlib.Path(str(self.p)+'.invalid-response.json')
 def test_actual_cursor_rejection_retained_no_replay(self):
  self.invoke();r=json.loads(self.side().read_text());self.assertEqual(r['response']['status'],'unattributed_rejection');self.assertEqual(len(r['response']['records']),2);self.assertFalse(r['replay_allowed']);self.assertEqual(r['authority'],'none');self.assertEqual(len(self.requests),1)
  raw=json.dumps(r['response'],sort_keys=True,separators=(',',':'),allow_nan=False).encode();self.assertEqual(hashlib.sha256(raw).hexdigest(),r['response_sha256'])
 def test_oversize_explicit_omission(self):
  self.invoke({'status':'bad','records':[],'payload':'x'*1048577});r=json.loads(self.side().read_text());self.assertFalse(r['response_retained']);self.assertNotIn('response',r);self.assertLess(self.side().stat().st_size,2097152)
 def test_first_receipt_preserved_read_only(self):
  self.invoke();before=self.side().read_bytes();error=self.invoke({'status':'bad','records':[]},False);self.assertEqual(before,self.side().read_bytes());self.assertNotIn('command',self.requests[-1]);self.assertTrue(any('FileExistsError' in n for n in error.__notes__))
 def test_write_failure_keeps_primary(self):
  self.side().mkdir();error=self.invoke();self.assertTrue(any('custody failed' in n for n in error.__notes__))
 def test_non_json_keeps_primary(self):
  error=self.invoke({'status':'bad','records':[],'payload':object()});self.assertFalse(self.side().exists());self.assertTrue(any('TypeError' in n for n in error.__notes__))
 def test_valid_reply_creates_no_diagnostic(self):
  result=m.run(self.p,{'timeout':0},call=lambda *a,**k:{'status':'timeout','records':[],'cursor':0});self.assertIsNone(result['state']['pending']);self.assertFalse(self.side().exists())
if __name__=='__main__':unittest.main()
