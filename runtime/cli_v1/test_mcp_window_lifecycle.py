"""Actual public caller with direct-subscription Fake X and real worker/session."""
import asyncio
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from Xlib import X
from .mcp_server import create_server
from .test_mcp_process_identity import FakeX, metadata
from runtime.guarded_x11_v1.test_window_lifecycle import LifecycleConnection


class LifecycleMCPTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, fault=None, trigger=None, isolated=False, selected=True):
        fake = FakeX(self)
        fake.backend.d.get_display_name = lambda: ':fake-lifecycle'
        connection = LifecycleConnection()
        entered, resume = threading.Event(), threading.Event()
        now = [1_000_000]
        def attributes():
            if fault == 'blocked' and 1 in fake.down:
                entered.set()
                if not resume.wait(5): raise TimeoutError('test did not resume')
        connection.on_attributes = attributes
        original_emit = fake.emit
        def emit(display, kind, code):
            original_emit(display, kind, code)
            if fault == 'modifier' and kind == X.KeyPress and code == 1:
                connection.event(X.DestroyNotify)
        # Override FakeX's injection patch with the event-producing transport.
        with tempfile.TemporaryDirectory() as td, \
                patch('time.monotonic_ns', side_effect=lambda: now[0]), \
                patch('runtime.guarded_x11_v1.target_queries.display.Display', return_value=connection), \
                patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity', side_effect=fake.read), \
                patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit):
            if isolated:
                from runtime.guarded_x11_v1.test_observation_worker import reader_backend
                from types import SimpleNamespace
                backend = reader_backend(fake, lambda *args: SimpleNamespace(data=fake.raw, depth=24, visual=1))
                backend.d.create_resource_object = lambda kind, xid: SimpleNamespace(id=xid)
                for target, kwargs in [
                    ('runtime.guarded_x11_v1.observation_worker.open_readonly_backend', dict(return_value=backend)),
                    ('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity', dict(side_effect=fake.read))]:
                    item = patch(target, **kwargs); item.start(); self.addCleanup(item.stop)
            server = create_server({'app':20}, td, session_mode='guarded-x11', guarded_process_identity=True,
                guarded_query_worker=True, guarded_observation_worker=isolated, guarded_window_lifecycle=selected)
            try:
                observed = metadata(await server.call_tool('interface_guarded_observe', {}))
                self.assertEqual(observed['status'], 'observed', observed)
                token = observed['source']['pointer_binding'].get('window_generation')
                if selected: self.assertRegex(token, r'^[0-9a-f]{64}$')
                else: self.assertIsNone(token)
                self.assertEqual(json.loads((Path(observed['call_directory'])/'report.json').read_text())['source'], observed['source'])
                minted = metadata(await server.call_tool('interface_guarded_mint', dict(alias='field',
                    source_sequence=observed['source']['sequence'], point=[8,8], region_size=[12,12])))
                if fault == 'stale': connection.event(X.DestroyNotify)
                if fault == 'reparent':
                    for kind in (X.UnmapNotify, X.ReparentNotify, X.MapNotify): connection.event(kind)
                args = dict(alias='field', offset=minted['offset'], interaction='keyboard', observe_after=False,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])
                task = asyncio.create_task(server.call_tool('interface_guarded_input', args))
                if fault == 'blocked':
                    self.assertTrue(await asyncio.to_thread(entered.wait, 2))
                    self.assertEqual(fake.down, {1})
                    if trigger == 'expiry': now[0] = fake.backend.owner.deadline
                    else:
                        listing = metadata(await server.call_tool('interface_results', {}))
                        call_id = next(row['call_id'] for row in listing['calls'] if row['operation'] == 'guarded_input')
                        cancelled = metadata(await server.call_tool('interface_guarded_cancel', {'call_id':call_id}))
                        self.assertEqual(cancelled['status'], 'cancel_requested')
                result = metadata(await asyncio.wait_for(task, 3))
                expected = 'refused' if fault == 'stale' and selected else 'execution_failed' if fault in ('modifier','blocked') else 'completed'
                self.assertEqual(result['status'], expected, result)
                if expected == 'completed': self.assertEqual(fake.emissions, [(2,1),(2,2),(3,2),(3,1)])
                elif fault == 'stale': self.assertEqual(fake.emissions, [])
                else:
                    self.assertEqual(fake.emissions, [(2,1),(3,1)])
                    self.assertTrue(result['result']['execution']['releases'][-1]['verified'])
                self.assertEqual(fake.down, set())
                if fault == 'blocked':
                    self.assertFalse(resume.is_set())
                    sequence = fake.backend.owner.sequence
                    resume.set()
                    for _ in range(100):
                        if connection.closed: break
                        await asyncio.sleep(.005)
                    self.assertTrue(connection.closed)
                    self.assertEqual(fake.backend.owner.sequence, sequence)
                    retried = metadata(await server.call_tool('interface_guarded_input', args))
                    self.assertEqual(retried['status'], 'refused')
                if isolated and expected == 'completed':
                    records = list(Path(td).rglob('qualified-observation-*.json'))
                    self.assertTrue(records)
                    self.assertTrue(all(json.loads(p.read_text())['pointer_binding']['window_generation']==token for p in records))
                before = list(fake.emissions)
                await server.call_tool('interface_results', {'call_id':result['call_id']})
                self.assertEqual(fake.emissions, before)
            finally:
                resume.set()
                await server.call_tool('interface_close', {})

    async def test_healthy(self): await self.exercise()
    async def test_unselected_process_only_still_allows_same_xid_residual(self): await self.exercise('stale', selected=False)
    async def test_reparent_remap(self): await self.exercise('reparent')
    async def test_same_process_destroy_reuse(self): await self.exercise('stale')
    async def test_modifier_prefix_released(self): await self.exercise('modifier')
    async def test_cancel_blocked_lifecycle(self): await self.exercise('blocked', 'cancel')
    async def test_expire_blocked_lifecycle(self): await self.exercise('blocked', 'expiry')
    async def test_isolated_observation_healthy(self): await self.exercise(isolated=True)
    async def test_isolated_observation_modifier_released(self): await self.exercise('modifier', isolated=True)


class LifecycleBoundaries(unittest.TestCase):
    def test_capture_destroy_cannot_publish_sequence_or_history(self):
        fake = FakeX(self)
        fake.backend.d.get_display_name = lambda: ':fake-lifecycle'
        connection = LifecycleConnection()
        capture = fake.backend.observe_read_only
        def changed(*args, **kwargs):
            result = capture(*args, **kwargs)
            connection.event(X.DestroyNotify)
            return result
        fake.backend.observe_read_only = changed
        from runtime.guarded_x11_v1.bridge import NativeHandleBridge
        with tempfile.TemporaryDirectory() as td, \
                patch('runtime.guarded_x11_v1.target_queries.display.Display', return_value=connection):
            bridge = NativeHandleBridge(None, {'app':20}, 'app', td+'/bridge',
                process_identity=True, query_worker=True, window_lifecycle=True)
            try:
                with self.assertRaises(RuntimeError): bridge.observe()
                self.assertEqual(bridge.sequence, 0)
                self.assertEqual(len(bridge.history), 0)
                self.assertTrue(bridge.review_required)
                self.assertEqual(fake.emissions, [])
            finally: bridge.close()

    def test_activation_pins_source_and_rejects_destroy_before_native_request(self):
        from runtime.guarded_x11_v1.bridge import NativeHandleBridge
        for destroy in (False, True):
            with self.subTest(destroy=destroy):
                fake = FakeX(self); backend = fake.backend
                backend.d.get_display_name = lambda: ':fake-lifecycle'
                backend._activation_supported = lambda: True
                backend._window_property = lambda name: [20]
                backend._focus_within = lambda xid: True
                backend.d.intern_atom = lambda name: 7
                backend.d.flush = Mock(); backend.root.send_event = Mock()
                connection = LifecycleConnection()
                with tempfile.TemporaryDirectory() as td, \
                        patch('runtime.guarded_x11_v1.target_queries.display.Display', return_value=connection), \
                        patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity', side_effect=fake.read), \
                        patch('time.monotonic_ns', return_value=1_000_000):
                    bridge = NativeHandleBridge(None, {'app':20}, 'app', td+'/bridge',
                        process_identity=True, query_worker=True, window_lifecycle=True)
                    try:
                        source = bridge.observe()
                        target = backend._activation_target
                        def replaced(name):
                            value = target(name)
                            if destroy: connection.event(X.DestroyNotify)
                            return value
                        backend._activation_target = replaced
                        result = bridge.activate_window(window_id=20, source_sequence=source['sequence'],
                            current_binding_revision=0, expires_at_ns=2_000_000, timeout_ms=100)
                        self.assertEqual(result['status'], 'execution_failed' if destroy else 'completed', result)
                        self.assertEqual(backend.root.send_event.call_count, 0 if destroy else 1)
                        self.assertTrue(result['execution']['releases'][-1]['verified'])
                        self.assertEqual(fake.emissions, [])
                    finally: bridge.close()

    def test_selection_dependencies_and_cli_forwarding(self):
        from .mcp_server import main
        import io
        with tempfile.TemporaryDirectory() as td:
            for options in [dict(guarded_window_lifecycle=True),
                            dict(guarded_window_lifecycle=1),
                            dict(guarded_window_lifecycle=True, guarded_process_identity=True)]:
                with self.assertRaises(ValueError):
                    create_server({'app':20}, Path(td)/'absent', session_mode='guarded-x11', **options)
                self.assertFalse((Path(td)/'absent').exists())
            targets = Path(td)/'targets.json'; targets.write_text('{"app":20}')
            argv = ['server','--targets',str(targets),'--output-directory',str(Path(td)/'out'),
                '--session-mode','guarded-x11','--guarded-process-identity','--guarded-query-worker',
                '--guarded-window-lifecycle']
            with patch('sys.argv', argv), patch('runtime.cli_v1.mcp_server.create_server') as create:
                main()
                self.assertIs(create.call_args.kwargs['guarded_window_lifecycle'], True)
            with patch('sys.argv', [x for x in argv if x!='--guarded-query-worker']), patch('sys.stderr', new_callable=io.StringIO):
                with self.assertRaises(SystemExit): main()


if __name__ == '__main__': unittest.main()
