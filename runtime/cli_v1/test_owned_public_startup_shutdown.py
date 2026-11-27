import asyncio,json,multiprocessing,multiprocessing.process,tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import metadata

def _marker_owner_factory(targets, directory, display_name, options):
 Path(directory, 'factory-entered').write_text('entered', encoding='utf-8')
 return _fake_owner_factory(targets, directory, display_name, options)

def _blocked_owner_factory(targets, directory, display_name, options):
 Path(directory, 'factory-entered').write_text('entered', encoding='utf-8')
 deadline=time.monotonic()+20
 while not Path(directory, 'factory-resume').exists():
  if time.monotonic()>=deadline:raise TimeoutError('factory gate')
  time.sleep(.01)
 Path(directory, 'factory-resumed').write_text('resumed', encoding='utf-8')
 return _fake_owner_factory(targets, directory, display_name, options)

class PublicStartupShutdownTests(unittest.IsolatedAsyncioTestCase):
 async def test_shutdown_retires_child_blocked_inside_owner_initialization(self):
  # The child has passed the shared cancellation check. This tests retirement,
  # not an atomic guarantee between that check and arbitrary initialization.
  with tempfile.TemporaryDirectory() as directory:
   captured=[];original_init=OwnedGuardedSessionOwner.__init__
   def capture(owner,*args,**kwargs):
    original_init(owner,*args,**kwargs);captured.append(owner)
   with patch.object(OwnedGuardedSessionOwner,'__init__',capture):
    server=create_server({'app':20},directory,session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,_guarded_owner_factory=_blocked_owner_factory)
   lifespan=server.settings.lifespan(server);await lifespan.__aenter__();call=None;exiting=None
   try:
    call=asyncio.create_task(server.call_tool('interface_guarded_observe',{}))
    deadline=time.monotonic()+5
    while not Path(directory,'factory-entered').exists() and time.monotonic()<deadline:
     await asyncio.sleep(.01)
    self.assertTrue(Path(directory,'factory-entered').exists())
    process=captured[0]._process or captured[0]._starting_process
    self.assertIsNotNone(process.pid)
    self.assertTrue(process.is_alive())
    exiting=asyncio.create_task(lifespan.__aexit__(None,None,None))
    await asyncio.wait_for(asyncio.shield(exiting),12)
    self.assertFalse(process.is_alive())
    receipt=json.loads((Path(directory)/('session-'+captured[0].session_id+'-close.json')).read_text())
    self.assertFalse(receipt['verified'])
    self.assertEqual(receipt['cleanup_status'],'UNKNOWN')
    Path(directory,'factory-resume').write_text('resume', encoding='utf-8')
    result=metadata(await asyncio.wait_for(asyncio.shield(call),10))
    self.assertNotEqual(result.get('status'),'observed',result)
    self.assertFalse(Path(directory,'factory-resumed').exists())
   finally:
    Path(directory,'factory-resume').write_text('cleanup', encoding='utf-8')
    if call is not None and not call.done():
     try:await asyncio.wait_for(asyncio.shield(call),10)
     except Exception:pass
    if exiting is None:await lifespan.__aexit__(None,None,None)
    elif not exiting.done():await asyncio.wait_for(asyncio.shield(exiting),12)
    for owner in captured:
     process=owner._process or owner._starting_process
     if process is not None and process.pid is not None:
      if process.is_alive():process.kill()
      await asyncio.to_thread(process.join,3)
      self.assertFalse(process.is_alive())

 async def test_pre_pid_shutdown_can_be_followed_by_late_process_creation(self):
  # Counterexample: a parent-side cancellation flag cannot interrupt a start()
  # already entered before a PID exists. This does not grant input authority.
  with tempfile.TemporaryDirectory() as directory:
   entered=threading.Event();resume=threading.Event();shutdown_returned=threading.Event()
   spawned=[];late=[];original_start=multiprocessing.process.BaseProcess.start
   def gated_start(process):
    entered.set()
    if not resume.wait(20):raise TimeoutError('pre-pid gate')
    original_start(process);spawned.append(process);late.append(shutdown_returned.is_set())
   server=create_server({'app':20},directory,session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,_guarded_owner_factory=_marker_owner_factory)
   lifespan=server.settings.lifespan(server);await lifespan.__aenter__();call=None;exiting=None
   try:
    with patch.object(multiprocessing.process.BaseProcess,'start',gated_start):
     call=asyncio.create_task(server.call_tool('interface_guarded_observe',{}))
     self.assertTrue(await asyncio.to_thread(entered.wait,3))
     exiting=asyncio.create_task(lifespan.__aexit__(None,None,None))
     await asyncio.wait_for(asyncio.shield(exiting),12)
     shutdown_returned.set()
     resume.set()
     result=metadata(await asyncio.wait_for(asyncio.shield(call),10))
     self.assertEqual(late,[True])
     self.assertNotEqual(result.get('status'),'observed',result)
     self.assertEqual(list(Path(directory).rglob('factory-entered')), [],
                      'late child must not enter owner factory after shutdown')
   finally:
    resume.set()
    if call is not None and not call.done():
     try:await asyncio.wait_for(asyncio.shield(call),10)
     except Exception:pass
    if exiting is None:await lifespan.__aexit__(None,None,None)
    elif not exiting.done():await asyncio.wait_for(asyncio.shield(exiting),12)
    for process in spawned:
     if process.is_alive():process.kill()
     await asyncio.to_thread(process.join,3)
     self.assertFalse(process.is_alive())

 async def test_observe_does_not_complete_after_shutdown_during_start(self):
  with tempfile.TemporaryDirectory() as directory:
   captured=[]; original_init=OwnedGuardedSessionOwner.__init__
   entered=threading.Event();resume=threading.Event();spawned=[]
   def capture(owner,*args,**kwargs):
    original_init(owner,*args,**kwargs);captured.append(owner)
   with patch.object(OwnedGuardedSessionOwner,'__init__',capture):
    server=create_server({'app':20},directory,session_mode='guarded-x11',guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
   original_start=multiprocessing.process.BaseProcess.start
   def gated_start(process):
    original_start(process);spawned.append(process);entered.set()
    if not resume.wait(20):raise TimeoutError('startup gate')
   lifespan=server.settings.lifespan(server);await lifespan.__aenter__();call=None;exiting=None
   try:
    with patch.object(multiprocessing.process.BaseProcess,'start',gated_start):
     call=asyncio.create_task(server.call_tool('interface_guarded_observe',{}))
     self.assertTrue(await asyncio.to_thread(entered.wait,3))
     exiting=asyncio.create_task(lifespan.__aexit__(None,None,None))
     await asyncio.wait_for(asyncio.shield(exiting),12)
     self.assertFalse(call.done())
     # A started child with a published process handle must be retired
     # before shutdown returns, even while the startup caller is gated.
     self.assertFalse(spawned[0].is_alive())
     receipt=json.loads((Path(directory)/('session-'+captured[0].session_id+'-close.json')).read_text())
     self.assertIs(receipt.get('verified'),False)
     self.assertEqual(receipt.get('cleanup_status'),'UNKNOWN')
     self.assertIs(receipt.get('replay_allowed'),False)
     resume.set()
     result=metadata(await asyncio.wait_for(asyncio.shield(call),5))
     self.assertNotEqual(result.get('status'),'observed',result)
     self.assertFalse(captured[0]._process.is_alive())
   finally:
    resume.set()
    if call is not None:
     try:await asyncio.wait_for(asyncio.shield(call),5)
     except Exception:pass
    if exiting is None:await lifespan.__aexit__(None,None,None)
    elif not exiting.done():await asyncio.wait_for(asyncio.shield(exiting),12)
    for process in spawned:
     if process.is_alive():process.kill()
     await asyncio.to_thread(process.join,3)
     self.assertFalse(process.is_alive())
if __name__=='__main__':unittest.main()
