import threading,time,unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_bounded_idle_owner_experiment import fake_process_owner

def make_owner():
 owner=OwnedGuardedSessionOwner.__new__(OwnedGuardedSessionOwner)
 owner._idle_quarantine_lock=threading.RLock();owner._rpc_lock=threading.Lock()
 owner._idle_rpc_quarantined=False;owner._idle_rpc_inflight=False;owner._idle_observation_used=False
 owner._idle_cancel_calls_inflight=0;owner._cancel_calls_inflight=0;owner._idle_closing=False
 owner._process=object();owner.state='open';owner._execution_unknown=False;owner.review_required=False
 owner._cancel_idle_without_cleanup=Mock(return_value={'route':'idle'})
 owner._cancel_guarded_normal=Mock(return_value={'route':'ordinary'})
 return owner

class Exclusivity(unittest.TestCase):
 def test_idle_refused_while_normal_rpc_active_and_cancel_uses_normal_route(self):
  owner=make_owner();entered=threading.Event();resume=threading.Event()
  def normal(method,args):
   entered.set();resume.wait(2)
  owner._request_locked=normal
  worker=threading.Thread(target=lambda:owner._call('invoke_guarded'));worker.start()
  try:
   self.assertTrue(entered.wait(1))
   with self.assertRaisesRegex(RuntimeError,'RPC.*in.flight'):
    owner.observe_idle_until(deadline_ns=time.monotonic_ns()+250_000_000,cancel_token='idle')
   self.assertEqual(owner.cancel_guarded('ordinary')['route'],'ordinary')
  finally:resume.set();worker.join(2)

 def test_normal_rpc_refused_while_idle_reserved(self):
  owner=make_owner();owner._idle_rpc_inflight=True;owner._request_locked=Mock()
  with self.assertRaisesRegex(RuntimeError,'idle.*in.flight'):owner._call('invoke_guarded')
  owner._request_locked.assert_not_called()

class OwnedProcessExclusivity(unittest.TestCase):
 def test_real_owned_process_refuses_rpc_while_idle_capture_is_blocked(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'block-capture').write_text('block')
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake-owned-idle',process_identity=True,query_worker=True,
                                  observation_worker=True,_owner_factory=fake_process_owner)
   results=[];errors=[];worker=None
   def observe():
    try:results.append(owner.observe_idle_until(deadline_ns=time.monotonic_ns()+3_000_000_000,cancel_token='idle-overlap'))
    except BaseException as error:errors.append(error)
   try:
    owner.get();worker=threading.Thread(target=observe);worker.start();deadline=time.monotonic()+2
    while not (root/'capture-entered').exists() and time.monotonic()<deadline:time.sleep(.005)
    self.assertTrue((root/'capture-entered').exists())
    with self.assertRaisesRegex(RuntimeError,'idle observation in flight'):
     owner.invoke_guarded('guarded_observe',{},root/'rejected')
    self.assertFalse((root/'rejected').exists())
    (root/'resume-capture').write_text('resume');worker.join(2)
    self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
    self.assertEqual(results[0]['status'],'observed')
    self.assertEqual(owner.close()['status'],'closed')
   finally:
    (root/'resume-capture').write_text('resume')
    if worker is not None:worker.join(3)
    owner.close()

class RetirementOverlap(unittest.TestCase):
 def test_cancel_reply_admitted_before_external_retirement_does_not_cleanup_later(self):
  class Process:
   def __init__(self):self.alive=True;self.exitcode=None
   def is_alive(self):return self.alive
   def terminate(self):self.alive=False;self.exitcode=-15
   def join(self,timeout):pass
  class Control:
   def send(self,request):pass
   def poll(self,timeout):return True
   def recv(self):return {'ok':True,'snapshot':{'state':'open','review_required':False},'result':{'status':'cancel_requested','release_confirmed':False,'late_server_request_possible':True}}
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake',process_identity=True,query_worker=True,observation_worker=True)
   owner._process=Process();owner._control=Control();owner.state='open';entered=threading.Event();resume=threading.Event();rows=[]
   def decision(result):entered.set();resume.wait(2);return True
   owner._cancel_requires_owner_retirement=decision
   owner._cleanup_after_owner_retirement=Mock(return_value=({'status':'disconnected'},{'status':'readback_verified'}))
   worker=threading.Thread(target=lambda:rows.append(owner.cancel_guarded('ordinary')));worker.start()
   try:
    self.assertTrue(entered.wait(1));self.assertTrue(owner.retire('external retirement')['retired'])
    resume.set();worker.join(2);self.assertFalse(worker.is_alive())
    self.assertEqual(rows[0]['status'],'cancel_unconfirmed');self.assertEqual(rows[0]['cleanup_status'],'UNKNOWN')
    self.assertFalse(rows[0]['release_confirmed']);self.assertFalse(rows[0]['replay_allowed'])
    owner._cleanup_after_owner_retirement.assert_not_called();self.assertEqual(owner.state,'failed')
   finally:resume.set();worker.join(2)

 def test_retired_owner_cannot_accept_stale_ordinary_cancel_snapshot(self):
  class Process:
   def __init__(self):self.alive=True;self.exitcode=None
   def is_alive(self):return self.alive
   def terminate(self):self.alive=False;self.exitcode=-15
   def join(self,timeout):pass
  class Control:
   def __init__(self):self.entered=threading.Event();self.resume=threading.Event()
   def send(self,request):pass
   def poll(self,timeout):self.entered.set();self.resume.wait(2);return True
   def recv(self):return {'ok':True,'snapshot':{'state':'open','review_required':False},'result':{'status':'not_active','input_dispatched':False,'release_confirmed':False}}
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake',process_identity=True,query_worker=True,observation_worker=True)
   owner._process=Process();control=Control();owner._control=control;owner.state='open';rows=[]
   worker=threading.Thread(target=lambda:rows.append(owner.cancel_guarded('ordinary')));worker.start()
   try:
    self.assertTrue(control.entered.wait(1));self.assertTrue(owner.retire('fixture retirement')['retired'])
    control.resume.set();worker.join(2);self.assertFalse(worker.is_alive())
    self.assertEqual(rows[0]['status'],'cancel_unconfirmed');self.assertEqual(rows[0]['cleanup_status'],'UNKNOWN')
    self.assertFalse(rows[0]['release_confirmed']);self.assertFalse(rows[0]['replay_allowed'])
    self.assertEqual(owner.state,'failed');self.assertTrue(owner.review_required);self.assertFalse(owner._process.is_alive())
   finally:control.resume.set();worker.join(2)

 def test_close_defers_during_ordinary_cancel_without_closing_supervisor(self):
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake',process_identity=True,query_worker=True,observation_worker=True)
   entered=threading.Event();resume=threading.Event();rows=[];supervisor=Mock();owner._cleanup_supervisor=supervisor
   def cancel_normal(*args,**kwargs):entered.set();resume.wait(2);return {'status':'cancel_unconfirmed'}
   owner._cancel_guarded_normal=cancel_normal
   worker=threading.Thread(target=lambda:owner.cancel_guarded('ordinary'));worker.start()
   try:
    self.assertTrue(entered.wait(1));row=owner.close();rows.append(row)
    self.assertEqual(row['status'],'cleanup_deferred');self.assertEqual(row['cleanup_status'],'UNKNOWN')
    self.assertFalse(row['release_confirmed']);supervisor.close.assert_not_called()
   finally:resume.set();worker.join(3)
   self.assertFalse(worker.is_alive())

 def test_cancel_refused_during_close_before_idle_ever_used(self):
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake',process_identity=True,query_worker=True,observation_worker=True)
   entered=threading.Event();resume=threading.Event()
   class Supervisor:
    def close(self):entered.set();resume.wait(2)
   owner._cleanup_supervisor=Supervisor();owner._cancel_guarded_normal=Mock(return_value={'status':'unsafe_route'})
   worker=threading.Thread(target=owner.close);worker.start()
   try:
    self.assertTrue(entered.wait(1));row=owner.cancel_guarded('ordinary')
    self.assertEqual(row['status'],'cancel_unconfirmed');self.assertEqual(row['cleanup_status'],'UNKNOWN')
    self.assertFalse(row['release_confirmed']);owner._cancel_guarded_normal.assert_not_called()
   finally:resume.set();worker.join(3)
   self.assertFalse(worker.is_alive())

 def test_retired_owner_cannot_publish_late_idle_response(self):
  class Process:
   def __init__(self):self.alive=True;self.exitcode=None
   def is_alive(self):return self.alive
   def terminate(self):self.alive=False;self.exitcode=-15
   def join(self,timeout):pass
  class Rpc:
   def __init__(self):self.entered=threading.Event();self.resume=threading.Event()
   def send(self,request):pass
   def recv(self):
    self.entered.set()
    if not self.resume.wait(2):raise RuntimeError('fixture timeout')
    return {'ok':True,'snapshot':{'state':'open','review_required':False},'result':{'status':'observed'}}
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake',process_identity=True,query_worker=True,observation_worker=True)
   owner._process=Process();owner._rpc=Rpc();owner.state='open';values=[];errors=[]
   def observe():
    try:values.append(owner.observe_idle_until(deadline_ns=time.monotonic_ns()+300_000_000,cancel_token='idle'))
    except Exception as error:errors.append(error)
   worker=threading.Thread(target=observe);worker.start()
   try:
    self.assertTrue(owner._rpc.entered.wait(1));self.assertTrue(owner.retire('fixture retirement')['retired'])
    owner._rpc.resume.set();worker.join(2)
    self.assertFalse(worker.is_alive());self.assertEqual(values,[]);self.assertEqual(len(errors),1)
    self.assertEqual(owner.state,'failed');self.assertTrue(owner.review_required)
    self.assertTrue(owner._idle_rpc_quarantined);self.assertFalse(owner._process.is_alive())
   finally:owner._rpc.resume.set();worker.join(2)

 def test_retirement_wakes_idle_waiter_without_waiting_for_deadline(self):
  class Process:
   def __init__(self):self.alive=True;self.exitcode=None
   def is_alive(self):return self.alive
   def terminate(self):self.alive=False;self.exitcode=-15
   def join(self,timeout):pass
  class Rpc:
   def __init__(self):self.entered=threading.Event();self.resume=threading.Event()
   def send(self,request):pass
   def recv(self):
    self.entered.set();self.resume.wait(3)
    return {'ok':True,'snapshot':{'state':'open','review_required':False},'result':{'status':'observed'}}
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake',process_identity=True,query_worker=True,observation_worker=True)
   owner._process=Process();owner._rpc=Rpc();owner.state='open';values=[];errors=[]
   def observe():
    try:values.append(owner.observe_idle_until(deadline_ns=time.monotonic_ns()+2_000_000_000,cancel_token='idle-wake'))
    except Exception as error:errors.append(error)
   worker=threading.Thread(target=observe);worker.start()
   try:
    self.assertTrue(owner._rpc.entered.wait(1));self.assertTrue(owner.retire('fixture retirement')['retired'])
    worker.join(.5);self.assertFalse(worker.is_alive(),'retired waiter slept until deadline')
    self.assertEqual(values,[]);self.assertEqual(len(errors),1);self.assertEqual(owner.state,'failed')
    self.assertTrue(owner.review_required);self.assertTrue(owner._idle_rpc_quarantined)
   finally:owner._rpc.resume.set();worker.join(3)

 def test_close_defers_while_woken_retirement_is_in_progress(self):
  class Process:
   def __init__(self):self.alive=True;self.exitcode=None;self.calls=0;self.entered=threading.Event();self.release=threading.Event()
   def is_alive(self):return self.alive
   def terminate(self):
    self.calls+=1;self.entered.set()
    if not self.release.wait(2):raise RuntimeError('fixture timeout')
    self.alive=False;self.exitcode=-15
   def join(self,timeout):pass
  class Rpc:
   def __init__(self):self.entered=threading.Event();self.release=threading.Event()
   def send(self,request):pass
   def recv(self):
    self.entered.set();self.release.wait(3)
    return {'ok':True,'snapshot':{'state':'open','review_required':False},'result':{'status':'observed'}}
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake',process_identity=True,query_worker=True,observation_worker=True)
   process=Process();rpc=Rpc();owner._process=process;owner._rpc=rpc;owner.state='open';errors=[]
   def observe():
    try:owner.observe_idle_until(deadline_ns=time.monotonic_ns()+2_000_000_000,cancel_token='idle-close')
    except Exception as error:errors.append(error)
   reader=threading.Thread(target=observe);retirer=threading.Thread(target=lambda:owner.retire('fixture retirement'));closes=[]
   closer=threading.Thread(target=lambda:closes.append(owner.close()))
   try:
    reader.start();self.assertTrue(rpc.entered.wait(1));retirer.start();self.assertTrue(process.entered.wait(1));reader.join(.5)
    self.assertFalse(reader.is_alive());self.assertEqual(len(errors),1)
    closer.start();closer.join(.5);self.assertFalse(closer.is_alive(),'close waited on in-progress retirement')
    row=closes[0];self.assertEqual(row['status'],'cleanup_deferred');self.assertFalse(row['release_confirmed'])
    self.assertEqual(process.calls,1);self.assertIsNone(owner.close_report)
   finally:
    process.release.set();rpc.release.set();reader.join(3);retirer.join(3)
    if closer.ident is not None:closer.join(3)
   self.assertFalse(retirer.is_alive());row=owner.close()
   self.assertEqual(process.calls,1);self.assertEqual(row['cleanup_status'],'UNKNOWN')

 def test_cancel_reports_in_progress_retirement_without_cleanup_replay(self):
  class Process:
   def __init__(self):self.alive=True;self.exitcode=None;self.entered=threading.Event();self.release=threading.Event();self.calls=0
   def is_alive(self):return self.alive
   def terminate(self):
    self.calls+=1;self.entered.set()
    if not self.release.wait(3):raise RuntimeError('fixture timeout')
    self.alive=False;self.exitcode=-15
   def join(self,timeout):pass
  class Control:
   def __init__(self):self.entered=threading.Event();self.release=threading.Event()
   def send(self,request):pass
   def poll(self,timeout):self.entered.set();self.release.wait(2);return False
  with tempfile.TemporaryDirectory() as td:
   owner=OwnedGuardedSessionOwner({'app':20},td,':fake',process_identity=True,query_worker=True,observation_worker=True,prestarted_cancel_supervisor=True)
   process=Process();control=Control();owner._process=process;owner._control=control;owner.state='open';owner._cleanup_supervisor=Mock();result={}
   canceller=threading.Thread(target=lambda:result.setdefault('cancel',owner.cancel_guarded('ordinary')))
   retirer=threading.Thread(target=lambda:result.setdefault('retire',owner.retire('independent retirement')))
   try:
    canceller.start();self.assertTrue(control.entered.wait(1));retirer.start();self.assertTrue(process.entered.wait(1))
    control.release.set();canceller.join(1);self.assertFalse(canceller.is_alive());row=result['cancel']
    self.assertEqual(row['status'],'cancel_unconfirmed');self.assertEqual(row['cleanup_status'],'UNKNOWN')
    self.assertTrue(row['owner_retirement_in_progress_at_attempt']);self.assertEqual(row['owner_release_attempt']['reason'],'retirement_in_progress_at_attempt')
    self.assertFalse(row['release_confirmed']);self.assertFalse(row['replay_allowed']);self.assertEqual(process.calls,1)
   finally:
    control.release.set();process.release.set();canceller.join(3)
    if retirer.ident is not None:retirer.join(3)
   self.assertTrue(result['retire']['retired']);owner._cleanup_supervisor.run.assert_not_called()

if __name__=='__main__':unittest.main()
