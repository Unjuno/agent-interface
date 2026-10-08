import importlib.util,pathlib,sys,tempfile,unittest,copy
from unittest.mock import patch
SOURCE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
import durable_submit_v4 as durable
from received_continuation_v1 import start
from append_checkpoint_v1 import load
import integrated_efficiency_client_v1 as m
class PendingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.c=m.RuntimeClient(pathlib.Path(self.tmp.name)/'client',1);self.c.journal=pathlib.Path(self.tmp.name)/'journal';durable.initialize(self.c.journal,start('inert-session'));self.requests=[];self.index=0;self.action=None
 def exchange(self,session,q,timeout):
  self.requests.append(copy.deepcopy(q));rows=[]
  if 'command' in q:
   command=dict(q['command'],transport_request_id=q['request_id']);self.action=command['id'];rows=[{'event':'command','command':command},{'event':'accepted','id':self.action},{'event':'observation','sequence':1}];status='batch_limit'
  elif self.mode=='complete':rows=[{'event':'terminal','id':self.action,'status':'completed','release':{'verified':True,'keys_down':[],'buttons_down':[]}}];status='boundary'
  elif self.mode=='error':raise ConnectionError('inert transport gone')
  else:status='timeout'
  self.index+=len(rows);return {'status':status,'records':rows,'cursor':self.index}
 def invoke(self):
  return self.c.call({'command':{'op':'submit','steps':[{'op':'observe'}]},'timeout':1})
 def runner(self,path,spec):return durable.run(path,spec,call=self.exchange)
 def test_batch_then_terminal_no_resend(self):
  self.mode='complete'
  with patch.object(m,'run',self.runner):result,_,_=self.invoke()
  self.assertEqual(len(self.requests),2);self.assertNotIn('command',self.requests[1]);self.assertEqual(self.requests[1]['action_id'],self.action);self.assertEqual(self.requests[1]['after'],3);self.assertIsNone(load(self.c.journal)['pending']);self.assertEqual([x['event'] for x in result['records']],['command','accepted','observation','terminal'])
 def test_submit_preserves_initial_observation(self):
  self.mode='complete'
  with patch.object(m,'run',self.runner),patch.object(self.c,'clock',return_value={'sequence':1,'runtime_ns':1}):row=self.c.submit('probe',[{'op':'observe'}])
  self.assertEqual(row['terminal']['status'],'completed');self.assertEqual(row['observations'],[{'event':'observation','sequence':1}]);self.assertEqual(len(self.c.programs),1);self.assertEqual(sum('command' in q for q in self.requests),1)
 def test_invalid_timeout_before_send(self):
  self.mode='complete'
  for timeout in [float('nan'),float('inf'),-1,31,True]:
   with patch.object(m,'run',self.runner),self.assertRaises(ValueError):self.c.call({'command':{'op':'submit','steps':[]},'timeout':timeout})
  self.assertEqual(self.requests,[]);self.assertIsNone(load(self.c.journal)['pending'])
 def test_read_count_bound_keeps_pending(self):
  self.mode='pending'
  with patch.object(m,'run',self.runner),patch.object(m.time,'monotonic',return_value=0):
   with self.assertRaises(TimeoutError):self.invoke()
  self.assertLessEqual(len(self.requests),33);self.assertEqual(sum('command' in q for q in self.requests),1);self.assertIsNotNone(load(self.c.journal)['pending'])
 def test_transport_failure_no_resend(self):
  self.mode='error'
  with patch.object(m,'run',self.runner):
   with self.assertRaisesRegex(ConnectionError,'inert transport gone'):self.invoke()
  self.assertEqual(len(self.requests),2);self.assertEqual(sum('command' in q for q in self.requests),1);self.assertTrue(load(self.c.journal)['pending']['accepted'])
 def test_deadline_stops_before_read(self):
  self.mode='pending'
  with patch.object(m,'run',self.runner),patch.object(m.time,'monotonic',side_effect=[0,2]):
   with self.assertRaises(TimeoutError):self.invoke()
  self.assertEqual(len(self.requests),1);self.assertIsNotNone(load(self.c.journal)['pending'])
if __name__=='__main__':unittest.main(verbosity=2)
