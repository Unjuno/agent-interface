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
                '--output-directory', str(root/'calls')])
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    listed = await client.list_tools()
                    self.assertEqual({tool.name for tool in listed.tools},
                                     {'interface_observe', 'interface_dispatch'})
                    reply = await client.call_tool('interface_dispatch', {
                        'program': {}, 'current_observation_seq': -1, 'current_binding_revision': 0})
                    row = json.loads(reply.content[0].text)
                    self.assertEqual(row['outcome_summary']['error'], 'INVALID_OBSERVATION_SEQ')
                    self.assertTrue(Path(row['call_directory']).is_relative_to(root/'calls'))

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
                    mcp.pop('call_directory')
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
                                     {'interface_observe', 'interface_dispatch'})
                    reply = await client.call_tool('interface_dispatch', {
                        'program': {}, 'current_observation_seq': -1, 'current_binding_revision': 0})
                    row = json.loads(reply.content[0].text)
                    self.assertEqual(row['outcome_summary']['error'], 'INVALID_OBSERVATION_SEQ')
                    self.assertEqual(row['image_status'], 'no_observation')

    async def test_report_persistence_failure_retains_result_without_replay(self):
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'fixture': 123}, td)
            report = {'schema': 'agent-interface/runtime-dispatch-result-v1',
                      'status': 'returned', 'result': {'status': 'completed'}}
            with patch('runtime.cli_v1.mcp_server.dispatch', return_value=report) as dispatch, patch(
                    'pathlib.Path.write_bytes', side_effect=OSError('disk full')):
                reply = await server.call_tool('interface_dispatch', {
                    'program': {}, 'current_observation_seq': 0, 'current_binding_revision': 0})
            dispatch.assert_called_once()
            row = json.loads(reply.content[0].text)
            self.assertIn('disk full', row['persistence_error'])
            self.assertEqual(row['outcome_summary']['execution_status'], 'completed')
            self.assertEqual(row['receipt']['source']['raw_report'], report)

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
