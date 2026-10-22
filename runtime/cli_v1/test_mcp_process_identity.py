"""Startup selection and public MCP -> actual guarded runtime, with Fake X only."""
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from PIL import Image
from Xlib import X
from runtime.cli_v1.mcp_server import create_server, main
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.guarded_x11_v1.bridge import _GuardedBackend


def metadata(response):
    return json.loads(response.content[0].text)


class StartupTests(unittest.TestCase):
    def test_invalid_selection_refuses_before_creating_output_or_opening(self):
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge') as opened:
            for mode, value in [('one-shot', True), ('persistent-x11', True),
                                ('guarded-x11', 1), ('guarded-x11', 'yes'), ('guarded-x11', None)]:
                with self.subTest(mode=mode, value=value):
                    out = Path(td)/'not-created'
                    with self.assertRaises(ValueError):
                        create_server({'app':20}, out, session_mode=mode,
                                      guarded_process_identity=value)
                    self.assertFalse(out.exists())
            opened.assert_not_called()

    def test_owner_rejects_non_boolean_selection(self):
        with tempfile.TemporaryDirectory() as td:
            for value in (1, 'true', None):
                with self.assertRaises(ValueError):
                    GuardedSessionOwner({'app':20}, td, process_identity=value)

    def test_cli_forwards_explicit_startup_selection(self):
        with tempfile.TemporaryDirectory() as td:
            targets = Path(td)/'targets.json'
            targets.write_text('{"app":20}', encoding='utf-8')
            out = str(Path(td)/'out')
            argv = ['server', '--targets', str(targets), '--output-directory', out,
                    '--session-mode', 'guarded-x11', '--guarded-process-identity']
            with patch('sys.argv', argv), patch('runtime.cli_v1.mcp_server.create_server') as create:
                main()
            create.assert_called_once_with({'app':20}, Path(out), display_name=None,
                session_mode='guarded-x11', guarded_process_identity=True)
            create.return_value.run.assert_called_once_with(transport='stdio')

    def test_cli_wrong_mode_refuses_before_reading_targets(self):
        argv = ['server', '--targets', 'missing-targets.json', '--output-directory', 'unused',
                '--guarded-process-identity']
        with patch('sys.argv', argv), patch('sys.stderr', new_callable=io.StringIO) as stderr:
            with self.assertRaises(SystemExit) as error:
                main()
        self.assertEqual(error.exception.code, 2)
        self.assertIn('requires --session-mode guarded-x11', stderr.getvalue())


class FakeX:
    """Only X transport/platform setup is fake; bridge/owner/session are real."""
    def __init__(self, case):
        self.generation = 'a' * 64
        self.flip = False
        self.fail = False
        self.emissions, self.down, self.identity_queries = [], set(), 0
        backend = self.backend = object.__new__(_GuardedBackend)
        backend.targets = {'app':SimpleNamespace(id=20)}
        backend.d = SimpleNamespace(sync=lambda:None, query_keymap=self.keymap,
            get_input_focus=lambda:SimpleNamespace(focus=SimpleNamespace(id=20)),
            screen=lambda:SimpleNamespace(width_in_pixels=32, height_in_pixels=32))
        backend.root = SimpleNamespace(query_pointer=lambda:SimpleNamespace(mask=0))
        backend.geometry = lambda _target:dict(x=0,y=0,width=32,height=32)
        backend.preflight = lambda _program:None
        backend.focus = lambda _target:None
        backend._activation_supported = lambda:False
        backend._refresh_keyboard_mapping = lambda:False
        backend._keycode = {'CTRL':1, 'a':2}.__getitem__
        backend.held_keycodes, backend.held_buttons, backend.emissions = {}, set(), 0
        backend.observe_read_only = self.capture
        backend.close = Mock()
        image = Image.new('RGB', (32,32))
        for y in range(32):
            for x in range(32):
                image.putpixel((x,y), ((x*31)%256, (y*29)%256, (x*y)%256))
        self.raw = image.tobytes('raw','BGRX')
        for target, kwargs in [
            ('runtime.guarded_x11_v1.bridge._GuardedBackend', {'return_value':backend}),
            ('runtime.guarded_x11_v1.bridge.read_linux_x11_process_identity', {'side_effect':self.read}),
            ('runtime.backends.x11_v1.backend.xtest.fake_input', {'side_effect':self.emit})]:
            p = patch(target, **kwargs)
            result = p.start()
            if target.endswith('._GuardedBackend'):
                self.constructor = result
            case.addCleanup(p.stop)

    def read(self, _connection, _xid):
        self.identity_queries += 1
        if self.fail:
            raise RuntimeError('fake owner identity unavailable')
        return self.generation

    def capture(self, target, frame, region):
        artifact = self.backend.capture_artifacts.write(self.raw, 32,32,depth=24,
            bits_per_pixel=32,scanline_pad=32,byte_order=0,
            masks=(0xff0000,0xff00,0xff),true_color=True)
        return {'artifact':artifact,'sha256':hashlib.sha256(self.raw).hexdigest(),
                'width':32, 'height':32, 'capture_started_ns':time.monotonic_ns()}

    def keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code//8] |= 1 << (code%8)
        return bitmap

    def emit(self, _display, kind, code):
        self.emissions.append((kind,code))
        if kind == X.KeyPress:
            self.down.add(code)
            if self.flip and code == 1:
                self.generation = 'b' * 64
        elif kind == X.KeyRelease:
            self.down.discard(code)


class MCPIdentityTests(unittest.IsolatedAsyncioTestCase):
    async def ground(self, server):
        response = await server.call_tool('interface_guarded_observe', {})
        source = metadata(response)
        self.assertEqual(source['status'], 'observed', source)
        self.assertEqual(len(response.content), 2)
        minted = metadata(await server.call_tool('interface_guarded_mint', dict(
            alias='field', source_sequence=source['source']['sequence'],
            point=[8,8], region_size=[12,12])))
        self.assertEqual(minted['status'], 'minted', minted)
        return source, minted['offset']

    async def input(self, server, offset):
        return metadata(await server.call_tool('interface_guarded_input', dict(
            alias='field', offset=offset, interaction='keyboard', observe_after=False,
            tail=[{'op':'key_chord','keys':['CTRL','a']}])) )

    async def test_selected_identity_survives_delivery_retention_and_stable_input(self):
        fake = FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'app':20}, td, session_mode='guarded-x11', guarded_process_identity=True)
            try:
                source, offset = await self.ground(server)
                self.assertIs(source['session']['process_identity'], True)
                self.assertEqual(source['source']['pointer_binding']['process_generation'], 'a'*64)
                retained = json.loads((Path(source['call_directory'])/'report.json').read_text())
                self.assertEqual(retained['source'], source['source'])
                result = await self.input(server, offset)
                self.assertEqual(result['status'], 'completed', result)
                self.assertEqual([c for k,c in fake.emissions if k == X.KeyPress], [1,2])
                self.assertTrue(result['result']['execution']['releases'][-1]['verified'])
                self.assertEqual(fake.down, set())
                before = list(fake.emissions)
                lookup = await server.call_tool('interface_results', {'call_id':result['call_id']})
                self.assertEqual(metadata(lookup)['result'], result['result'])
                self.assertEqual(fake.emissions, before)
            finally:
                await server.call_tool('interface_close', {})
            fake.backend.close.assert_called_once()

    async def test_same_xid_changed_process_refuses_old_alias_through_mcp(self):
        fake = FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'app':20}, td, session_mode='guarded-x11', guarded_process_identity=True)
            try:
                _, offset = await self.ground(server)
                fake.generation = 'b'*64
                result = await self.input(server, offset)
                self.assertEqual(result['status'], 'refused', result)
                self.assertEqual(fake.emissions, [])
            finally:
                await server.call_tool('interface_close', {})

    async def test_change_after_modifier_releases_prefix_and_requires_review(self):
        fake = FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'app':20}, td, session_mode='guarded-x11', guarded_process_identity=True)
            try:
                _, offset = await self.ground(server)
                fake.flip = True
                result = await self.input(server, offset)
                self.assertEqual(result['status'], 'execution_failed', result)
                self.assertEqual(fake.emissions, [(X.KeyPress,1),(X.KeyRelease,1)])
                self.assertTrue(result['session']['review_required'])
                self.assertTrue(result['result']['execution']['releases'][-1]['verified'])
                self.assertEqual(fake.down, set())
                self.assertEqual((await self.input(server, offset))['status'], 'refused')
                self.assertEqual(fake.emissions, [(X.KeyPress,1),(X.KeyRelease,1)])
            finally:
                await server.call_tool('interface_close', {})

    async def test_default_mode_does_not_query_or_claim_process_identity(self):
        fake = FakeX(self)
        fake.fail = True
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'app':20}, td, session_mode='guarded-x11')
            try:
                source, offset = await self.ground(server)
                self.assertIs(source['session']['process_identity'], False)
                self.assertNotIn('process_generation', source['source']['pointer_binding'])
                self.assertEqual((await self.input(server, offset))['status'], 'completed')
                self.assertEqual(fake.identity_queries, 0)
            finally:
                await server.call_tool('interface_close', {})

    async def test_unavailable_identity_does_not_reopen_or_downgrade(self):
        fake = FakeX(self)
        fake.fail = True
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'app':20}, td, session_mode='guarded-x11', guarded_process_identity=True)
            try:
                for _ in range(2):
                    row = metadata(await server.call_tool('interface_guarded_observe', {}))
                    self.assertEqual(row['status'], 'refused', row)
                    self.assertTrue(row['session']['process_identity'])
                    self.assertTrue(row['session']['review_required'])
                fake.constructor.assert_called_once()
                before = fake.identity_queries
                response = await server.call_tool('interface_guarded_observe', {'process_identity':False})
                self.assertTrue(response.isError)
                refused = metadata(response)
                self.assertEqual(refused['status'], 'invalid_request')
                self.assertEqual(refused['unknown_arguments'], ['process_identity'])
                self.assertIs(refused['operation_invoked'], False)
                self.assertEqual(fake.identity_queries, before)
                self.assertEqual(fake.emissions, [])
            finally:
                await server.call_tool('interface_close', {})


if __name__ == '__main__':
    unittest.main()
