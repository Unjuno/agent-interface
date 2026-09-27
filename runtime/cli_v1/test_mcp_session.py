import asyncio
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.mcp_session import MCPSessionOwner


class OwnedMCPTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self):
        backend = Mock()
        backend.observe_read_only.return_value = {'sha256': 'fixture'}
        backend.release_all.return_value = {'verified': True, 'keys_down': [], 'buttons_down': []}
        session = SimpleNamespace(backend=backend, recovery_required=False)
        def dispatch(program, **kwargs):
            if session.recovery_required:
                return {'status': 'refused', 'error': 'INPUT_RECOVERY_REQUIRED'}
            session.recovery_required = True
            return {'status': 'release_unverified', 'recovery_required': True}
        session.dispatch = Mock(side_effect=dispatch)
        return session

    def row(self, reply):
        return json.loads(reply.content[0].text)

    def selection(self):
        return patch('runtime.cli_v1.mcp_session.select_backend',
                     return_value=SimpleNamespace(available=True, backend_id='x11-v1'))

    async def test_one_connection_preserves_recovery_across_observation_and_closes_once(self):
        session = self.fixture()
        with tempfile.TemporaryDirectory() as td, self.selection(), patch(
                'runtime.cli_v1.mcp_session.open_session', return_value=session) as opened:
            server = create_server({'fixture':123}, td, session_mode='persistent-x11')
            args={'target':'fixture','region':[0,0,1,1],'frame':'window_client'}
            a=self.row(await server.call_tool('interface_observe',args))
            await server.call_tool('interface_dispatch', {'program':{},'current_observation_seq':1,'current_binding_revision':1})
            b=self.row(await server.call_tool('interface_observe',args))
            c=self.row(await server.call_tool('interface_dispatch', {'program':{},'current_observation_seq':2,'current_binding_revision':2}))
            report=json.loads(Path(c['call_directory'],'report.json').read_text())
            self.assertEqual(report['result']['error'],'INPUT_RECOVERY_REQUIRED')
            self.assertEqual(a['session']['session_id'],b['session']['session_id'])
            self.assertTrue(b['session']['recovery_required'])
            session.backend.close.assert_not_called()
            closed=self.row(await server.call_tool('interface_close',{}))
            self.assertEqual(closed['status'],'closed')
            await server.call_tool('interface_close',{})
            blocked=self.row(await server.call_tool('interface_observe',args))
            self.assertEqual(blocked['status'],'session_closed')
            await server.call_tool('interface_results',{'call_id':a['call_id']})
            opened.assert_called_once()
            session.backend.close.assert_called_once()
            session.backend.release_all.assert_called_once()

    async def test_request_failure_does_not_open_connection(self):
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_session.open_session') as opened:
            server=create_server({'fixture':123},td,session_mode='persistent-x11')
            with patch('runtime.cli_v1.mcp_server._write_json',side_effect=OSError('disk full')):
                reply=self.row(await server.call_tool('interface_observe',{'target':'fixture','region':[0,0,1,1],'frame':'window_client'}))
            self.assertEqual(reply['error'],'REQUEST_PERSISTENCE_FAILED')
            opened.assert_not_called()

    async def test_failed_initialization_never_reopens(self):
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',side_effect=OSError('offline')) as opened:
            owner=MCPSessionOwner({'fixture':123})
            with self.assertRaises(OSError): owner.get()
            with self.assertRaises(RuntimeError): owner.get()
            opened.assert_called_once()
            self.assertEqual(owner.snapshot()['state'],'failed')
            owner.close()
            with self.assertRaises(RuntimeError): owner.get()

    async def test_close_failure_is_retained_without_second_release_or_close(self):
        session=self.fixture()
        session.backend.release_all.side_effect=OSError('release failed')
        session.backend.close.side_effect=OSError('close failed')
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session):
            owner=MCPSessionOwner({'fixture':123});owner.get();owner.dispatch_attempted=True
            first=owner.close();second=owner.close()
            self.assertEqual(first,second)
            self.assertEqual(first['status'],'cleanup_failed')
            self.assertIn('release_error',first);self.assertIn('close_error',first)
            session.backend.release_all.assert_called_once();session.backend.close.assert_called_once()

    async def test_cancelled_transport_waits_for_worker_before_shutdown_close(self):
        session=self.fixture();entered=threading.Event();release=threading.Event()
        def reader(*args):
            entered.set()
            if not release.wait(5): raise RuntimeError('test worker deadline')
            session.backend.close.assert_not_called()
            return {'sha256':'fixture'}
        session.backend.observe_read_only.side_effect=reader
        with tempfile.TemporaryDirectory() as td, self.selection(), patch(
                'runtime.cli_v1.mcp_session.open_session',return_value=session) as opened:
            server=create_server({'fixture':123},td,session_mode='persistent-x11')
            async with server.settings.lifespan(server):
                task=asyncio.create_task(server.call_tool('interface_observe',{'target':'fixture','region':[0,0,1,1],'frame':'window_client'}))
                self.assertTrue(await asyncio.to_thread(entered.wait,2))
                busy=self.row(await server.call_tool('interface_close',{}))
                self.assertEqual(busy['status'],'busy')
                task.cancel()
                with self.assertRaises(asyncio.CancelledError): await task
                asyncio.get_running_loop().call_later(.05,release.set)
            opened.assert_called_once();session.backend.close.assert_called_once()
            session.backend.release_all.assert_not_called()
            self.assertEqual(len(list(Path(td).glob('*/report.json'))),1)
            report=json.loads(next(Path(td).glob('session-*-close.json')).read_text())
            self.assertEqual(report['status'],'closed')


if __name__=='__main__': unittest.main()
