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
            c=self.row(await server.call_tool('interface_dispatch', {'program':{},'current_observation_seq':2,'current_binding_revision':1}))
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


    async def test_explicit_review_preserves_recovery_and_invalidates_old_binding(self):
        session=self.fixture();session.recovery_required=True
        session.backend.targets={'fixture':SimpleNamespace(id=123)}
        session.backend.d.create_resource_object.side_effect=lambda kind,wid: SimpleNamespace(id=wid)
        evidence={'window_id':456,'transient_chain':[456,123],'geometry':[1,2,30,40]}
        with tempfile.TemporaryDirectory() as td, self.selection(), patch(
                'runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',return_value=evidence):
            server=create_server({'fixture':123},td,session_mode='persistent-x11')
            inspection=self.row(await server.call_tool('interface_inspect_target',{'target':'fixture'}))
            self.assertEqual(session.backend.targets['fixture'].id,123)
            retained=self.row(await server.call_tool('interface_results',{'call_id':inspection['call_id']}))
            self.assertEqual(retained['review_id'],inspection['review_id'])
            self.assertFalse(retained['operation_invoked'])
            args={'target':'fixture','window_id':456,'review_id':inspection['review_id']}
            reviewed=self.row(await server.call_tool('interface_review_target',args))
            self.assertEqual(reviewed['binding_revision'],2)
            self.assertEqual(session.backend.targets['fixture'].id,456)
            self.assertTrue(session.recovery_required)
            session.backend.release_all.assert_not_called()
            session.backend.focus.assert_not_called()
            again=self.row(await server.call_tool('interface_review_target',args))
            self.assertEqual(again['status'],'needs_review')
            stale=self.row(await server.call_tool('interface_dispatch',{'program':{},'current_observation_seq':1,'current_binding_revision':1}))
            report=json.loads(Path(stale['call_directory'],'report.json').read_text())
            self.assertEqual(report['error'],'SESSION_BINDING_REVISION_MISMATCH')
            session.dispatch.assert_not_called()
            current=self.row(await server.call_tool('interface_dispatch',{'program':{},'current_observation_seq':2,'current_binding_revision':2}))
            report=json.loads(Path(current['call_directory'],'report.json').read_text())
            self.assertEqual(report['result']['error'],'INPUT_RECOVERY_REQUIRED')
            await server.call_tool('interface_close',{})

    async def test_changed_target_review_does_not_mutate_registry(self):
        session=self.fixture();session.backend.targets={'fixture':SimpleNamespace(id=123)}
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',side_effect=[
                    {'window_id':456,'geometry':[1,2,30,40]},
                    {'window_id':456,'geometry':[2,2,30,40]}]):
            owner=MCPSessionOwner({'fixture':123})
            inspected=owner.inspect_target('fixture')
            with self.assertRaisesRegex(ValueError,'changed'):
                owner.review_target('fixture',456,inspected['review_id'])
            self.assertEqual(owner.targets,{'fixture':123})
            self.assertEqual(owner.binding_revision,1)
            self.assertIsNone(owner.target_review)
            session.backend.d.create_resource_object.assert_not_called()
            owner.close()

    async def test_expired_target_review_requires_new_inspection(self):
        session=self.fixture()
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',return_value={'window_id':456}), patch(
                'runtime.cli_v1.mcp_session.time.monotonic_ns',side_effect=[0,30_000_000_001]):
            owner=MCPSessionOwner({'fixture':123})
            inspected=owner.inspect_target('fixture')
            with self.assertRaisesRegex(ValueError,'expired'):
                owner.review_target('fixture',456,inspected['review_id'])
            self.assertEqual(owner.targets,{'fixture':123})
            owner.close()

    async def test_inspection_image_is_delivered_once_and_retained_without_recapture(self):
        session=self.fixture()
        evidence={'window_id':456,'transient_chain':[456,123]}
        with tempfile.TemporaryDirectory() as td, self.selection(), patch(
                'runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',return_value=evidence) as inspect, patch(
                'runtime.cli_v1.mcp_server.present_result',return_value={
                    'image_status':'available','image':{'type':'image','mimeType':'image/png','data':'YWJj'}}):
            server=create_server({'fixture':123},td,session_mode='persistent-x11')
            reply=await server.call_tool('interface_inspect_target',{'target':'fixture','screen_region':[0,0,10,10]})
            row=self.row(reply)
            self.assertIn('review_id',row)
            self.assertNotIn('image',row)
            self.assertEqual([x.type for x in reply.content],['text','image'])
            self.assertFalse(row['input_dispatched'])
            self.assertEqual(row['session']['targets'],{'fixture':123})
            raw=json.loads(Path(row['call_directory'],'report.json').read_text())
            self.assertEqual(raw['observation_report']['status'],'returned')
            retained=await server.call_tool('interface_results',{'call_id':row['call_id'],'include_image':False})
            self.assertEqual([x.type for x in retained.content],['text'])
            self.assertEqual(self.row(retained)['image_delivery'],'omitted_by_request')
            self.assertEqual(inspect.call_count,2)
            session.backend.observe_read_only.assert_called_once_with('fixture','screen_physical_px',[0,0,10,10])
            session.backend.focus.assert_not_called()
            session.backend.release_all.assert_not_called()
            await server.call_tool('interface_close',{})

    async def test_capture_disagreement_retains_observation_but_no_review_id(self):
        session=self.fixture()
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',side_effect=[{'window_id':456},{'window_id':123}]):
            owner=MCPSessionOwner({'fixture':123})
            result=owner.inspect_target('fixture',screen_region=[0,0,10,10])
            self.assertEqual(result['error'],'TARGET_CHANGED_DURING_CAPTURE')
            self.assertEqual(result['observation_report']['status'],'returned')
            self.assertNotIn('review_id',result)
            self.assertIsNone(owner.target_review)
            self.assertEqual(owner.targets,{'fixture':123})
            owner.close()

    async def test_review_image_uses_new_binding_and_results_do_not_repeat_selection(self):
        session=self.fixture();session.backend.targets={'fixture':SimpleNamespace(id=123)}
        session.backend.d.create_resource_object.side_effect=lambda kind,wid: SimpleNamespace(id=wid)
        def read(*args):
            self.assertEqual(session.backend.targets['fixture'].id,456)
            return {'sha256':'fixture'}
        session.backend.observe_read_only.side_effect=read
        with tempfile.TemporaryDirectory() as td, self.selection(), patch(
                'runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',return_value={'window_id':456}), patch(
                'runtime.cli_v1.mcp_server.present_result',return_value={
                    'image_status':'available','image':{'type':'image','mimeType':'image/png','data':'YWJj'}}):
            server=create_server({'fixture':123},td,session_mode='persistent-x11')
            inspected=self.row(await server.call_tool('interface_inspect_target',{'target':'fixture'}))
            reply=await server.call_tool('interface_review_target',{
                'target':'fixture','window_id':456,'review_id':inspected['review_id'],
                'screen_region':[0,0,10,10]})
            row=self.row(reply)
            self.assertEqual(row['binding_revision'],2)
            self.assertEqual(row['capture_consistency'],'matched')
            self.assertEqual([x.type for x in reply.content],['text','image'])
            retained=self.row(await server.call_tool('interface_results',{'call_id':row['call_id'],'include_image':False}))
            self.assertEqual(retained['binding_revision'],2)
            self.assertFalse(retained['operation_invoked'])
            session.backend.observe_read_only.assert_called_once()
            session.backend.d.create_resource_object.assert_called_once()
            session.backend.focus.assert_not_called()
            await server.call_tool('interface_close',{})

    async def test_review_capture_failure_retains_committed_selection_and_consumes_token(self):
        session=self.fixture();session.backend.targets={'fixture':SimpleNamespace(id=123)}
        session.backend.d.create_resource_object.side_effect=lambda kind,wid: SimpleNamespace(id=wid)
        session.recovery_required=True
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',return_value={'window_id':456}):
            owner=MCPSessionOwner({'fixture':123})
            inspected=owner.inspect_target('fixture')
            row=owner.review_target('fixture',456,inspected['review_id'],screen_region=[0,0,0,10])
            self.assertEqual(row['status'],'target_reviewed')
            self.assertEqual(row['capture_consistency'],'unconfirmed')
            self.assertEqual(row['observation_report']['status'],'invalid_request')
            self.assertEqual(owner.targets,{'fixture':456})
            self.assertEqual(owner.binding_revision,2)
            self.assertTrue(session.recovery_required)
            with self.assertRaises(ValueError): owner.review_target('fixture',456,inspected['review_id'])
            session.backend.observe_read_only.assert_not_called()
            owner.close()

    async def test_review_capture_changed_metadata_does_not_rebind_or_hide_selection(self):
        session=self.fixture();session.backend.targets={'fixture':SimpleNamespace(id=123)}
        session.backend.d.create_resource_object.side_effect=lambda kind,wid: SimpleNamespace(id=wid)
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',side_effect=[
                    {'window_id':456},{'window_id':456},{'window_id':123}]):
            owner=MCPSessionOwner({'fixture':123})
            inspected=owner.inspect_target('fixture')
            row=owner.review_target('fixture',456,inspected['review_id'],screen_region=[0,0,10,10])
            self.assertEqual(row['capture_consistency'],'changed')
            self.assertEqual(row['status'],'target_reviewed')
            self.assertEqual(owner.binding_revision,2)
            self.assertEqual(owner.targets,{'fixture':456})
            session.backend.focus.assert_not_called()
            owner.close()

    async def test_invalid_capture_region_never_yields_review_id(self):
        session=self.fixture()
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',return_value={'window_id':456}):
            owner=MCPSessionOwner({'fixture':123})
            result=owner.inspect_target('fixture',screen_region=[0,0,0,10])
            self.assertEqual(result['error'],'TARGET_CAPTURE_FAILED')
            self.assertEqual(result['observation_report']['status'],'invalid_request')
            self.assertNotIn('review_id',result)
            self.assertIsNone(owner.target_review)
            session.backend.observe_read_only.assert_not_called()
            owner.close()

if __name__=='__main__': unittest.main()
