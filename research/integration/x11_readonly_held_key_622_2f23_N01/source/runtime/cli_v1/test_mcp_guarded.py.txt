"""Guarded transport/retention contracts, with an inert bridge fixture."""
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import sys
import unittest
from unittest.mock import Mock, patch
from runtime.cli_v1.mcp_server import create_server


class FakeBridge:
    def __init__(self, display, targets, target, directory):
        self.sequence=0;self.binding_revision=0;self.review_required=False
        self.directory=Path(directory);self.directory.mkdir()
        self.backend=SimpleNamespace(configure_capture_artifacts=self.configure,
            targets={target:SimpleNamespace(id=targets[target])},release_all=Mock(return_value={
                'verified':True,'keys_down':[],'buttons_down':[]}),close=Mock())
        self.session=SimpleNamespace(backend=self.backend,recovery_required=False)
        self.observe=Mock(side_effect=self.capture)
        self.mint=Mock(return_value=[12,7])
        self.click=Mock(side_effect=self.input)
        self.keyboard=Mock(side_effect=self.input)
        self.move=Mock(side_effect=self.input)
        self.review_window=Mock(return_value={'status':'needs_review','input_dispatched':False})

    def mint_reference(self, alias, source_sequence, point, *, region_size):
        return {'offset':self.mint(alias,source_sequence,point,region_size=region_size),
                'lifetime':{'clock':'time.monotonic_ns','minted_ns':1_000_000_000,
                    'expires_ns':301_000_000_000,'capture_freshness_ms':1500,
                    'authority_granted':False,'scope':'Same execution host clock; deadline does not grant input authority.'}}

    def configure(self, directory, *, retain_rgb=False):
        self.capture_directory=Path(directory);self.capture_directory.mkdir(parents=True,exist_ok=True)

    def capture(self):
        from PIL import Image
        self.sequence+=1
        image=self.capture_directory/(str(self.sequence)+'.png')
        Image.new('RGB',(32,32),'white').save(image)
        native={'sha256':'raw-fixture', 'capture_started_ns':1,
                'artifact':{'path':str(image),'mime_type':'image/png',
                    'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
                    'source_raw_sha256':'raw-fixture'}}
        return {'sequence':self.sequence,'observation_id':'fixture-'+str(self.sequence),
                'binding_revision':0,'capture_ns':1,'pointer_binding':{},'native':native}

    def input(self,*args,**kwargs):
        # The same worker must retain its request before reaching this boundary.
        request=json.loads((self.capture_directory.parent/'request.json').read_text())
        if request['operation']!='guarded_input':raise RuntimeError('request missing')
        return {'status':'completed','recovery_required':False,
                'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}


def metadata(response):
    return json.loads(response.content[0].text)


class GuardedMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_input_feedback_preserves_receipt_and_delivers_exact_cue_capture(self):
        for verdict in ('matched', 'pending', 'rejected', 'needs_review'):
            with self.subTest(verdict=verdict), tempfile.TemporaryDirectory() as td:
                opened=[]
                def fixture(*args):
                    bridge=FakeBridge(*args)
                    bridge.feedback=Mock(side_effect=lambda **kw: {
                        'status':verdict,'task_success':None,'authority_granted':False,
                        'input_dispatched':False,'samples':[{'title':'saved'}],
                        'observation':bridge.capture()})
                    opened.append(bridge); return bridge
                with patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=fixture):
                    server=create_server({'app':123},td,session_mode='guarded-x11')
                    reply=await server.call_tool('interface_guarded_input',dict(
                        alias='save',offset=[12,7],tail=[],feedback={
                            'expected_title':'saved','rejected_titles':['failed'],'timeout_ms':500}))
                    self.assertEqual(reply.isError,verdict!='matched')
                    row=metadata(reply); bridge=opened[0]
                    self.assertEqual(row['result']['status'],'completed')
                    self.assertEqual(row['status'],'completed' if verdict=='matched' else 'needs_review')
                    self.assertEqual(row['feedback']['status'],verdict)
                    self.assertEqual(row['source'],row['feedback']['observation'])
                    self.assertIsNone(row['task_success']); self.assertFalse(row['replay_allowed'])
                    bridge.click.assert_called_once(); bridge.observe.assert_not_called()
                    bridge.feedback.assert_called_once_with(expected_title='saved',rejected_titles=['failed'],timeout_ms=500)
                    bridge.mint.assert_not_called()
                    retained=await server.call_tool('interface_results',{'call_id':row['call_id']})
                    self.assertEqual(metadata(retained)['result'],row['result'])
                    self.assertEqual(retained.content[1].data,reply.content[1].data)
                    bridge.feedback.assert_called_once(); bridge.click.assert_called_once()
                    await server.call_tool('interface_close',{})

    async def test_input_feedback_never_waits_after_uncertain_input_or_release(self):
        cases=[{'status':'refused','input_dispatched':False},
            {'status':'execution_failed'},
            {'status':'completed','execution':{'releases':[]}},
            {'status':'completed','recovery_required':True,'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}},
            {'status':'completed','execution':{'releases':[{'verified':False,'keys_down':[],'buttons_down':[]}]}},
            {'status':'completed','execution':{'releases':[{'verified':True,'keys_down':['a'],'buttons_down':[]}]}}]
        for receipt in cases:
            with self.subTest(receipt=receipt), tempfile.TemporaryDirectory() as td:
                opened=[]
                def fixture(*args):
                    bridge=FakeBridge(*args); bridge.click=Mock(return_value=receipt)
                    bridge.feedback=Mock(); opened.append(bridge); return bridge
                with patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=fixture):
                    server=create_server({'app':123},td,session_mode='guarded-x11')
                    row=metadata(await server.call_tool('interface_guarded_input',dict(alias='save',offset=[12,7],tail=[],feedback={'expected_title':'saved'})))
                    self.assertEqual(row['result'],receipt)
                    self.assertEqual(row['feedback_status'],'cue_not_attempted')
                    self.assertEqual(row['status'],receipt['status'])
                    opened[0].feedback.assert_not_called(); opened[0].click.assert_called_once()
                    await server.call_tool('interface_close',{})

    async def test_feedback_exception_keeps_input_and_requires_review_without_replay(self):
        opened=[]
        def fixture(*args):
            bridge=FakeBridge(*args); bridge.feedback=Mock(side_effect=RuntimeError('cue persistence failed'))
            opened.append(bridge); return bridge
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=fixture):
            server=create_server({'app':123},td,session_mode='guarded-x11')
            row=metadata(await server.call_tool('interface_guarded_input',dict(alias='save',offset=[12,7],tail=[],feedback={'expected_title':'saved'})))
            self.assertEqual(row['result']['status'],'completed')
            self.assertEqual(row['status'],'needs_review')
            self.assertEqual(row['feedback_status'],'cue_failed')
            self.assertIn('cue persistence failed',row['feedback_error'])
            self.assertTrue(opened[0].review_required)
            opened[0].click.assert_called_once(); opened[0].observe.assert_not_called()
            await server.call_tool('interface_close',{})

    async def test_feedback_without_capture_refuses_before_open(self):
        from mcp.server.fastmcp.exceptions import ToolError
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge') as opened:
            server=create_server({'app':123},td,session_mode='guarded-x11')
            with self.assertRaises(ToolError):
                await server.call_tool('interface_guarded_input',dict(alias='save',offset=[12,7],tail=[],observe_after=False,feedback={'expected_title':'saved'}))
            opened.assert_not_called()

    async def test_invalid_feedback_refuses_before_open_or_input(self):
        from mcp.server.fastmcp.exceptions import ToolError
        for cue in ({'expected_title':''},{'expected_title':'saved','timeout_ms':10001},
                    {'expected_title':'saved','rejected_titles':['saved']},
                    {'expected_title':'saved','unknown':1}):
            with self.subTest(cue=cue), tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge') as opened:
                server=create_server({'app':123},td,session_mode='guarded-x11')
                with self.assertRaises(ToolError):
                    await server.call_tool('interface_guarded_input',dict(alias='save',offset=[12,7],tail=[],feedback=cue))
                opened.assert_not_called()

    async def test_requested_activation_review_returns_exact_image_without_edit(self):
        opened=[]
        def fixture(*args):
            bridge=FakeBridge(*args)
            bridge.activate_window=Mock(return_value={'status':'completed','execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}})
            def reviewed(window_id):
                bridge.binding_revision+=1
                return {'status':'reviewed','observation':bridge.capture()}
            bridge.review_window.side_effect=reviewed
            opened.append(bridge);return bridge
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=fixture):
            server=create_server({'app':123},td,session_mode='guarded-x11')
            reply=await server.call_tool('interface_guarded_activate_window',dict(window_id=123,source_sequence=1,current_binding_revision=0,expires_at_ns=5000,timeout_ms=300,review_after_activation=True))
            row=metadata(reply)
            self.assertEqual(row['status'],'reviewed')
            self.assertEqual(row['result']['status'],'completed')
            self.assertEqual(row['source'],row['review']['observation'])
            self.assertEqual(row['session']['binding_revision'],1)
            self.assertEqual(len(reply.content),2)
            lookup=await server.call_tool('interface_results',{'call_id':row['call_id']})
            self.assertEqual(reply.content[1].data,lookup.content[1].data)
            opened[0].activate_window.assert_called_once_with(window_id=123,source_sequence=1,current_binding_revision=0,expires_at_ns=5000,timeout_ms=300)
            opened[0].review_window.assert_called_once_with(123)
            opened[0].click.assert_not_called();opened[0].mint.assert_not_called()
            self.assertIsNone(row['task_success']);self.assertFalse(row['replay_allowed'])
            await server.call_tool('interface_close',{})

    async def test_requested_review_never_follows_failed_or_uncertain_activation(self):
        for result in [
            {'status':'refused','input_dispatched':False},
            {'status':'execution_failed'},
            {'status':'completed','execution':{'releases':[]}},
            {'status':'completed','execution':{'releases':[{'verified':False,'keys_down':[],'buttons_down':[]}]}},
            {'status':'completed','execution':{'releases':[{'verified':True,'keys_down':['a'],'buttons_down':[]}]}},
        ]:
            with self.subTest(result=result), tempfile.TemporaryDirectory() as td:
                opened=[]
                def fixture(*args):
                    bridge=FakeBridge(*args);bridge.activate_window=Mock(return_value=result)
                    opened.append(bridge);return bridge
                with patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=fixture):
                    server=create_server({'app':123},td,session_mode='guarded-x11')
                    reply=await server.call_tool('interface_guarded_activate_window',dict(window_id=123,source_sequence=1,current_binding_revision=0,expires_at_ns=5000,timeout_ms=300,review_after_activation=True))
                    row=metadata(reply)
                    self.assertEqual(row['feedback_status'],'review_not_attempted')
                    self.assertEqual(row['result'],result)
                    opened[0].review_window.assert_not_called();opened[0].observe.assert_not_called()
                    await server.call_tool('interface_close',{})

    async def test_failed_requested_review_preserves_completed_activation(self):
        opened=[]
        def fixture(*args):
            bridge=FakeBridge(*args)
            bridge.activate_window=Mock(return_value={'status':'completed','execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}})
            bridge.review_window.return_value={'status':'needs_review','error':'focus changed'}
            opened.append(bridge);return bridge
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=fixture):
            server=create_server({'app':123},td,session_mode='guarded-x11')
            row=metadata(await server.call_tool('interface_guarded_activate_window',dict(window_id=123,source_sequence=1,current_binding_revision=0,expires_at_ns=5000,timeout_ms=300,review_after_activation=True)))
            self.assertEqual(row['status'],'needs_review')
            self.assertEqual(row['result']['status'],'completed')
            self.assertNotIn('input_dispatched',row)
            self.assertNotIn('source',row)
            opened[0].activate_window.assert_called_once();opened[0].review_window.assert_called_once()
            await server.call_tool('interface_close',{})

    async def test_review_exception_retains_activation_without_retry_or_no_effect_claim(self):
        opened=[]
        def fixture(*args):
            bridge=FakeBridge(*args)
            bridge.activate_window=Mock(return_value={'status':'completed','execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}})
            bridge.review_window.side_effect=RuntimeError('review persistence failed')
            opened.append(bridge);return bridge
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=fixture):
            server=create_server({'app':123},td,session_mode='guarded-x11')
            row=metadata(await server.call_tool('interface_guarded_activate_window',dict(window_id=123,source_sequence=1,current_binding_revision=0,expires_at_ns=5000,timeout_ms=300,review_after_activation=True)))
            self.assertEqual(row['status'],'needs_review')
            self.assertEqual(row['result']['status'],'completed')
            self.assertNotIn('input_dispatched',row)
            self.assertIn('review persistence failed',row['review_error'])
            opened[0].activate_window.assert_called_once();opened[0].review_window.assert_called_once()
            self.assertTrue(opened[0].review_required)
            await server.call_tool('interface_close',{})

    async def test_explicit_activation_uses_retained_worker_without_edit_or_review(self):
        opened=[]
        def fixture(*args):
            bridge=FakeBridge(*args)
            bridge.activate_window=Mock(return_value={'status':'completed','execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}})
            opened.append(bridge);return bridge
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=fixture):
            server=create_server({'app':123},td,session_mode='guarded-x11')
            response=await server.call_tool('interface_guarded_activate_window',dict(window_id=123,source_sequence=1,current_binding_revision=0,expires_at_ns=5000,timeout_ms=300))
            row=metadata(response);self.assertEqual(row['status'],'completed')
            opened[0].activate_window.assert_called_once_with(window_id=123,source_sequence=1,current_binding_revision=0,expires_at_ns=5000,timeout_ms=300)
            opened[0].click.assert_not_called();opened[0].review_window.assert_not_called();opened[0].observe.assert_not_called()
            self.assertIsNone(row['task_success']);self.assertFalse(row['replay_allowed'])
            result=metadata(await server.call_tool('interface_results',{'call_id':row['call_id']}))
            self.assertEqual(result['result'],row['result']);self.assertFalse(result['operation_invoked'])
            opened[0].activate_window.assert_called_once()
            await server.call_tool('interface_close',{})

    async def test_minted_reference_deadline_is_retained_without_renewal(self):
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=FakeBridge):
            server=create_server({'app':123},td,session_mode='guarded-x11')
            response=await server.call_tool('interface_guarded_mint',{'alias':'field','source_sequence':1,'point':[20,20],'region_size':[24,14]})
            row=metadata(response)
            self.assertIn('lifetime',row,'public response omits finite reference deadline')
            self.assertEqual(row['lifetime']['expires_ns'],301_000_000_000)
            self.assertFalse(row['lifetime']['authority_granted']);self.assertFalse(row['input_dispatched'])
            lookup=metadata(await server.call_tool('interface_results',{'call_id':row['call_id'],'include_image':False}))
            self.assertEqual(lookup['lifetime'],row['lifetime'])
            self.assertFalse(lookup['operation_invoked'])
            many=metadata(await server.call_tool('interface_guarded_mint_many',{'source_sequence':1,'references':[{'alias':'save','point':[20,20],'region_size':[24,14]}]}))
            self.assertEqual(many['minted'][0]['lifetime'],row['lifetime'])
            self.assertEqual(many['minted'][0]['offset'],[12,7])
            await server.call_tool('interface_close',{})

    async def test_pointer_only_move_returns_fresh_image_without_click_or_keyboard(self):
        from mcp.server.fastmcp.exceptions import ToolError
        opened = []
        def fixture(*args):
            bridge = FakeBridge(*args); opened.append(bridge); return bridge
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge', side_effect=fixture):
            server = create_server({'app':123}, td, session_mode='guarded-x11')
            try:
                response = await server.call_tool('interface_guarded_input', {
                    'alias':'save', 'offset':[12,7], 'tail':[], 'interaction':'move'})
            except ToolError as error:
                self.fail('public guarded move must be supported: '+str(error))
            self.assertFalse(response.isError)
            self.assertEqual(metadata(response)['feedback_status'], 'captured')
            self.assertEqual(response.content[1].type, 'image')
            opened[0].move.assert_called_once_with('save', [12,7], tail=[])
            opened[0].click.assert_not_called()
            opened[0].keyboard.assert_not_called()
            request = json.loads(next(Path(td).glob('*/request.json')).read_text())
            self.assertEqual(request['arguments']['interaction'], 'move')
            await server.call_tool('interface_close', {})

    async def test_metadata_only_guarded_lookup_skips_encoding_and_preserves_capture(self):
        import base64
        with tempfile.TemporaryDirectory() as td:
            bridge = FakeBridge(None, {'app': 123}, 'app', Path(td)/'bridge')
            with patch('runtime.cli_v1.mcp_guarded.open_bridge', return_value=bridge):
                server = create_server({'app': 123}, td, session_mode='guarded-x11')
                original = await server.call_tool('interface_guarded_observe', {})
                before = metadata(original)
                call_id = before['call_id']
                raw_path = Path(td, call_id, 'report.json')
                saved_bytes = raw_path.read_bytes()
                with patch('runtime.cli_v1.review.base64.b64encode', wraps=base64.b64encode) as encode:
                    omitted = await server.call_tool('interface_results', {
                        'call_id': call_id, 'include_image': False})
                    self.assertEqual(encode.call_count, 0)
                row = metadata(omitted)
                self.assertEqual(len(omitted.content), 1)
                self.assertEqual(row['image_status'], before['image_status'])
                self.assertEqual(row['image_delivery'], 'omitted_by_request')
                self.assertEqual(row['source'], before['source'])
                self.assertEqual(row['observation_report'], before['observation_report'])
                self.assertIs(row['operation_invoked'], False)
                self.assertEqual(raw_path.read_bytes(), saved_bytes)
                included = await server.call_tool('interface_results', {'call_id': call_id})
                self.assertEqual(included.content[1].data, original.content[1].data)
                image_path = Path(before['source']['native']['artifact']['path'])
                image_path.write_bytes(image_path.read_bytes()+b'corruption')
                with patch('runtime.cli_v1.review.base64.b64encode', wraps=base64.b64encode) as encode:
                    corrupted = await server.call_tool('interface_results', {
                        'call_id': call_id, 'include_image': False})
                    self.assertEqual(encode.call_count, 0)
                self.assertEqual(metadata(corrupted)['image_status'], 'needs_review')
                self.assertIn('image_error', metadata(corrupted))
                self.assertEqual(raw_path.read_bytes(), saved_bytes)
                bridge.observe.assert_called_once()
                bridge.click.assert_not_called()
                bridge.keyboard.assert_not_called()
                await server.call_tool('interface_close', {})

    async def test_public_observation_keeps_current_rgb_across_capture_directory_changes(self):
        # Removing the guarded owner's retain_rgb policy must refuse the real
        # bridge observation, rather than silently pass an inert bridge fake.
        from PIL import Image
        from runtime.backends.x11_v1.backend import X11Backend
        from runtime.guarded_x11_v1.bridge import NativeHandleBridge
        import io
        import base64
        with tempfile.TemporaryDirectory() as td:
            bridge = object.__new__(NativeHandleBridge)
            bridge.out = Path(td)/'bridge'; bridge.out.mkdir()
            bridge.target = 'app'; bridge.sequence = 0
            bridge.binding_revision = 0; bridge.history = {}; bridge.review_required = False
            bridge._binding = lambda: {'focus':123, 'surface':123, 'geometry':[0,0,2,1]}
            backend = object.__new__(X11Backend)
            backend.targets = {'app':SimpleNamespace(id=123)}
            backend.d = SimpleNamespace(screen=lambda:SimpleNamespace(width_in_pixels=2,height_in_pixels=1))
            backend.release_all = lambda: {'verified':True,'keys_down':[],'buttons_down':[]}
            backend.close = lambda: None
            captures = []
            def capture(target, frame, region):
                raw = bytes([3,2,1,0,6,5,4,0])
                artifact = backend.capture_artifacts.write(raw, 2, 1, depth=24,
                    bits_per_pixel=32, scanline_pad=32, byte_order=0,
                    masks=(0xff0000,0xff00,0xff), true_color=True)
                captures.append(artifact)
                return {'artifact':artifact,'sha256':hashlib.sha256(raw).hexdigest(),'capture_started_ns':1}
            backend.observe_read_only = capture
            bridge.backend = backend
            bridge.session = SimpleNamespace(backend=backend,recovery_required=False)
            backend.configure_capture_artifacts(bridge.out/'images', retain_rgb=True)
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server = create_server({'app':123},td,session_mode='guarded-x11')
                try:
                    for sequence in (1,2):
                        response = await server.call_tool('interface_guarded_observe',{})
                        row = metadata(response)
                        self.assertEqual(row['status'],'observed',row)
                        self.assertEqual(row['source']['sequence'],sequence)
                        self.assertEqual(row['source']['image_source'],'exact_capture_rgb_handoff')
                        self.assertEqual(len(response.content),2)
                        with Image.open(io.BytesIO(base64.b64decode(response.content[1].data))) as image:
                            self.assertEqual(list(image.convert('RGB').getdata()),[(1,2,3),(4,5,6)])
                        self.assertEqual(list(bridge.history[sequence][1].getdata()),[(1,2,3),(4,5,6)])
                        self.assertEqual(Path(captures[-1]['path']).parent,Path(row['call_directory'])/'images')
                    self.assertNotEqual(Path(captures[0]['path']).parent,Path(captures[1]['path']).parent)
                    before = len(captures)
                    reread = await server.call_tool('interface_results',{'call_id':row['call_id']})
                    self.assertEqual(reread.content[1],response.content[1])
                    self.assertEqual(len(captures),before)
                finally:
                    await server.call_tool('interface_close',{})

    async def test_opt_in_observation_references_preserve_image_and_retained_full_view(self):
        from runtime.cli_v1.receipt_references import expand_guarded_observation
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            def capture():
                source=bridge.capture();source['native']['extension']='x'*800
                return source
            bridge.observe.side_effect=capture
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                response=await server.call_tool('interface_guarded_observe',{'observation_refs':True})
                row=metadata(response);self.assertIn('reference_schema',row)
                expanded=expand_guarded_observation(row)
                retained=await server.call_tool('interface_results',{'call_id':row['call_id']})
                full=metadata(retained);self.assertNotIn('reference_schema',full)
                self.assertEqual(full['source'],expanded['source'])
                self.assertEqual(full['observation_report'],expanded['observation_report'])
                self.assertEqual(response.content[1],retained.content[1])
                self.assertEqual(bridge.observe.call_count,1)
                await server.call_tool('interface_close',{})
                reread=metadata(await server.call_tool('interface_results',{'call_id':row['call_id'],'observation_refs':True}))
                self.assertFalse(reread['operation_invoked'])
                self.assertEqual(expand_guarded_observation(reread)['observation_report'],full['observation_report'])
                self.assertEqual(bridge.observe.call_count,1)
                bridge.click.assert_not_called();bridge.keyboard.assert_not_called()

    async def test_batch_mints_same_source_without_observe_or_input_and_retains_result(self):
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                refs=[{'alias':name,'point':[20,30],'region_size':[24,14]} for name in ('field','save')]
                response=await server.call_tool('interface_guarded_mint_many',{'source_sequence':7,'references':refs})
                row=metadata(response)
                self.assertEqual(row['status'],'minted')
                self.assertEqual([{'alias':r['alias'],'offset':r['offset']} for r in row['minted']],
                                 [{'alias':r['alias'],'offset':[12,7]} for r in refs])
                self.assertEqual(bridge.mint.call_args_list,[
                    unittest.mock.call('field',7,[20,30],region_size=(24,14)),
                    unittest.mock.call('save',7,[20,30],region_size=(24,14))])
                retained=metadata(await server.call_tool('interface_results',{'call_id':row['call_id']}))
                self.assertEqual(retained['minted'],row['minted'])
                self.assertFalse(retained['operation_invoked'])
                self.assertEqual(bridge.mint.call_count,2)
                bridge.observe.assert_not_called();bridge.click.assert_not_called();bridge.keyboard.assert_not_called()
                await server.call_tool('interface_close',{})

    async def test_batch_failure_preserves_success_and_stops_before_later_alias(self):
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            bridge.mint.side_effect=[[12,7],OSError('receipt write failed after possible registration')]
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                refs=[{'alias':name,'point':[20,30],'region_size':[24,14]} for name in ('field','save','later')]
                reply=await server.call_tool('interface_guarded_mint_many',{'source_sequence':7,'references':refs})
                row=metadata(reply)
                self.assertTrue(reply.isError);self.assertEqual(row['status'],'mint_incomplete')
                self.assertEqual([{'alias':r['alias'],'offset':r['offset']} for r in row['minted']],
                                 [{'alias':'field','offset':[12,7]}])
                self.assertEqual(row['failed_index'],1);self.assertEqual(row['failed_alias'],'save')
                self.assertEqual(row['failed_alias_state'],'unknown')
                self.assertEqual(row['unattempted_aliases'],['later'])
                self.assertFalse(row['input_dispatched']);self.assertFalse(row['replay_allowed'])
                self.assertEqual(bridge.mint.call_count,2)
                bridge.observe.assert_not_called();bridge.click.assert_not_called();bridge.keyboard.assert_not_called()
                await server.call_tool('interface_close',{})

    async def test_batch_duplicate_aliases_refuse_before_opening(self):
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge') as factory:
            server=create_server({'app':123},td,session_mode='guarded-x11')
            ref={'alias':'same','point':[20,30],'region_size':[24,14]}
            row=metadata(await server.call_tool('interface_guarded_mint_many',{'source_sequence':7,'references':[ref,ref]}))
            self.assertEqual(row['status'],'refused');self.assertEqual(row['minted'],[])
            factory.assert_not_called()

    async def test_batch_entire_schema_validated_before_any_mint(self):
        from mcp.server.fastmcp.exceptions import ToolError
        from copy import deepcopy
        valid={'alias':'field','point':[20,30],'region_size':[24,14]}
        bad=[]
        for key,value in [('alias','bad alias'),('point',[True,30]),('point',[20]),('region_size',[97,14]),('unknown',False)]:
            ref=deepcopy(valid);ref[key]=value;bad.append([valid,ref])
        bad.extend([[],[dict(valid,alias='x'+str(i)) for i in range(9)]])
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge') as factory:
            server=create_server({'app':123},td,session_mode='guarded-x11')
            for refs in bad:
                with self.subTest(refs=refs),self.assertRaises(ToolError):
                    await server.call_tool('interface_guarded_mint_many',{'source_sequence':7,'references':refs})
            factory.assert_not_called();self.assertEqual(list(Path(td).iterdir()),[])

    async def test_unknown_top_level_arguments_never_reach_bridge(self):
        opened=[]
        def open_fixture(*args,**kwargs):
            bridge=FakeBridge(*args,**kwargs);opened.append(bridge);return bridge
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge', side_effect=open_fixture) as factory:
            server=create_server({'app':123},td,session_mode='guarded-x11')
            for tool in await server.list_tools():
                self.assertIs(tool.inputSchema['additionalProperties'],False)
            refused=await server.call_tool('interface_guarded_input',{
                'alias':'browser_context','offset':[12,12],'tail':[], 'pointer':False})
            self.assertTrue(refused.isError)
            row=metadata(refused)
            self.assertEqual(row['unknown_arguments'],['pointer'])
            self.assertFalse(row['input_dispatched'])
            self.assertFalse(row['operation_invoked'])
            factory.assert_not_called()
            self.assertEqual(list(Path(td).iterdir()),[])
            await server.call_tool('interface_guarded_input',{
                'alias':'browser_context','offset':[12,12],'tail':[],'interaction':'keyboard'})
            factory.assert_called_once()
            opened[0].keyboard.assert_called_once()
            opened[0].click.assert_not_called()
            await server.call_tool('interface_close',{})

    async def test_explicit_mode_tools_shared_retention_and_no_replay(self):
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=FakeBridge) as factory:
            server=create_server({'app':123},td,session_mode='guarded-x11')
            names={tool.name for tool in await server.list_tools()}
            self.assertIn('interface_guarded_input',names)
            self.assertNotIn('interface_dispatch',names)
            self.assertNotIn('interface_inspect_target',names)
            factory.assert_not_called()
            initial=await server.call_tool('interface_guarded_observe',{})
            self.assertEqual(initial.content[1].type,'image')
            source=metadata(initial)['source']
            mint=metadata(await server.call_tool('interface_guarded_mint',{
                'alias':'save','source_sequence':source['sequence'],'point':[20,20],'region_size':[24,14]}))
            self.assertEqual(mint['offset'],[12,7])
            action=await server.call_tool('interface_guarded_input',{
                'alias':'save','offset':mint['offset'],'tail':[]})
            row=metadata(action);self.assertEqual(row['status'],'completed')
            self.assertIsNone(row['task_success']);self.assertFalse(row['replay_allowed'])
            raw=(Path(row['call_directory'])/'report.json').read_bytes()
            retained=await server.call_tool('interface_results',{'call_id':row['call_id']})
            self.assertEqual(retained.content[1].data,action.content[1].data)
            self.assertFalse(metadata(retained)['operation_invoked'])
            omitted=await server.call_tool('interface_results',{'call_id':row['call_id'],'include_image':False})
            self.assertEqual(len(omitted.content),1)
            self.assertEqual(metadata(omitted)['image_delivery'],'omitted_by_request')
            self.assertEqual((Path(row['call_directory'])/'report.json').read_bytes(),raw)
            factory.assert_called_once()
            closed=metadata(await server.call_tool('interface_close',{}))
            self.assertTrue(closed['release_attempted'])
            self.assertEqual(metadata(await server.call_tool('interface_guarded_observe',{}))['status'],'session_closed')
            after=await server.call_tool('interface_results',{'call_id':row['call_id']})
            self.assertEqual(after.content[1].data,action.content[1].data)

    async def test_capture_failure_keeps_completed_input_and_retained_failure(self):
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            bridge.observe.side_effect=OSError('capture failed')
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                reply=await server.call_tool('interface_guarded_input',{'alias':'x','offset':[1,2],'tail':[]})
                row=metadata(reply)
                self.assertTrue(reply.isError)
                self.assertEqual(row['result']['status'],'completed')
                self.assertEqual(row['feedback_status'],'observation_failed')
                self.assertNotIn('source',row);self.assertEqual(len(reply.content),1)
                again=metadata(await server.call_tool('interface_results',{'call_id':row['call_id']}))
                self.assertEqual(again['result'],row['result']);bridge.click.assert_called_once()
                await server.call_tool('interface_close',{})

    async def test_uncertain_input_error_is_retained_without_implicit_observation_or_retry(self):
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            bridge.click.side_effect=RuntimeError('delivery uncertain')
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                row=metadata(await server.call_tool('interface_guarded_input',{'alias':'x','offset':[1,2],'tail':[]}))
                self.assertEqual(row['effect_status'],'unknown')
                self.assertNotIn('input_dispatched',row)
                await server.call_tool('interface_results',{'call_id':row['call_id']})
                bridge.click.assert_called_once();bridge.observe.assert_not_called()
                await server.call_tool('interface_close',{})

    async def test_strict_schema_and_failed_initialization_do_not_reopen(self):
        with tempfile.TemporaryDirectory() as td, patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=OSError('display failed')) as factory:
            server=create_server({'app':123},td,session_mode='guarded-x11')
            with self.assertRaises(Exception):
                await server.call_tool('interface_guarded_mint',{'alias':'x','source_sequence':True,'point':[1,2],'region_size':[24,14]})
            factory.assert_not_called()
            row=metadata(await server.call_tool('interface_guarded_observe',{}))
            self.assertEqual(row['status'],'backend_unavailable')
            self.assertFalse(row['operation_invoked'])
            await server.call_tool('interface_guarded_observe',{})
            factory.assert_called_once()
            await server.call_tool('interface_close',{})
            with self.assertRaises(ValueError):create_server({'a':1,'b':2},td,session_mode='guarded-x11')

    async def test_busy_rejects_close_and_input_without_queueing(self):
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            entered=threading.Event();release=threading.Event()
            def blocked(*args,**kwargs):
                entered.set();release.wait(5);return bridge.input(*args,**kwargs)
            bridge.click.side_effect=blocked
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                args={'alias':'x','offset':[1,2],'tail':[],'observe_after':False}
                first=asyncio.create_task(server.call_tool('interface_guarded_input',args))
                try:
                    self.assertTrue(await asyncio.to_thread(entered.wait,3))
                    self.assertEqual(metadata(await server.call_tool('interface_close',{}))['status'],'busy')
                    self.assertEqual(metadata(await server.call_tool('interface_guarded_input',args))['status'],'busy')
                    bridge.backend.close.assert_not_called()
                finally:release.set()
                self.assertEqual(metadata(await first)['feedback_status'],'not_requested')
                bridge.click.assert_called_once()
                await server.call_tool('interface_close',{})
                bridge.backend.close.assert_called_once()

    async def test_real_stdio_discovery_input_image_retention_and_close(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        with tempfile.TemporaryDirectory() as td:
            code="""import sys
from unittest.mock import patch
from runtime.cli_v1.test_mcp_guarded import FakeBridge
from runtime.cli_v1.mcp_server import create_server
with patch('runtime.cli_v1.mcp_guarded.open_bridge',side_effect=FakeBridge):
    create_server({'app':123},sys.argv[1],session_mode='guarded-x11').run(transport='stdio')
"""
            params=StdioServerParameters(command=sys.executable,args=['-c',code,td],
                cwd=str(Path(__file__).resolve().parents[2]))
            async with stdio_client(params) as (reader,writer):
                async with ClientSession(reader,writer) as client:
                    await client.initialize()
                    self.assertIn('interface_guarded_input',{t.name for t in (await client.list_tools()).tools})
                    refused=await client.call_tool('interface_guarded_input',{
                        'alias':'x','offset':[1,2],'tail':[],'pointer':False})
                    self.assertTrue(refused.isError)
                    self.assertEqual(metadata(refused)['unknown_arguments'],['pointer'])
                    self.assertEqual(list(Path(td).iterdir()),[])
                    minted=await client.call_tool('interface_guarded_mint_many',{
                        'source_sequence':1,'references':[
                            {'alias':'field','point':[20,30],'region_size':[24,14]},
                            {'alias':'save','point':[40,30],'region_size':[24,14]}]})
                    self.assertEqual([{'alias':r['alias'],'offset':r['offset']} for r in metadata(minted)['minted']],[
                        {'alias':'field','offset':[12,7]},{'alias':'save','offset':[12,7]}])
                    action=await client.call_tool('interface_guarded_input',{'alias':'x','offset':[1,2],'tail':[]})
                    row=metadata(action);self.assertEqual(row['status'],'completed')
                    self.assertEqual(action.content[1].type,'image')
                    retained=await client.call_tool('interface_results',{'call_id':row['call_id']})
                    self.assertEqual(retained.content[1].data,action.content[1].data)
                    closed=metadata(await client.call_tool('interface_close',{}))
                    self.assertEqual(closed['status'],'closed')

    async def test_review_updates_binding_and_retains_the_exact_returned_image(self):
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            def reviewed(window_id):
                bridge.binding_revision+=1
                bridge.backend.targets['app'].id=window_id
                return {'status':'reviewed','observation':bridge.capture()}
            bridge.review_window.side_effect=reviewed
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                reply=await server.call_tool('interface_guarded_review_window',{'window_id':456})
                row=metadata(reply)
                self.assertEqual(row['status'],'reviewed')
                self.assertFalse(row['input_dispatched'])
                self.assertEqual(row['session']['targets'],{'app':456})
                self.assertEqual(row['session']['binding_revision'],1)
                self.assertEqual(row['source'],row['review']['observation'])
                again=await server.call_tool('interface_results',{'call_id':row['call_id']})
                self.assertEqual(reply.content[1].data,again.content[1].data)
                bridge.review_window.assert_called_once_with(456)
                bridge.click.assert_not_called();bridge.keyboard.assert_not_called()
                await server.call_tool('interface_close',{})

    async def test_malformed_mint_refuses_without_input_or_minting(self):
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                for point,size in [([1],[24,14]),([1,2],[3,14]),([1,2],[97,14]),([1,2],[24])]:
                    response=await server.call_tool('interface_guarded_mint',{
                        'alias':'x','source_sequence':1,'point':point,'region_size':size})
                    self.assertTrue(response.isError)
                    self.assertFalse(metadata(response)['input_dispatched'])
                bridge.mint.assert_not_called();bridge.click.assert_not_called()
                bridge.keyboard.assert_not_called();bridge.observe.assert_not_called()
                await server.call_tool('interface_close',{})
    async def test_brief_projection_preserves_full_retention_and_image_without_replay(self):
        from runtime.cli_v1.test_guarded_presentation import normal_report
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            bridge.click.side_effect=lambda *a,**k:normal_report()['result']
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                response=await server.call_tool('interface_guarded_input',{'alias':'x','offset':[1,2],'tail':[],'detail':'brief'})
                brief=metadata(response);self.assertEqual(brief['presentation']['returned'],'brief')
                raw_path=Path(brief['call_directory'])/'report.json';raw_before=raw_path.read_bytes()
                self.assertIn('guard_checks',json.loads(raw_before)['result'])
                full_reply=await server.call_tool('interface_results',{'call_id':brief['call_id'],'detail':'full'})
                full=metadata(full_reply)
                self.assertNotIn('presentation',full)
                self.assertEqual(full_reply.content[1].data,response.content[1].data)
                self.assertIn('guard_checks',full['result'])
                after=await server.call_tool('interface_results',{'call_id':brief['call_id'],'detail':'brief','include_image':False})
                self.assertEqual(metadata(after)['presentation']['returned'],'brief')
                self.assertEqual(len(after.content),1)
                self.assertEqual(raw_before,raw_path.read_bytes())
                bridge.click.assert_called_once();bridge.observe.assert_called_once()
                await server.call_tool('interface_close',{})

    async def test_brief_does_not_hide_report_persistence_failure(self):
        from runtime.cli_v1.test_guarded_presentation import normal_report
        from runtime.cli_v1.attempt import _write_json
        with tempfile.TemporaryDirectory() as td:
            bridge=FakeBridge(None,{'app':123},'app',Path(td)/'fixture')
            bridge.click.side_effect=lambda *a,**k:normal_report()['result']
            def write(path,value):
                if Path(path).name=='report.json':raise OSError('retained report unavailable')
                return _write_json(path,value)
            with patch('runtime.cli_v1.mcp_guarded.open_bridge',return_value=bridge),patch('runtime.cli_v1.mcp_server._write_json',side_effect=write):
                server=create_server({'app':123},td,session_mode='guarded-x11')
                response=await server.call_tool('interface_guarded_input',{'alias':'x','offset':[1,2],'tail':[],'detail':'brief'})
                row=metadata(response)
                self.assertTrue(response.isError);self.assertIn('persistence_error',row)
                self.assertEqual(row['presentation']['returned'],'full')
                self.assertIn('guard_checks',row['result'])
                self.assertEqual(row['result']['status'],'completed')
                bridge.click.assert_called_once()
            await server.call_tool('interface_close',{})


class PublicCompiledOwnerTests(unittest.TestCase):
    def owner(self, root):
        from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
        owner = GuardedSessionOwner({'app':7}, root, ':fixture')
        with patch('runtime.cli_v1.mcp_guarded.open_bridge', side_effect=FakeBridge):
            owner.get()
        owner.bridge.history = {}
        owner.bridge.configure(root/'previous-call/images', retain_rgb=True)
        return owner

    def callbacks(self):
        return {'perceive':lambda native,rgb:{}, 'verify_effect':lambda req,native,rgb:{}}

    def test_unopened_owner_is_not_implicitly_allocated(self):
        from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owner=GuardedSessionOwner({'app':7},root,':fixture')
            with patch('runtime.cli_v1.mcp_guarded.open_bridge') as opened:
                with self.assertRaises(RuntimeError):
                    owner.run_compiled({}, {}, call_root=root/'call', **self.callbacks())
                opened.assert_not_called()

    def test_final_image_uses_new_call_root_without_extra_observation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owner=self.owner(root);bridge=owner.bridge
            receipt={'outcome':'TASK_SUCCEEDED','observations':[{'sequence':1}]}
            def graph(actual,*args,**kwargs):
                self.assertIs(actual,bridge)
                native=bridge.capture();bridge.history[1]=(native,None)
                return receipt
            with patch('runtime.guarded_x11_v1.compiled.run',side_effect=graph) as run:
                row=owner.run_compiled({}, {}, call_root=root/'method', **self.callbacks())
            self.assertEqual(row['method_receipt'],receipt)
            self.assertIsNone(row['task_success']);self.assertFalse(row['replay_allowed'])
            self.assertEqual(row['feedback']['image_status'],'image')
            self.assertTrue(Path(row['feedback']['image_reference']['path']).is_relative_to(root/'method'))
            self.assertEqual(bridge.sequence,1);bridge.observe.assert_not_called();run.assert_called_once()

    def test_zero_observation_yield_does_not_present_previous_capture(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owner=self.owner(root);native=owner.bridge.capture();owner.bridge.history[1]=(native,None)
            with patch('runtime.guarded_x11_v1.compiled.run',return_value={'outcome':'SAFE_YIELD','observations':[]}):
                row=owner.run_compiled({}, {}, call_root=root/'method', **self.callbacks())
            self.assertIsNone(row['feedback']);self.assertEqual(owner.bridge.sequence,1)

    def test_exception_keeps_same_owner_cleanup_duty_and_never_replays(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owner=self.owner(root);bridge=owner.bridge
            with patch('runtime.guarded_x11_v1.compiled.run',side_effect=RuntimeError('after partial input')) as run:
                with self.assertRaises(RuntimeError):
                    owner.run_compiled({}, {}, call_root=root/'method', **self.callbacks())
            self.assertTrue(bridge.review_required);run.assert_called_once()
            close=owner.close();self.assertTrue(close['release']['verified']);bridge.backend.release_all.assert_called_once()
            with self.assertRaises(RuntimeError):
                owner.run_compiled({}, {}, call_root=root/'another', **self.callbacks())

    def test_presentation_failure_retains_method_result_and_requires_review(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owner=self.owner(root);bridge=owner.bridge
            receipt={'outcome':'TASK_SUCCEEDED','observations':[{'sequence':1}]}
            def graph(*args,**kwargs):
                native=bridge.capture();bridge.history[1]=(native,None);return receipt
            with patch('runtime.guarded_x11_v1.compiled.run',side_effect=graph), patch('runtime.cli_v1.review.present_result',side_effect=OSError('presentation unavailable')):
                row=owner.run_compiled({}, {}, call_root=root/'method', **self.callbacks())
            self.assertEqual(row['method_receipt'],receipt);self.assertTrue(bridge.review_required)
            self.assertEqual(row['feedback']['image_status'],'needs_review');self.assertFalse(row['replay_allowed'])

    def test_reused_call_directory_refuses_before_graph_execution(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owner=self.owner(root);(root/'method').mkdir()
            with patch('runtime.guarded_x11_v1.compiled.run') as run:
                with self.assertRaises(FileExistsError):
                    owner.run_compiled({}, {}, call_root=root/'method', **self.callbacks())
                run.assert_not_called()

    def test_review_or_recovery_requirement_is_not_reset(self):
        for reason in ('review','recovery'):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as td:
                root=Path(td);owner=self.owner(root)
                if reason=='review':owner.bridge.review_required=True
                else:owner.session.recovery_required=True
                with patch('runtime.guarded_x11_v1.compiled.run') as run:
                    with self.assertRaises(RuntimeError):
                        owner.run_compiled({}, {}, call_root=root/'method', **self.callbacks())
                    run.assert_not_called();self.assertFalse((root/'method').exists())

    def test_old_graph_sequence_cannot_deliver_unrelated_previous_image(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owner=self.owner(root);native=owner.bridge.capture();owner.bridge.history[1]=(native,None)
            receipt={'outcome':'SAFE_YIELD','observations':[{'sequence':1}]}
            with patch('runtime.guarded_x11_v1.compiled.run',return_value=receipt):
                row=owner.run_compiled({}, {}, call_root=root/'method', **self.callbacks())
            self.assertEqual(row['method_receipt'],receipt);self.assertTrue(owner.bridge.review_required)
            self.assertEqual(row['feedback']['image_status'],'needs_review');self.assertIsNone(row['feedback']['image'])


class InputDependencyOwnerTests(unittest.TestCase):
    def test_unopened_owner_cannot_register(self):
        from .mcp_guarded import GuardedSessionOwner
        with tempfile.TemporaryDirectory() as d:
            owner=GuardedSessionOwner({'app':1},d)
            with self.assertRaises(RuntimeError):
                with owner.input_guard('save',[0,0],tail=[{'op':'key_chord','keys':['CTRL','s']}],verify=lambda *a:True):pass
            self.assertIsNone(owner.bridge)

    def test_state_is_checked_at_context_entry(self):
        from .mcp_guarded import GuardedSessionOwner
        from contextlib import nullcontext
        owner=object.__new__(GuardedSessionOwner);owner.state='open';owner.session=object()
        owner.bridge=SimpleNamespace(input_guard=Mock(return_value=nullcontext()))
        context=owner.input_guard('save',[0,0],tail=[],verify=lambda *a:True)
        owner.state='closed'
        with self.assertRaises(RuntimeError):
            with context:pass
        owner.bridge.input_guard.assert_not_called()

    def test_open_owner_delegates_context_without_input_or_reopen(self):
        from .mcp_guarded import GuardedSessionOwner
        from contextlib import contextmanager
        entered=[]
        @contextmanager
        def guard(*args,**kwargs):
            entered.append('enter')
            try:yield
            finally:entered.append('exit')
        owner=object.__new__(GuardedSessionOwner);owner.state='open';owner.session=object()
        owner.bridge=SimpleNamespace(input_guard=Mock(side_effect=guard))
        verify=lambda *a:True;tail=[{'op':'key_chord','keys':['CTRL','s']}]
        with owner.input_guard('save',[0,0],tail=tail,verify=verify):self.assertEqual(entered,['enter'])
        self.assertEqual(entered,['enter','exit'])
        owner.bridge.input_guard.assert_called_once_with('save',[0,0],tail=tail,verify=verify)
