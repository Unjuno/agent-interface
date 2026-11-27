"""Response/retirement ordering without real GUI or process allocation."""
import tempfile
import threading
import unittest
from unittest.mock import Mock,patch
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner

class PausedResponse(dict):
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.entered=threading.Event();self.resume=threading.Event()
 def get(self,key,default=None):
  if key=='snapshot':
   self.entered.set()
   if not self.resume.wait(3):raise RuntimeError('test barrier expired')
  return super().get(key,default)

class Process:
 def __init__(self):self.alive=True;self.exitcode=None;self.pid=42
 def is_alive(self):return self.alive
 def terminate(self):self.alive=False;self.exitcode=-15
 def join(self,timeout=None):pass

def make_owner(root):
 owner=OwnedGuardedSessionOwner({'app':20},root);owner._process=Process();owner.state='open'
 owner._cleanup_retained_calc_process_group=Mock(return_value=None)
 return owner

class RetirementFenceTests(unittest.TestCase):
 def test_retirement_before_response_commit_rejects_stale_normal_reply(self):
  with tempfile.TemporaryDirectory() as root:
   owner=make_owner(root);owner._owner_input_obligations={'keys':{'a':38},'buttons':[]}
   response=PausedResponse(ok=True,result={'status':'success'},snapshot={'state':'open','error':None,'owner_input_obligations':{'keys':{},'buttons':[]}})
   owner._rpc=Mock();owner._rpc.recv.return_value=response;out=[]
   def invoke():
    try:out.append(owner._call('observe'))
    except Exception as error:out.append(error)
   thread=threading.Thread(target=invoke);thread.start();self.assertTrue(response.entered.wait(2))
   retirement=owner.retire('test retirement');self.assertTrue(retirement['retired'])
   response.resume.set();thread.join(3);self.assertFalse(thread.is_alive())
   self.assertIsInstance(out[0],RuntimeError);self.assertEqual(owner.state,'failed');self.assertTrue(owner.review_required)
   self.assertEqual(owner._owner_input_obligations,{'keys':{'a':38},'buttons':[]})
 def test_response_committed_before_retirement_still_returns(self):
  with tempfile.TemporaryDirectory() as root:
   owner=make_owner(root);owner._rpc=Mock();owner._rpc.recv.return_value={'ok':True,'result':{'status':'success'},'snapshot':{'state':'open'}}
   self.assertEqual(owner._call('observe'),{'status':'success'});self.assertTrue(owner.retire('after response')['retired'])
 def test_retire_before_start_keeps_unopened_owner_available(self):
  with tempfile.TemporaryDirectory() as root:
   owner=OwnedGuardedSessionOwner({'app':20},root)
   self.assertFalse(owner.retire('no child')['retired'])
   self.assertEqual(owner._lifecycle_version(),0)
 def test_rejected_reply_marks_unknown_when_termination_fails(self):
  class FailingProcess(Process):
   def terminate(self):raise OSError('termination failed')
  with tempfile.TemporaryDirectory() as root:
   owner=make_owner(root);owner._process=FailingProcess()
   response=PausedResponse(ok=True,result={'status':'success'},snapshot={'state':'open'})
   owner._rpc=Mock();owner._rpc.recv.return_value=response;out=[]
   def invoke():
    try:out.append(owner._call('observe'))
    except Exception as error:out.append(error)
   thread=threading.Thread(target=invoke);thread.start();self.assertTrue(response.entered.wait(2))
   with self.assertRaises(OSError):owner.retire('termination failure')
   response.resume.set();thread.join(3);self.assertFalse(thread.is_alive())
   self.assertIsInstance(out[0],RuntimeError)
   snapshot=owner.snapshot();self.assertTrue(snapshot['review_required'])
   self.assertEqual(snapshot['cleanup_status'],'UNKNOWN')
if __name__=='__main__':unittest.main()
