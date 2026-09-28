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
        self.review_window=Mock(return_value={'status':'needs_review','input_dispatched':False})

    def configure(self, directory):
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