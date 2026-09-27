import json
import asyncio
import threading
import io
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

from runtime.cli_v1.mcp_server import create_server


class PublicMCPTests(unittest.IsolatedAsyncioTestCase):

    async def test_validation_nesting_failure_retains_structured_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            with patch('runtime.cli_v1.mcp_server.inspect_program', side_effect=RecursionError), \
                 patch('runtime.cli_v1.mcp_server.dispatch') as dispatch, \
                 patch('runtime.cli_v1.mcp_server.observe') as observe:
                reply = await server.call_tool('interface_validate', {'program': {}})
                row = json.loads(reply.content[0].text)
                self.assertTrue(reply.isError)
                self.assertEqual(row['status'], 'input_error')
                self.assertEqual(row['error'], 'INPUT_NESTING_LIMIT')
                self.assertIsNone(row['static_valid'])
                self.assertIsNone(row['task_success'])
                self.assertIs(row['side_effect_authority'], False)
                self.assertIs(row['backend_checked'], False)
                self.assertEqual(row['runtime_admission'], 'not_evaluated')
                dispatch.assert_not_called()
                observe.assert_not_called()
            self.assertEqual(list(Path(td).iterdir()), [])

    async def test_static_validation_matches_inspector_without_action_or_retention(self):
        from copy import deepcopy
        from runtime.cli_v1.validate_program import inspect_program
        valid = {'schema': 'agent-interface/program-v1', 'program_id': 'draft',
                 'source': {'observation_seq': 0, 'binding_revision': 0},
                 'authority': {'lease_id': 'expired', 'expires_at_ns': 1},
                 'terminal': {'release_all_required': True},
                 'ops': [{'op': 'text', 'text': 'ab', 'gap_ms': 2}, {'op': 'release_all'}]}
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td, display_name='no-display')
            with patch('runtime.cli_v1.mcp_server.dispatch') as dispatch, \
                 patch('runtime.cli_v1.mcp_server.observe') as observe:
                for program in (valid, {}):
                    before = deepcopy(program)
                    response = await server.call_tool('interface_validate', {'program': program})
                    row = json.loads(response.content[0].text)
                    self.assertEqual(row, inspect_program(program))
                    self.assertEqual(response.isError, not row['static_valid'])
                    self.assertEqual(program, before)
                dispatch.assert_not_called()
                observe.assert_not_called()
            self.assertEqual(list(Path(td).iterdir()), [])

    async def test_report_references_require_explicit_opt_in_without_replay(self):
        from runtime.cli_v1.receipt_references import REPORT_REF, expand_receipt
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            args = {'target': 'fixture', 'frame': 'window_client', 'region': [0, 0, 1, 1]}
            report = {'status': 'returned', 'extension': 'x' * 4000}
            with patch('runtime.cli_v1.mcp_server.observe', return_value=report) as observe:
                for name, arguments in (('interface_observe', args), ('interface_results', {})):
                    reply = await server.call_tool(name, dict(arguments, report_refs=True))
                    row = json.loads(reply.content[0].text)
                    self.assertEqual(row['status'], 'invalid_request')
                    self.assertFalse(row['operation_invoked'])
                observe.assert_not_called()
                self.assertEqual(list(Path(td).iterdir()), [])
                original = await server.call_tool('interface_observe', dict(args, compact=True))
                old = json.loads(original.content[0].text)
                self.assertNotEqual(old['receipt']['schema'], REPORT_REF)
                retained = await server.call_tool('interface_results', {
                    'call_id': old['call_id'], 'compact': True, 'report_refs': True})
                new = json.loads(retained.content[0].text)
                self.assertEqual(new['receipt']['schema'], REPORT_REF)
                self.assertEqual(expand_receipt(new['receipt']), expand_receipt(old['receipt']))
                self.assertEqual(new['outcome_summary'], old['outcome_summary'])
                observe.assert_called_once()
                self.assertNotIn('report_refs', observe.call_args.kwargs)

    async def test_retained_image_can_be_omitted_without_changing_result_or_replaying(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            envelope = {'image_status': 'image', 'image_reference': {'sha256': 'retained'},
                        'outcome_summary': {'execution_status': 'completed'},
                        'image': {'type': 'image', 'mimeType': 'image/png', 'data': 'YWJj'}}
            with patch('runtime.cli_v1.mcp_server.observe', return_value={'status': 'returned'}) as observe, \
                 patch('runtime.cli_v1.mcp_server.present_result', return_value=envelope):
                original = await server.call_tool('interface_observe', {
                    'target': 'fixture', 'frame': 'window_client', 'region': [0,0,10,10]})
                call_id = json.loads(original.content[0].text)['call_id']
                raw_before = Path(td, call_id, 'report.json').read_bytes()
                omitted = await server.call_tool('interface_results', {
                    'call_id': call_id, 'include_image': False})
                self.assertEqual(len(omitted.content), 1)
                row = json.loads(omitted.content[0].text)
                self.assertEqual(row['image_delivery'], 'omitted_by_request')
                self.assertEqual(row['image_reference'], envelope['image_reference'])
                self.assertEqual(row['outcome_summary'], envelope['outcome_summary'])
                self.assertFalse(row['operation_invoked'])
                self.assertNotIn('YWJj', omitted.content[0].text)
                included = await server.call_tool('interface_results', {'call_id': call_id})
                self.assertEqual(included.content[1].data, 'YWJj')
                self.assertNotIn('image_delivery', json.loads(included.content[0].text))
                self.assertEqual(Path(td, call_id, 'report.json').read_bytes(), raw_before)
                observe.assert_called_once()
                for invalid in ('false', 0):
                    with self.assertRaises(Exception):
                        await server.call_tool('interface_results', {
                            'call_id': call_id, 'include_image': invalid})

    async def test_result_pages_are_stable_when_new_calls_arrive(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            async def result(args):
                return json.loads((await server.call_tool('interface_results', args)).content[0].text)
            with patch('runtime.cli_v1.mcp_server.observe', return_value={'status': 'returned'}) as observe:
                args = {'target': 'fixture', 'frame': 'window_client', 'region': [0,0,1,1]}
                ids = []
                for _ in range(23):
                    reply = await server.call_tool('interface_observe', args)
                    ids.append(Path(json.loads(reply.content[0].text)['call_directory']).name)
                first = await result({})
                self.assertEqual([r['call_id'] for r in first['calls']], list(reversed(ids))[:20])
                await server.call_tool('interface_observe', args)
                second = await result({'before_call_id': first['next_before_call_id']})
                self.assertEqual([r['call_id'] for r in second['calls']], list(reversed(ids))[-3:])
                self.assertIsNone(second['next_before_call_id'])
                self.assertEqual((await result({'before_call_id': ids[0]}))['calls'], [])
                self.assertEqual((await result({'before_call_id': 'missing'}))['status'], 'unknown_cursor')
                self.assertEqual((await result({'call_id': ids[0], 'before_call_id': ids[1]}))['status'], 'invalid_request')
                self.assertEqual(observe.call_count, 24)



    async def test_retained_results_never_repeat_backend_and_reject_unknown_ids(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            with patch('runtime.cli_v1.mcp_server.dispatch', return_value={
                    'schema': 'agent-interface/runtime-dispatch-result-v1',
                    'status': 'returned', 'result': {'status': 'completed'}}) as dispatch:
                original = await server.call_tool('interface_dispatch', {
                    'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0})
                listing = json.loads((await server.call_tool('interface_results', {})).content[0].text)
                self.assertEqual(listing['total_calls'], 1)
                call_id = json.loads(original.content[0].text)['call_id']
                self.assertEqual(call_id, listing['calls'][0]['call_id'])
                reread = json.loads((await server.call_tool('interface_results', {'call_id': call_id})).content[0].text)
                self.assertEqual(reread['outcome_summary'], json.loads(original.content[0].text)['outcome_summary'])
                self.assertIs(reread['operation_invoked'], False)
                self.assertEqual(reread['call_id'], call_id)
                self.assertEqual(reread['retained_call']['arguments']['program'], {})
                self.assertTrue(reread['retained_call']['backend_attempted'])
                self.assertIsNone(reread['retained_call']['persistence_failure'])
                unknown = await server.call_tool('interface_results', {'call_id': '../outside'})
                self.assertTrue(unknown.isError)
                Path(td, call_id, 'report.json').unlink()
                missing = await server.call_tool('interface_results', {'call_id': call_id})
                missing_row = json.loads(missing.content[0].text)
                self.assertEqual(missing_row['status'], 'receipt_unavailable')
                self.assertTrue(missing_row['call']['backend_attempted'])
                self.assertIsNone(missing_row['call']['persistence_failure'])
                self.assertIs(missing_row['replay_allowed'], False)
                dispatch.assert_called_once()


    async def test_portable_stdio_runs_outside_checkout(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from runtime.distribution_v2.build import SOURCE_FILES, build
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root/'source'
            repository = Path(__file__).resolve().parents[2]
            for name in SOURCE_FILES:
                target = source/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((repository/name).read_bytes())
            artifact = root/'runtime.pyz'
            build(source, artifact, root/'manifest.json', root/'sum')
            targets = root/'targets.json'
            targets.write_text('{"fixture":123}')
            params = StdioServerParameters(command=sys.executable, cwd=str(root), args=[
                str(artifact), 'mcp', '--targets', str(targets),
                '--output-directory', str(root/'calls'), '--display', 'not-a-valid-display'])
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    listed = await client.list_tools()
                    self.assertEqual({tool.name for tool in listed.tools},
                                     {'interface_observe', 'interface_dispatch', 'interface_results', 'interface_validate'})
                    dispatch_tool = next(t for t in listed.tools if t.name == 'interface_dispatch')
                    validation = await client.call_tool('interface_validate', {'program': {}})
                    self.assertTrue(validation.isError)
                    validation_row = json.loads(validation.content[0].text)
                    self.assertIs(validation_row['static_valid'], False)
                    self.assertEqual(validation_row['runtime_admission'], 'not_evaluated')
                    program_schema = dispatch_tool.inputSchema['properties']['program']
                    self.assertEqual(program_schema['type'], 'object')
                    for term in ('agent-interface/program-v1', 'expires_at_ns',
                                 'execution host monotonic clock', 'release_all',
                                 'gap_ms', 'repeat', '128'):
                        self.assertIn(term, program_schema['description'])
                    reply = await client.call_tool('interface_dispatch', {
                        'program': {}, 'current_observation_seq': -1, 'current_binding_revision': 0})
                    row = json.loads(reply.content[0].text)
                    self.assertEqual(row['outcome_summary']['error'], 'INVALID_OBSERVATION_SEQ')
                    self.assertTrue(Path(row['call_directory']).is_relative_to(root/'calls'))
                    retained = await client.call_tool('interface_results', {
                        'call_id': row['call_id']})
                    reread = json.loads(retained.content[0].text)
                    self.assertEqual(reread['outcome_summary'], row['outcome_summary'])
                    self.assertEqual(reread['call_id'], row['call_id'])
                    self.assertIs(reread['operation_invoked'], False)

                    # Real packaged transport: choose v3 only on explicit reread.
                    from runtime.cli_v1.receipt_references import REPORT_REF, expand_receipt
                    for tool in listed.tools:
                        if tool.name == 'interface_validate':
                            self.assertNotIn('report_refs', tool.inputSchema['properties'])
                            continue
                        option = tool.inputSchema['properties']['report_refs']
                        self.assertEqual(option['type'], 'boolean')
                        self.assertIs(option['default'], False)
                    if sys.platform != 'linux':
                        return  # The following control targets X11 initialization.
                    failed = await client.call_tool('interface_dispatch', {
                        'program': {'schema': 'agent-interface/program-v1',
                            'program_id': 'portable-reference-control',
                            'source': {'observation_seq': 1, 'binding_revision': 0},
                            'authority': {'lease_id': 'no-input', 'expires_at_ns': 1},
                            'terminal': {'release_all_required': True},
                            'ops': [{'op': 'focus', 'target': 'fixture'},
                                    {'op': 'text', 'text': 'price=13*7', 'gap_ms': 20},
                                    {'op': 'release_all'}]},
                        'current_observation_seq': 1, 'current_binding_revision': 0,
                        'compact': True})
                    default = json.loads(failed.content[0].text)
                    self.assertNotEqual(default['receipt']['schema'], REPORT_REF)
                    self.assertEqual(default['receipt']['source']['raw_report']['failure_phase'],
                                     'backend_initialization')
                    self.assertEqual(default['outcome_summary']['failure_phase'],
                                     'backend_initialization')
                    report_path = Path(default['call_directory'])/'report.json'
                    original_bytes = report_path.read_bytes()
                    referenced = await client.call_tool('interface_results', {
                        'call_id': default['call_id'], 'compact': True, 'report_refs': True})
                    referenced = json.loads(referenced.content[0].text)
                    self.assertEqual(referenced['receipt']['schema'], REPORT_REF)
                    self.assertEqual(expand_receipt(referenced['receipt']),
                                     expand_receipt(default['receipt']))
                    self.assertEqual(referenced['outcome_summary'], default['outcome_summary'])
                    self.assertFalse(referenced['operation_invoked'])
                    self.assertEqual(report_path.read_bytes(), original_bytes)
                    self.assertEqual(len(list((root/'calls').glob('*/request.json'))), 2)


    async def test_cli_and_mcp_preserve_identical_failed_presentation(self):
        from runtime.cli_v1.__main__ import _present_result
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            raw = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                   'status': 'runtime_failed', 'cleanup_error': 'release uncertain',
                   'result': {'status': 'execution_failed', 'recovery_required': True,
                              'execution': {'failed_op': 1, 'failed_op_effect': 'unknown'}}}
            for error in (ValueError('bad review'), RuntimeError('unexpected review error')):
                with self.subTest(error=error), patch('runtime.cli_v1.review.review_bytes', side_effect=error), patch(
                        'runtime.cli_v1.mcp_server.dispatch', return_value=raw) as dispatch:
                    reply = await server.call_tool('interface_dispatch', {
                        'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0})
                    output = io.StringIO()
                    with redirect_stdout(output):
                        code = _present_result(raw, with_review=True, capture_directory=td, exit_code=2)
                    mcp = json.loads(reply.content[0].text)
                    self.assertEqual(mcp.pop('call_id'), Path(mcp.pop('call_directory')).name)
                    self.assertEqual(len(reply.content), 1)
                    mcp['image'] = None  # MCP carries images separately from its text metadata.
                    self.assertEqual(mcp, json.loads(output.getvalue()))
                    self.assertEqual(mcp['raw_result'], raw)
                    self.assertTrue(mcp['outcome_summary']['recovery_required'])
                    self.assertEqual(code, 2)
                    dispatch.assert_called_once()

    async def test_cancelled_transport_keeps_worker_and_receipt_without_replay(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            entered, release = threading.Event(), threading.Event()
            def delayed(*args, **kwargs):
                entered.set()
                if not release.wait(5):
                    raise RuntimeError('test deadline')
                return {'status': 'returned'}
            from runtime.cli_v1.review import present_result
            presented = threading.Event()
            def present(*args, **kwargs):
                result = present_result(*args, **kwargs)
                presented.set()
                return result
            args = {'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0}
            with patch('runtime.cli_v1.mcp_server.dispatch', side_effect=delayed) as dispatch, patch(
                    'runtime.cli_v1.mcp_server.present_result', side_effect=present):
                first = asyncio.create_task(server.call_tool('interface_dispatch', args))
                try:
                    self.assertTrue(await asyncio.to_thread(entered.wait, 2))
                    listed = json.loads((await server.call_tool('interface_results', {})).content[0].text)
                    call_id = listed['calls'][0]['call_id']
                    pending = json.loads((await server.call_tool('interface_results', {'call_id': call_id})).content[0].text)
                    self.assertEqual(pending['status'], 'pending')
                    self.assertEqual(pending['call']['arguments'], args)
                    first.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await first
                    busy = await server.call_tool('interface_dispatch', args)
                    self.assertTrue(busy.isError)
                finally:
                    release.set()
                self.assertTrue(await asyncio.to_thread(presented.wait, 2))
                reports = list(Path(td).glob('*/report.json'))
                self.assertEqual(len(reports), 1)
                self.assertEqual(json.loads(reports[0].read_text()), {'status': 'returned'})
                for _ in range(100):
                    reread = json.loads((await server.call_tool('interface_results', {'call_id': call_id})).content[0].text)
                    if reread.get('status') != 'pending':
                        break
                    await asyncio.sleep(.01)
                self.assertEqual(reread['outcome_summary']['reported_status'], 'returned')
                self.assertIs(reread['operation_invoked'], False)
                dispatch.assert_called_once()

    async def test_overlapping_call_is_rejected_without_queueing_input(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            entered, release = threading.Event(), threading.Event()
            def delayed(*args, **kwargs):
                entered.set()
                if not release.wait(5):
                    raise RuntimeError('test deadline')
                return {'status': 'returned'}
            args = {'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0}
            with patch('runtime.cli_v1.mcp_server.dispatch', side_effect=delayed) as dispatch:
                first = asyncio.create_task(server.call_tool('interface_dispatch', args))
                try:
                    self.assertTrue(await asyncio.to_thread(entered.wait, 2))
                    second = await server.call_tool('interface_dispatch', args)
                    self.assertTrue(second.isError)
                    self.assertEqual(json.loads(second.content[0].text),
                                     {'status': 'busy', 'operation_invoked': False})
                finally:
                    release.set()
                    await first
                dispatch.assert_called_once()

    async def test_stdio_discovery_and_invalid_request_without_gui(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        with tempfile.TemporaryDirectory() as td:
            targets = Path(td) / 'targets.json'
            targets.write_text('{"fixture":123}')
            params = StdioServerParameters(command=sys.executable, args=[
                '-m', 'runtime.cli_v1.mcp_server', '--targets', str(targets),
                '--output-directory', str(Path(td)/'calls')])
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    listed = await client.list_tools()
                    self.assertEqual({tool.name for tool in listed.tools},
                                     {'interface_observe', 'interface_dispatch', 'interface_results', 'interface_validate'})
                    dispatch_tool = next(t for t in listed.tools if t.name == 'interface_dispatch')
                    program_schema = dispatch_tool.inputSchema['properties']['program']
                    self.assertEqual(program_schema['type'], 'object')
                    for term in ('agent-interface/program-v1', 'expires_at_ns',
                                 'execution host monotonic clock', 'release_all',
                                 'gap_ms', 'repeat', '128'):
                        self.assertIn(term, program_schema['description'])
                    reply = await client.call_tool('interface_dispatch', {
                        'program': {}, 'current_observation_seq': -1, 'current_binding_revision': 0})
                    row = json.loads(reply.content[0].text)
                    self.assertEqual(row['outcome_summary']['error'], 'INVALID_OBSERVATION_SEQ')
                    self.assertEqual(row['image_status'], 'no_observation')

    async def test_report_persistence_failure_retains_result_without_replay(self):
        from runtime.cli_v1.attempt import _write_json
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            report = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                      'status': 'returned', 'result': {'status': 'completed'}}
            def write(path, value):
                if path.name == 'report.json':
                    raise OSError('disk full')
                return _write_json(path, value)
            with patch('runtime.cli_v1.mcp_server.dispatch', return_value=report) as dispatch, patch(
                    'runtime.cli_v1.mcp_server._write_json', side_effect=write):
                reply = await server.call_tool('interface_dispatch', {
                    'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0})
            dispatch.assert_called_once()
            row = json.loads(reply.content[0].text)
            self.assertIn('disk full', row['persistence_error'])
            self.assertEqual(row['outcome_summary']['execution_status'], 'completed')
            self.assertEqual(row['receipt']['source']['raw_report'], report)
            self.assertTrue(reply.isError)
            self.assertIs(row['replay_allowed'], False)
            retained = await server.call_tool('interface_results', {'call_id': row['call_id']})
            missing = json.loads(retained.content[0].text)
            self.assertEqual(missing['status'], 'receipt_unavailable')
            self.assertTrue(missing['call']['backend_attempted'])
            self.assertEqual(missing['call']['persistence_failure'], 'report')
            self.assertIs(missing['operation_invoked'], False)
            self.assertIs(missing['replay_allowed'], False)

    async def test_request_persistence_failure_is_explicit_and_releases_busy_lock(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            args = {'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0}
            with patch('runtime.cli_v1.mcp_server._write_json', side_effect=OSError('disk full')), \
                 patch('runtime.cli_v1.mcp_server.dispatch') as dispatch:
                reply = await server.call_tool('interface_dispatch', args)
                row = json.loads(reply.content[0].text)
                self.assertTrue(reply.isError)
                self.assertEqual(row['error'], 'REQUEST_PERSISTENCE_FAILED')
                self.assertIs(row['operation_invoked'], False)
                dispatch.assert_not_called()
            retained = await server.call_tool('interface_results', {'call_id': row['call_id']})
            missing = json.loads(retained.content[0].text)
            self.assertEqual(missing['status'], 'receipt_unavailable')
            self.assertIs(missing['call']['backend_attempted'], False)
            self.assertEqual(missing['call']['persistence_failure'], 'request')
            self.assertIs(missing['replay_allowed'], False)
            with patch('runtime.cli_v1.mcp_server.dispatch', return_value={'status': 'returned'}) as dispatch:
                later = await server.call_tool('interface_dispatch', args)
                self.assertFalse(later.isError)
                dispatch.assert_called_once()

    async def test_report_replace_failure_keeps_temporary_bytes_without_claiming_receipt(self):
        import os
        original_replace = os.replace
        report = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                  'status': 'returned', 'result': {'status': 'completed'}}
        def replace(source, destination):
            if Path(destination).name == 'report.json':
                raise OSError('report replacement unavailable')
            return original_replace(source, destination)
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            with patch('runtime.cli_v1.attempt.os.replace', side_effect=replace), \
                 patch('runtime.cli_v1.mcp_server.dispatch', return_value=report) as dispatch:
                response = await server.call_tool('interface_dispatch', {
                    'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0})
                row = json.loads(response.content[0].text)
                directory = Path(row['call_directory'])
                temporary = directory / '.report.json.tmp'
                before = temporary.read_bytes()
                self.assertEqual(json.loads(before), report)
                self.assertFalse((directory / 'report.json').exists())
                self.assertTrue((directory / 'request.json').exists())
                self.assertTrue(response.isError)
                self.assertEqual(row['outcome_summary']['execution_status'], 'completed')
                retained = await server.call_tool('interface_results', {'call_id': row['call_id']})
                self.assertEqual(json.loads(retained.content[0].text)['status'], 'receipt_unavailable')
                self.assertEqual(temporary.read_bytes(), before)
                dispatch.assert_called_once()

    async def test_dispatch_once_preserves_failure_and_fixed_targets(self):
        with tempfile.TemporaryDirectory() as td:
            targets = {'fixture': 123}
            server = create_server(targets, td, display_name=':199')
            targets['fixture'] = 456
            report = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                      'status': 'runtime_failed', 'cleanup_error': 'close failed',
                      'result': {'status': 'execution_failed', 'recovery_required': True,
                                 'execution': {'failed_op': 2, 'failed_op_effect': 'unknown'}}}
            with patch('runtime.cli_v1.mcp_server.dispatch', return_value=report) as dispatch:
                reply = await server.call_tool('interface_dispatch', {
                    'program': {'ops': []}, 'current_observation_seq': 7,
                    'current_binding_revision': 3, 'compact': True})
            dispatch.assert_called_once()
            self.assertEqual(dispatch.call_args.args, ({'ops': []}, {'fixture': 123}))
            self.assertEqual(dispatch.call_args.kwargs['current_observation_seq'], 7)
            self.assertEqual(dispatch.call_args.kwargs['display_name'], ':199')
            metadata = json.loads(reply.content[0].text)
            self.assertTrue(metadata['outcome_summary']['recovery_required'])
            self.assertEqual(metadata['outcome_summary']['cleanup_error'], 'close failed')
            root = Path(metadata['call_directory'])
            self.assertEqual(json.loads((root/'report.json').read_text()), report)
            self.assertEqual(json.loads((root/'request.json').read_text())['targets'], {'fixture': 123})

    async def test_image_is_forwarded_once_outside_text(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            envelope = {'status': 'returned', 'image': {
                'type': 'image', 'mimeType': 'image/png', 'data': 'YWJj'}}
            with patch('runtime.cli_v1.mcp_server.observe', return_value={'status': 'returned'}) as observe, patch(
                    'runtime.cli_v1.review.review_bytes', return_value=envelope):
                reply = await server.call_tool('interface_observe', {
                    'target': 'fixture', 'frame': 'window_client', 'region': [0, 0, 10, 10]})
            observe.assert_called_once()
            self.assertEqual(len(reply.content), 2)
            self.assertEqual(reply.content[1].data, 'YWJj')
            self.assertNotIn('YWJj', reply.content[0].text)
            self.assertIn('image', envelope)

    async def test_unexpected_backend_and_review_errors_never_repeat_input(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            with patch('runtime.cli_v1.mcp_server.dispatch', side_effect=RuntimeError('uncertain')) as dispatch, patch(
                    'runtime.cli_v1.review.review_bytes', side_effect=ValueError('review failed')):
                reply = await server.call_tool('interface_dispatch', {
                    'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0})
            dispatch.assert_called_once()
            metadata = json.loads(reply.content[0].text)
            self.assertEqual(metadata['raw_result']['effect_status'], 'unknown')
            self.assertEqual(metadata['image_status'], 'needs_review')

    async def test_strict_arguments_refuse_before_backend(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            for seq in (True, '1', 1.5):
                with patch('runtime.cli_v1.mcp_server.dispatch') as dispatch:
                    with self.assertRaises(Exception):
                        await server.call_tool('interface_dispatch', {
                            'program': {}, 'current_observation_seq': seq, 'current_binding_revision': 0})
                    dispatch.assert_not_called()
            self.assertEqual(list(Path(td).iterdir()), [])

    def test_invalid_target_configuration(self):
        with tempfile.TemporaryDirectory() as td:
            for targets in ({}, {'fixture': True}, {'fixture': 0}, {'': 5}, []):
                with self.assertRaises(ValueError):
                    create_server(targets, td)


if __name__ == '__main__':
    unittest.main()
