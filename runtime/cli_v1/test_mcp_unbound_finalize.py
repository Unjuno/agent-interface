import asyncio,json,os,signal,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
import runtime.cli_v1.mcp_server as mcp_server
from runtime.cli_v1.owned_target_session import OwnedTargetGuardedSessionOwner
from runtime.cli_v1.mcp_server import create_server
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess

def fail_factory(targets,directory,display_name,options):raise RuntimeError('fixture startup failure')
def metadata(result):return json.loads(result.content[0].text)

@unittest.skipUnless(sys.platform.startswith('linux') and callable(getattr(os,'pidfd_open',None))
    and callable(getattr(signal,'pidfd_send_signal',None)), 'Linux pidfd required')
class EndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_owner_then_explicit_finalize(self):
        target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        server=None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                server=create_server({'app':1234},Path(tmp)/'mcp',display_name=':91',session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,
                    _guarded_owned_target_process=target,_guarded_prestarted_target_identity=True,_guarded_owner_factory=fail_factory)
                early=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertEqual(early['status'],'refused');self.assertFalse(early['operation_invoked'])
                observation=metadata(await server.call_tool('interface_guarded_observe',{}))
                self.assertNotEqual(observation['status'],'observed')
                signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=3)
                closed=metadata(await server.call_tool('interface_close',{}))
                self.assertEqual(closed.get('cleanup_status'),'UNKNOWN')
                done=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertEqual(done['status'],'handle_closed',done)
                self.assertEqual(done['cleanup_status'],'UNKNOWN');self.assertFalse(done['replay_allowed']);self.assertIsNone(done['task_success'])
                self.assertTrue(target._closed)
        finally:
            if server is not None:
                try:await server.call_tool('interface_close',{})
                except BaseException:pass
            if target.running:signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=2)
            try:target.close(_custody=target._session_custody)
            except BaseException:pass
    async def test_live_target_refused_then_exited_target_finalized(self):
        target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        server=None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                server=create_server({'app':1234},Path(tmp)/'mcp',display_name=':91',session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,
                    _guarded_owned_target_process=target,_guarded_prestarted_target_identity=True,_guarded_owner_factory=fail_factory)
                await server.call_tool('interface_guarded_observe',{})
                closed=metadata(await server.call_tool('interface_close',{}));self.assertEqual(closed.get('cleanup_status'),'UNKNOWN')
                first=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertEqual(first['status'],'refused',first);self.assertEqual(first['reason'],'target_still_alive')
                self.assertTrue(target.running)
                signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=3)
                second=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertEqual(second['status'],'handle_closed',second);self.assertEqual(second['cleanup_status'],'UNKNOWN')
                self.assertFalse(second['replay_allowed']);self.assertIsNone(second['task_success']);self.assertTrue(target._closed)
        finally:
            if server is not None:
                try:await server.call_tool('interface_close',{})
                except BaseException:pass
            if target.running:signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=2)
            try:target.close(_custody=target._session_custody)
            except BaseException:pass
    async def test_request_persistence_failure_does_not_close_handle(self):
        target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        server=None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                server=create_server({'app':1234},Path(tmp)/'mcp',display_name=':91',session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,
                    _guarded_owned_target_process=target,_guarded_prestarted_target_identity=True,_guarded_owner_factory=fail_factory)
                await server.call_tool('interface_guarded_observe',{})
                signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=3)
                await server.call_tool('interface_close',{})
                write=mcp_server._write_json
                def fault(path,value):
                    if Path(path).name=='request.json':raise OSError('injected request persistence failure')
                    return write(path,value)
                with patch('runtime.cli_v1.mcp_server._write_json',side_effect=fault):
                    refused=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertEqual(refused['error'],'REQUEST_PERSISTENCE_FAILED',refused)
                self.assertFalse(refused['operation_invoked']);self.assertFalse(target._closed)
                done=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertEqual(done['status'],'handle_closed',done);self.assertTrue(target._closed)
        finally:
            if server is not None:
                try:await server.call_tool('interface_close',{})
                except BaseException:pass
            if target.running:signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=2)
            try:target.close(_custody=target._session_custody)
            except BaseException:pass
    async def test_concurrent_finalization_is_refused(self):
        target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        server=None;resume=threading.Event();entered=threading.Event();task=None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                server=create_server({'app':1234},Path(tmp)/'mcp',display_name=':91',session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,
                    _guarded_owned_target_process=target,_guarded_prestarted_target_identity=True,_guarded_owner_factory=fail_factory)
                await server.call_tool('interface_guarded_observe',{})
                signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=3)
                await server.call_tool('interface_close',{})
                original=OwnedTargetGuardedSessionOwner.finalize_exited_unbound_target
                def gated(owner):
                    entered.set()
                    if not resume.wait(3):raise TimeoutError('fixture timeout')
                    return original(owner)
                with patch.object(OwnedTargetGuardedSessionOwner,'finalize_exited_unbound_target',gated):
                    task=asyncio.create_task(server.call_tool('interface_guarded_finalize_unbound_target',{}))
                    self.assertTrue(await asyncio.to_thread(entered.wait,2))
                    duplicate=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                    self.assertIn(duplicate['status'],('busy','refused'));self.assertFalse(target._closed)
                    resume.set();done=metadata(await asyncio.wait_for(task,4));self.assertEqual(done['status'],'handle_closed',done)
        finally:
            resume.set()
            if task is not None and not task.done():
                try:await asyncio.wait_for(task,4)
                except BaseException:pass
            if server is not None:
                try:await server.call_tool('interface_close',{})
                except BaseException:pass
            if target.running:signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=2)
            try:target.close(_custody=target._session_custody)
            except BaseException:pass
    async def test_report_persistence_failure_retains_closed_handle_without_replay(self):
        target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        server=None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                server=create_server({'app':1234},Path(tmp)/'mcp',display_name=':91',session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,
                    _guarded_owned_target_process=target,_guarded_prestarted_target_identity=True,_guarded_owner_factory=fail_factory)
                await server.call_tool('interface_guarded_observe',{})
                signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=3)
                await server.call_tool('interface_close',{})
                write=mcp_server._write_json
                def fault(path,value):
                    if Path(path).name=='report.json':raise OSError('injected report persistence failure')
                    return write(path,value)
                with patch('runtime.cli_v1.mcp_server._write_json',side_effect=fault):
                    row=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertTrue(target._closed);self.assertIn('persistence_error',row)
                self.assertFalse(row['replay_allowed']);self.assertIsNone(row['task_success'])
                again=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertEqual(again['status'],'handle_closed',again);self.assertTrue(target._closed)
        finally:
            if server is not None:
                try:await server.call_tool('interface_close',{})
                except BaseException:pass
            if target.running:signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=2)
            try:target.close(_custody=target._session_custody)
            except BaseException:pass
    async def test_cancelled_wait_retains_finalization_and_receipt(self):
        target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        server=None;resume=threading.Event();entered=threading.Event();task=None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'mcp'
                server=create_server({'app':1234},root,display_name=':91',session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,
                    _guarded_owned_target_process=target,_guarded_prestarted_target_identity=True,_guarded_owner_factory=fail_factory)
                await server.call_tool('interface_guarded_observe',{})
                signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=3)
                closed=metadata(await server.call_tool('interface_close',{}));self.assertEqual(closed.get('cleanup_status'),'UNKNOWN')
                original=OwnedTargetGuardedSessionOwner.finalize_exited_unbound_target
                def gated(owner):
                    entered.set()
                    if not resume.wait(4):raise TimeoutError('fixture timeout')
                    return original(owner)
                with patch.object(OwnedTargetGuardedSessionOwner,'finalize_exited_unbound_target',gated):
                    task=asyncio.create_task(server.call_tool('interface_guarded_finalize_unbound_target',{}))
                    self.assertTrue(await asyncio.to_thread(entered.wait,2))
                    listing=metadata(await server.call_tool('interface_results',{}))
                    matches=[item for item in listing['calls'] if item['operation']=='guarded_finalize_unbound_target']
                    self.assertEqual(len(matches),1);call_id=matches[0]['call_id']
                    task.cancel()
                    with self.assertRaises(asyncio.CancelledError):await task
                    duplicate=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                    self.assertIn(duplicate['status'],('busy','refused'));self.assertFalse(target._closed)
                    resume.set()
                    for _ in range(150):
                        row=metadata(await server.call_tool('interface_results',{'call_id':call_id}))
                        if row.get('status')!='pending':break
                        await asyncio.sleep(.01)
                    self.assertNotEqual(row.get('status'),'pending',row);self.assertTrue(target._closed)
                    report=json.loads((root/call_id/'report.json').read_text())
                    self.assertEqual(report['status'],'handle_closed',report);self.assertEqual(report['cleanup_status'],'UNKNOWN')
                    self.assertFalse(report['replay_allowed']);self.assertIsNone(report['task_success'])
        finally:
            resume.set()
            if task is not None and not task.done():
                try:await asyncio.wait_for(task,4)
                except BaseException:pass
            if server is not None:
                try:await server.call_tool('interface_close',{})
                except BaseException:pass
            if target.running:signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=2)
            try:target.close(_custody=target._session_custody)
            except BaseException:pass
    async def test_shutdown_refuses_new_finalization(self):
        target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        server=None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                server=create_server({'app':1234},Path(tmp)/'mcp',display_name=':91',session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,
                    _guarded_owned_target_process=target,_guarded_prestarted_target_identity=True,_guarded_owner_factory=fail_factory)
                async with server.settings.lifespan(server):
                    await server.call_tool('interface_guarded_observe',{})
                    signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=3)
                    closed=metadata(await server.call_tool('interface_close',{}));self.assertEqual(closed.get('cleanup_status'),'UNKNOWN')
                refused=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                self.assertEqual(refused['status'],'refused',refused);self.assertFalse(refused['operation_invoked'])
                self.assertFalse(target._closed)
        finally:
            if target.running:signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=2)
            try:target.close(_custody=target._session_custody)
            except BaseException:pass
    async def test_shutdown_waits_for_admitted_finalization(self):
        target=OwnedTargetProcess.launch([sys.executable,'-c','import time;time.sleep(20)'],disposable=True)
        server=None;manager=None;exit_task=None;work=None;entered=threading.Event();resume=threading.Event()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                server=create_server({'app':1234},Path(tmp)/'mcp',display_name=':91',session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,guarded_owned_process=True,
                    _guarded_owned_target_process=target,_guarded_prestarted_target_identity=True,_guarded_owner_factory=fail_factory)
                manager=server.settings.lifespan(server);await manager.__aenter__()
                await server.call_tool('interface_guarded_observe',{})
                signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=3)
                await server.call_tool('interface_close',{})
                original=OwnedTargetGuardedSessionOwner.finalize_exited_unbound_target
                def gated(owner):
                    entered.set()
                    if not resume.wait(4):raise TimeoutError('fixture timeout')
                    return original(owner)
                with patch.object(OwnedTargetGuardedSessionOwner,'finalize_exited_unbound_target',gated):
                    work=asyncio.create_task(server.call_tool('interface_guarded_finalize_unbound_target',{}))
                    self.assertTrue(await asyncio.to_thread(entered.wait,2))
                    exit_task=asyncio.create_task(manager.__aexit__(None,None,None));await asyncio.sleep(.1)
                    self.assertFalse(exit_task.done());self.assertFalse(target._closed)
                    refused=metadata(await server.call_tool('interface_guarded_finalize_unbound_target',{}))
                    self.assertEqual(refused['status'],'refused');self.assertFalse(refused['operation_invoked'])
                    resume.set();done=metadata(await asyncio.wait_for(work,4));self.assertEqual(done['status'],'handle_closed',done)
                    await asyncio.wait_for(exit_task,4);manager=None;self.assertTrue(target._closed)
        finally:
            resume.set()
            if work is not None and not work.done():
                try:await asyncio.wait_for(work,4)
                except BaseException:pass
            if exit_task is not None and not exit_task.done():
                try:await asyncio.wait_for(exit_task,4)
                except BaseException:pass
            elif manager is not None and exit_task is None:
                try:await manager.__aexit__(None,None,None)
                except BaseException:pass
            if target.running:signal.pidfd_send_signal(target._pidfd,signal.SIGKILL);target._process.wait(timeout=2)
            try:target.close(_custody=target._session_custody)
            except BaseException:pass
    async def test_endpoint_absent_for_unowned_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            server=create_server({'app':1234},Path(tmp)/'mcp')
            self.assertNotIn('interface_guarded_finalize_unbound_target',{tool.name for tool in await server.list_tools()})
if __name__=='__main__':unittest.main(verbosity=2)
