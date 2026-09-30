import asyncio
from contextlib import ExitStack
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

    async def test_post_dispatch_inspection_is_opt_in_retained_and_never_replayed(self):
        from copy import deepcopy
        raw = json.loads((Path(__file__).parent/'fixtures/nonpaced_dispatch_review.json').read_text())['receipt']['source']['raw_report']
        for case in ('success', 'inspection_error', 'helper_error', 'release_failure'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td, ExitStack() as stack:
                session = self.fixture()
                stack.enter_context(self.selection())
                stack.enter_context(patch('runtime.cli_v1.mcp_session.open_session', return_value=session))
                evidence = {'window_id':456,'transient_chain':[456,123]}
                inspect = stack.enter_context(patch('runtime.cli_v1.mcp_session.inspect_focused_target', return_value=evidence))
                report = deepcopy(raw)
                if case == 'release_failure': report['result']['execution']['releases'][0]['verified'] = False
                if case == 'inspection_error': inspect.side_effect = OSError('lost focus metadata')
                if case == 'helper_error': stack.enter_context(patch.object(MCPSessionOwner,'inspect_after_dispatch',side_effect=RuntimeError('helper failure')))
                dispatch = stack.enter_context(patch('runtime.cli_v1.mcp_server.dispatch_in_session', return_value=report))
                stack.enter_context(patch('runtime.cli_v1.mcp_server.present_result', side_effect=lambda report,*a,**k: {'report':deepcopy(report)}))
                server = create_server({'fixture':123},td,session_mode='persistent-x11')
                args = {'program':{},'current_observation_seq':1,'current_binding_revision':1,'inspect_after':'fixture','detail':'summary','compact':True,'report_refs':True}
                row = self.row(await server.call_tool('interface_dispatch',args))
                context = row['post_dispatch_inspection']
                self.assertEqual(row['report']['result'],report['result'])
                self.assertEqual(row['session']['binding_revision'],1)
                self.assertEqual(row['session']['targets'],{'fixture':123})
                if case == 'success': self.assertEqual(context['review_request']['tool'],'interface_review_target')
                elif case == 'release_failure': self.assertEqual(context['status'],'skipped')
                else: self.assertIn('error',context)
                stored = Path(row['call_directory'],'report.json').read_bytes()
                previous = inspect.call_count
                retained = self.row(await server.call_tool('interface_results',{'call_id':row['call_id'],'include_image':False}))
                self.assertEqual(retained['post_dispatch_inspection'],context)
                self.assertFalse(retained['operation_invoked'])
                self.assertEqual(inspect.call_count,previous)
                self.assertEqual(Path(row['call_directory'],'report.json').read_bytes(),stored)
                dispatch.assert_called_once()
                self.assertNotIn('inspect_after',dispatch.call_args.kwargs)
                session.backend.focus.assert_not_called()
                await server.call_tool('interface_close',{})

    async def test_post_dispatch_inspection_rejects_invalid_target_or_mode_before_input(self):
        for mode,target in [('one-shot','fixture'),('persistent-x11','unknown')]:
            with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_server.dispatch') as direct, patch('runtime.cli_v1.mcp_server.dispatch_in_session') as owned, patch('runtime.cli_v1.mcp_session.open_session') as opened:
                server=create_server({'fixture':123},td,session_mode=mode)
                reply=await server.call_tool('interface_dispatch',{'program':{},'current_observation_seq':1,'current_binding_revision':1,'inspect_after':target})
                self.assertTrue(reply.isError)
                self.assertFalse(self.row(reply)['operation_invoked'])
                direct.assert_not_called(); owned.assert_not_called(); opened.assert_not_called()

    async def test_inspection_error_flag_separates_pending_review_from_failures(self):
        from runtime.cli_v1.attempt import _write_json as write_json
        for case in ('ready_metadata', 'ready_image', 'inspect_failure', 'capture_failure',
                     'changed_during_capture', 'presentation_failure', 'persistence_failure'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td, ExitStack() as stack:
                session=self.fixture()
                evidence={'window_id':456,'transient_chain':[456,123]}
                stack.enter_context(self.selection())
                stack.enter_context(patch('runtime.cli_v1.mcp_session.open_session',return_value=session))
                inspect=stack.enter_context(patch('runtime.cli_v1.mcp_session.inspect_focused_target',return_value=evidence))
                if case=='inspect_failure':
                    inspect.side_effect=OSError('window unavailable')
                if case=='capture_failure':
                    session.backend.observe_read_only.side_effect=OSError('capture unavailable')
                if case=='changed_during_capture':
                    inspect.side_effect=[evidence,dict(evidence,window_id=457)]
                shown={'image_status':'image','image':{'type':'image','mimeType':'image/png','data':'YWJj'}}
                if case=='presentation_failure':
                    shown={'image_status':'needs_review','image_error':'artifact unavailable'}
                stack.enter_context(patch('runtime.cli_v1.mcp_server.present_result',return_value=shown))
                if case=='persistence_failure':
                    def persist(path,value):
                        if Path(path).name=='report.json':raise OSError('disk full')
                        return write_json(path,value)
                    stack.enter_context(patch('runtime.cli_v1.mcp_server._write_json',side_effect=persist))
                server=create_server({'fixture':123},td,session_mode='persistent-x11')
                arguments={'target':'fixture'}
                if case!='ready_metadata':arguments['screen_region']=[0,0,10,10]
                reply=await server.call_tool('interface_inspect_target',arguments)
                row=self.row(reply)
                self.assertEqual(reply.isError,case not in ('ready_metadata','ready_image'))
                self.assertEqual(row['status'],'needs_review')
                self.assertFalse(row['input_dispatched'])
                self.assertFalse(row['authority_granted'])
                self.assertEqual(row['session']['binding_revision'],1)
                self.assertEqual(row['session']['targets'],{'fixture':123})
                if case.startswith('ready_'):
                    self.assertEqual(row['review_request']['tool'],'interface_review_target')
                session.backend.focus.assert_not_called()
                session.backend.release_all.assert_not_called()
                session.dispatch.assert_not_called()
                await server.call_tool('interface_close',{})

    async def test_recovery_capture_validates_before_release_and_only_captures_success(self):
        owner = MCPSessionOwner({'fixture': 123})
        session = self.fixture(); owner.session = session; owner.state = 'open'
        session.recover_input = Mock(return_value={'status': 'recovery_failed',
            'release_attempted': True, 'recovery_required': True})
        for target, region in [('fixture', None), (None, [0, 0, 1, 1]),
                               ('missing', [0, 0, 1, 1]), ('fixture', [0, 0, True, 1]),
                               ('fixture', [0, 0, 0, 1]), ('fixture', [0, 0, 8192, 8192])]:
            self.assertEqual(owner.recover_input(1, target, region)['error'], 'INVALID_RECOVERY_OBSERVATION')
        session.recover_input.assert_not_called()
        failed = owner.recover_input(1, 'fixture', [0, 0, 1, 1])
        self.assertEqual(failed['status'], 'recovery_failed')
        session.backend.observe_read_only.assert_not_called()
        session.recover_input.return_value = {'status': 'input_recovered',
            'release_attempted': True, 'recovery_required': False}
        session.backend.observe_read_only.side_effect = OSError('window vanished')
        recovered = owner.recover_input(1, 'fixture', [0, 0, 1, 1])
        self.assertEqual(recovered['status'], 'input_recovered')
        self.assertEqual(recovered['binding_revision'], 2)
        self.assertEqual(recovered['observation_report']['status'], 'observation_failed')
        self.assertEqual(owner.recover_input(1, 'fixture', [0, 0, 1, 1])['error'], 'SESSION_BINDING_REVISION_MISMATCH')
        session.backend.observe_read_only.assert_called_once()

    async def test_recovery_capture_persists_and_historical_read_does_not_recapture(self):
        session = self.fixture()
        session.recover_input = Mock(return_value={'status': 'input_recovered',
            'release_attempted': True, 'recovery_required': False})
        with tempfile.TemporaryDirectory() as td, self.selection(), patch(
                'runtime.cli_v1.mcp_session.open_session', return_value=session):
            server = create_server({'fixture': 123}, td, session_mode='persistent-x11')
            await server.call_tool('interface_observe', {'target': 'fixture', 'frame': 'window_client', 'region': [0, 0, 1, 1]})
            session.backend.observe_read_only.reset_mock()
            args = {'current_binding_revision': 1, 'target': 'fixture', 'region': [0, 0, 1, 1]}
            with patch('runtime.cli_v1.mcp_server._write_json', side_effect=OSError('disk full')):
                refused = self.row(await server.call_tool('interface_recover_input', args))
            self.assertEqual(refused['error'], 'REQUEST_PERSISTENCE_FAILED')
            session.recover_input.assert_not_called()
            session.backend.observe_read_only.assert_not_called()
            recovered = self.row(await server.call_tool('interface_recover_input', args))
            self.assertEqual(recovered['observation_report']['status'], 'returned')
            recorded = json.loads(Path(recovered['call_directory'], 'report.json').read_text())
            self.assertEqual(recorded['binding_revision'], 2)
            retained = self.row(await server.call_tool('interface_results', {'call_id': recovered['call_id']}))
            self.assertFalse(retained['operation_invoked'])
            self.assertEqual(retained['observation_report'], recovered['observation_report'])
            session.recover_input.assert_called_once()
            session.backend.observe_read_only.assert_called_once_with('fixture', 'window_client', [0, 0, 1, 1])

    async def test_recovery_requires_existing_owner_and_current_revision(self):
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session') as opened:
            owner = MCPSessionOwner({'fixture': 123})
            self.assertEqual(owner.recover_input(1)['error'], 'RECOVERY_REQUIRES_OPEN_SESSION')
            opened.assert_not_called()
            session = self.fixture()
            session.recover_input = Mock(return_value={'status': 'recovery_failed',
                'release_attempted': True, 'recovery_required': True})
            owner.session = session; owner.state = 'open'
            owner.target_review = {'pending': True}
            self.assertEqual(owner.recover_input(0)['error'], 'SESSION_BINDING_REVISION_MISMATCH')
            session.recover_input.assert_not_called()
            self.assertEqual(owner.recover_input(1)['status'], 'recovery_failed')
            self.assertEqual(owner.binding_revision, 1)
            session.recover_input.return_value = {'status': 'input_recovered',
                'release_attempted': True, 'recovery_required': False}
            self.assertEqual(owner.recover_input(1)['binding_revision'], 2)
            self.assertIsNone(owner.target_review)
            self.assertEqual(owner.recover_input(1)['error'], 'SESSION_BINDING_REVISION_MISMATCH')
            self.assertEqual(session.recover_input.call_count, 2)

    async def test_recovery_is_persisted_and_retained_reads_never_repeat_release(self):
        session = self.fixture()
        session.recovery_required = True
        def recover():
            session.recovery_required = False
            return {'status': 'input_recovered', 'release_attempted': True,
                    'recovery_required': False, 'release': session.backend.release_all()}
        session.recover_input = Mock(side_effect=recover)
        with tempfile.TemporaryDirectory() as td, self.selection(), patch(
                'runtime.cli_v1.mcp_session.open_session', return_value=session):
            server = create_server({'fixture': 123}, td, session_mode='persistent-x11')
            observed = self.row(await server.call_tool('interface_observe', {
                'target': 'fixture', 'region': [0, 0, 1, 1], 'frame': 'window_client'}))
            with patch('runtime.cli_v1.mcp_server._write_json', side_effect=OSError('disk full')):
                failed = self.row(await server.call_tool('interface_recover_input', {'current_binding_revision': 1}))
            self.assertEqual(failed['error'], 'REQUEST_PERSISTENCE_FAILED')
            session.recover_input.assert_not_called()
            recovered = self.row(await server.call_tool('interface_recover_input', {'current_binding_revision': 1}))
            self.assertEqual(recovered['status'], 'input_recovered')
            self.assertEqual(recovered['session']['binding_revision'], 2)
            self.assertEqual(recovered['session']['session_id'], observed['session']['session_id'])
            retained = self.row(await server.call_tool('interface_results', {'call_id': recovered['call_id']}))
            self.assertEqual(retained['status'], 'input_recovered')
            self.assertFalse(retained['operation_invoked'])
            session.recover_input.assert_called_once()
            session.backend.release_all.assert_called_once()
            old = self.row(await server.call_tool('interface_dispatch', {'program': {},
                'current_observation_seq': 0, 'current_binding_revision': 1}))
            report = json.loads(Path(old['call_directory'], 'report.json').read_text())
            self.assertEqual(report['error'], 'SESSION_BINDING_REVISION_MISMATCH')
            session.dispatch.assert_not_called()

    async def test_recovery_tool_is_only_on_persistent_public_route(self):
        with tempfile.TemporaryDirectory() as td:
            for mode in ('one-shot', 'persistent-x11', 'guarded-x11'):
                server = create_server({'fixture': 123}, Path(td)/mode, session_mode=mode)
                names = {tool.name for tool in await server.list_tools()}
                self.assertEqual('interface_recover_input' in names, mode == 'persistent-x11')

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
            request=inspection['review_request']
            self.assertEqual(request['tool'], 'interface_review_target')
            args=request['arguments']
            self.assertEqual(args, {'target':'fixture','window_id':456,'review_id':inspection['review_id']})
            self.assertEqual(retained['review_request'], request)
            reviewed=self.row(await server.call_tool(request['tool'],args))
            self.assertEqual(reviewed['binding_revision'],2)
            self.assertEqual(session.backend.targets['fixture'].id,456)
            self.assertTrue(session.recovery_required)
            session.backend.release_all.assert_not_called()
            session.backend.focus.assert_not_called()
            replay=await server.call_tool('interface_review_target',args)
            self.assertTrue(replay.isError)
            again=self.row(replay)
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
                owner.review_target(**inspected['review_request']['arguments'])
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
                owner.review_target(**inspected['review_request']['arguments'])
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

    async def test_captured_request_passes_public_schema_without_alias_translation(self):
        session=self.fixture();session.backend.targets={'fixture':SimpleNamespace(id=123)}
        session.backend.d.create_resource_object.side_effect=lambda kind,wid: SimpleNamespace(id=wid)
        with tempfile.TemporaryDirectory() as td, self.selection(), patch(
                'runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',return_value={'window_id':456}):
            server=create_server({'fixture':123},td,session_mode='persistent-x11')
            row=self.row(await server.call_tool('interface_inspect_target',
                {'target':'fixture','screen_region':[0,0,10,10]}))
            self.assertEqual(session.backend.targets['fixture'].id,123)
            request=row['review_request']
            self.assertEqual(request['arguments']['screen_region'],[0,0,10,10])
            reviewed=self.row(await server.call_tool(request['tool'],request['arguments']))
            self.assertEqual(reviewed['status'],'target_reviewed')
            self.assertEqual(reviewed['capture_consistency'],'matched')
            self.assertEqual(reviewed['binding_revision'],2)
            session.backend.focus.assert_not_called()
            session.backend.release_all.assert_not_called()
            session.dispatch.assert_not_called()
            await server.call_tool('interface_close',{})

    async def test_editing_request_cannot_change_pending_target_evidence(self):
        session=self.fixture()
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',return_value={'window_id':456}):
            owner=MCPSessionOwner({'fixture':123})
            region=[0,0,10,10]
            row=owner.inspect_target('fixture',screen_region=region)
            region[2]=99
            self.assertEqual(row['review_request']['arguments']['screen_region'],[0,0,10,10])
            row['review_request']['arguments']['window_id']=999
            self.assertEqual(owner.target_review['evidence']['window_id'],456)
            with self.assertRaisesRegex(ValueError,'mismatched'):
                owner.review_target(**row['review_request']['arguments'])
            self.assertEqual(owner.targets,{'fixture':123})
            self.assertEqual(owner.binding_revision,1)
            owner.close()

    async def test_capture_disagreement_retains_observation_but_no_review_id(self):
        session=self.fixture()
        with self.selection(), patch('runtime.cli_v1.mcp_session.open_session',return_value=session), patch(
                'runtime.cli_v1.mcp_session.inspect_focused_target',side_effect=[{'window_id':456},{'window_id':123}]):
            owner=MCPSessionOwner({'fixture':123})
            result=owner.inspect_target('fixture',screen_region=[0,0,10,10])
            self.assertEqual(result['error'],'TARGET_CHANGED_DURING_CAPTURE')
            self.assertEqual(result['observation_report']['status'],'returned')
            self.assertNotIn('review_id',result)
            self.assertNotIn('review_request',result)
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
            with self.assertRaises(ValueError): owner.review_target(**inspected['review_request']['arguments'])
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
            self.assertNotIn('review_request',result)
            self.assertIsNone(owner.target_review)
            session.backend.observe_read_only.assert_not_called()
            owner.close()

if __name__=='__main__': unittest.main()
