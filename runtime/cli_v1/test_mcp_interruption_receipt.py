"""MCP worker interruption custody, with Fake X and owned Python probes only."""
import asyncio
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from Xlib import X

from runtime.cli_v1 import mcp_server
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.test_mcp_process_identity import FakeX, metadata


class WorkerStop(BaseException):
    pass


async def grounded(server):
    source = metadata(await server.call_tool('interface_guarded_observe', {}))
    minted = metadata(await server.call_tool('interface_guarded_mint', dict(
        alias='field', source_sequence=source['source']['sequence'], point=[8, 8], region_size=[12, 12])))
    return dict(alias='field', offset=minted['offset'], interaction='keyboard', observe_after=False,
                tail=[dict(op='key_chord', keys=['CTRL', 'a'])])


async def input_record(server):
    rows = metadata(await server.call_tool('interface_results', {}))['calls']
    return next(row for row in rows if row['operation'] == 'guarded_input')


class InterruptionReceiptTests(unittest.IsolatedAsyncioTestCase):
    async def test_pending_fatal_worker_stop_can_be_retrieved_and_explicitly_recovered(self):
        for exception in (KeyboardInterrupt, SystemExit):
            with self.subTest(exception=exception.__name__), tempfile.TemporaryDirectory() as td:
                fake = FakeX(self)
                fake.backend.d.create_resource_object = lambda kind, xid: fake.backend.targets['app']
                server = mcp_server.create_server({'app': 20}, td, session_mode='guarded-x11')
                arguments = await grounded(server)
                entered, resume = threading.Event(), threading.Event()
                original = exception('pending worker CTRL')
                def emit(connection, kind, code):
                    fake.emit(connection, kind, code)
                    if kind == X.KeyPress:
                        entered.set()
                        if not resume.wait(5):
                            raise TimeoutError('test did not release its gate')
                        raise original
                try:
                    with patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit):
                        pending = metadata(await server.call_tool('interface_guarded_input',
                            dict(arguments, wait_for_result_ms=0)))
                        self.assertEqual(pending['status'], 'pending', pending)
                        self.assertTrue(await asyncio.to_thread(entered.wait, 2))
                        self.assertEqual(metadata(await server.call_tool('interface_close', {}))['status'], 'busy')
                        resume.set()
                        async def terminal():
                            while True:
                                result = metadata(await server.call_tool('interface_results',
                                    dict(call_id=pending['call_id'], include_image=False)))
                                if result['status'] != 'pending':
                                    return result
                                await asyncio.sleep(.005)
                        row = await asyncio.wait_for(terminal(), 2)
                    self.assertEqual(row['status'], 'runtime_interrupted', row)
                    self.assertEqual(row['exception_type'], exception.__name__)
                    self.assertTrue(row['session']['recovery_required'])
                    self.assertEqual(fake.down, set())
                    recovered = metadata(await server.call_tool('interface_guarded_recover_input',
                        {'current_binding_revision': row['session']['binding_revision']}))
                    self.assertEqual(recovered['status'], 'input_recovered', recovered)
                    self.assertTrue(recovered['review_required'])
                    self.assertFalse(recovered['replay_allowed'])
                    self.assertEqual([e for e in fake.emissions if e[0] == X.KeyPress], [(X.KeyPress, 1)])
                    print(json.dumps({'case': 'pending-fatal-recovery', 'exception': exception.__name__,
                        'pending': pending, 'terminal': row, 'recovery': recovered,
                        'emissions': fake.emissions}), flush=True)
                finally:
                    resume.set()

    async def test_worker_stop_retains_current_execution_and_lookup_never_replays(self):
        fake = FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            server = mcp_server.create_server({'app': 20}, td, session_mode='guarded-x11')
            arguments = await grounded(server)
            original = WorkerStop('after CTRL')
            def emit(connection, kind, code):
                fake.emit(connection, kind, code)
                if kind == X.KeyPress:
                    raise original
            with patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit):
                with self.assertRaises(WorkerStop) as caught:
                    await server.call_tool('interface_guarded_input', arguments)
            self.assertIs(caught.exception, original)
            call = await input_record(server)
            self.assertEqual(call['state'], 'finished')
            before = list(fake.emissions)
            for detail in ('full', 'brief'):
                row = metadata(await server.call_tool('interface_results',
                    dict(call_id=call['call_id'], include_image=False, detail=detail)))
                self.assertEqual(row['status'], 'runtime_interrupted', row)
                self.assertEqual(row['interrupted_execution'], fake.backend.interrupted_execution)
                self.assertTrue(row['session']['recovery_required'])
                self.assertFalse(row['operation_invoked'])
                self.assertFalse(row['replay_allowed'])
                self.assertIsNone(row['task_success'])
            self.assertEqual(fake.emissions, before)
            self.assertEqual(fake.down, set())
            print(json.dumps({'case': 'worker-stop', 'lookup': row, 'emissions': fake.emissions}), flush=True)

    async def test_previous_execution_is_not_attached_to_stop_before_dispatch(self):
        fake = FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            server = mcp_server.create_server({'app': 20}, td, session_mode='guarded-x11')
            arguments = await grounded(server)
            fake.backend.interrupted_execution = {'error': 'previous call', 'failed_op': 9}
            original = WorkerStop('before dispatch')
            with patch.object(GuardedSessionOwner, 'invoke_guarded', side_effect=original):
                with self.assertRaises(WorkerStop):
                    await server.call_tool('interface_guarded_input', arguments)
            call = await input_record(server)
            row = metadata(await server.call_tool('interface_results', dict(call_id=call['call_id'])))
            self.assertEqual(row['status'], 'runtime_interrupted', row)
            self.assertNotIn('interrupted_execution', row)
            self.assertEqual(fake.emissions, [])

    async def test_receipt_failure_preserves_stop_and_exposes_unavailability(self):
        for after_report in (False, True):
            for failure in (OSError, SystemExit):
                with self.subTest(after_report=after_report, persistence_error=failure.__name__):
                    fake = FakeX(self)
                    with tempfile.TemporaryDirectory() as td:
                        server = mcp_server.create_server({'app': 20}, td, session_mode='guarded-x11')
                        arguments = await grounded(server)
                        original = WorkerStop('call interrupted')
                        writer = mcp_server._write_json
                        def write(path, value):
                            if path.name == 'interruption.json':
                                raise failure('interruption receipt unavailable')
                            return writer(path, value)
                        target = (patch.object(mcp_server, 'present_management_report', side_effect=original)
                                  if after_report else patch.object(GuardedSessionOwner, 'invoke_guarded', side_effect=original))
                        with target, patch.object(mcp_server, '_write_json', side_effect=write):
                            with self.assertRaises(WorkerStop) as caught:
                                await server.call_tool('interface_guarded_input', arguments)
                        self.assertIs(caught.exception, original)
                        call = await input_record(server)
                        before = list(fake.emissions)
                        row = metadata(await server.call_tool('interface_results', dict(call_id=call['call_id'])))
                        self.assertEqual(row['status'], 'receipt_unavailable')
                        self.assertIn('interruption_persistence_failure', row['call'])
                        self.assertFalse(row['replay_allowed'])
                        self.assertEqual(fake.emissions, before)
                        if not after_report:
                            self.assertEqual(fake.emissions, [])

    async def test_stop_after_report_preserves_original_report_and_does_not_borrow_old_snapshot(self):
        fake = FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            server = mcp_server.create_server({'app': 20}, td, session_mode='guarded-x11')
            arguments = await grounded(server)
            fake.backend.interrupted_execution = {'error': 'previous call'}
            with patch.object(mcp_server, 'present_management_report', side_effect=WorkerStop('presentation')):
                with self.assertRaises(WorkerStop):
                    await server.call_tool('interface_guarded_input', arguments)
            call = await input_record(server)
            raw = json.loads((Path(td) / call['call_id'] / 'report.json').read_text())
            self.assertEqual(raw['status'], 'completed')
            before = list(fake.emissions)
            row = metadata(await server.call_tool('interface_results', dict(call_id=call['call_id'])))
            self.assertEqual(row['status'], 'runtime_interrupted', row)
            self.assertTrue(row['report_artifact_present'])
            self.assertNotIn('interrupted_execution', row)
            self.assertEqual(fake.emissions, before)

    async def test_keyboardinterrupt_and_systemexit_are_preserved_in_owned_process(self):
        for kind in ('KeyboardInterrupt', 'SystemExit'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                flags = ['-B'] + (['-O'] if sys.flags.optimize else [])
                proc = await asyncio.to_thread(subprocess.run,
                    [sys.executable, *flags, '-m', __name__, '--probe', td, kind],
                    cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=20)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                row = json.loads(proc.stdout)
                self.assertEqual(row['caught'], kind, row)
                self.assertEqual(row['receipts'], 1, row)
                self.assertEqual(row['report']['status'], 'runtime_interrupted')
                self.assertTrue(row['report']['session']['recovery_required'])
                self.assertEqual(row['down'], [])
                self.assertEqual(row['emissions'], [[X.KeyPress, 1], [X.KeyRelease, 1]])
                print(json.dumps({'case': 'owned-fatal-stop', 'kind': kind, 'receipt': row}), flush=True)


def probe(directory, kind):
    case = unittest.TestCase()
    fake = FakeX(case)
    error = {'KeyboardInterrupt': KeyboardInterrupt, 'SystemExit': SystemExit}[kind]('after CTRL')
    async def run():
        server = mcp_server.create_server({'app': 20}, directory, session_mode='guarded-x11')
        arguments = await grounded(server)
        def emit(connection, event, code):
            fake.emit(connection, event, code)
            if event == X.KeyPress:
                raise error
        with patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit):
            await server.call_tool('interface_guarded_input', arguments)
    caught = None
    try:
        asyncio.run(run())
    except BaseException as failure:
        caught = type(failure).__name__
    finally:
        case.doCleanups()
    files = list(Path(directory).glob('*/interruption.json'))
    print(json.dumps(dict(caught=caught, receipts=len(files),
                         report=json.loads(files[0].read_text()) if len(files) == 1 else None,
                         emissions=fake.emissions, down=sorted(fake.down))))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--probe':
        probe(sys.argv[2], sys.argv[3])
    else:
        unittest.main()
