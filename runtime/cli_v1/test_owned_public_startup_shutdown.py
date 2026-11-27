import asyncio,json,multiprocessing,multiprocessing.process,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import metadata

class PublicStartupShutdownTests(unittest.IsolatedAsyncioTestCase):
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
