"""Packaged MCP expiry and explicit continuation on an owned synthetic X11 target."""
import asyncio
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from runtime.distribution_v2.build import build

ENABLED = (sys.platform.startswith('linux') and
           os.environ.get('AGENT_INTERFACE_PACKAGED_MCP_XVFB_TEST') == '1' and
           bool(os.environ.get('DISPLAY')) and
           all(importlib.util.find_spec(name) is not None for name in ('mcp', 'Xlib', 'PIL')))


@unittest.skipUnless(ENABLED, 'requires explicitly enabled private Xvfb and optional MCP/Xlib/Pillow')
class PackagedMCPX11Tests(unittest.IsolatedAsyncioTestCase):
    async def test_expiry_then_explicit_suffix_saves_exact_effect(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        checkout = Path(__file__).resolve().parents[2]
        fixture = Path(__file__).with_name('x11_editor_fixture.py')
        with tempfile.TemporaryDirectory(prefix='packaged-mcp-x11-') as temp:
            root = Path(temp)
            archive = root/'runtime.pyz'
            build(checkout, archive, root/'manifest.json', root/'sums')
            stderr = (root/'app.stderr').open('wb')
            app = subprocess.Popen([sys.executable, str(fixture), str(root)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=stderr)
            try:
                deadline = time.monotonic() + 5
                while not (root/'app-ready.json').exists():
                    if app.poll() is not None:
                        self.fail('synthetic editor exited before readiness')
                    if time.monotonic() >= deadline:
                        self.fail('synthetic editor readiness timed out')
                    await asyncio.sleep(.02)
                ready = json.loads((root/'app-ready.json').read_text(encoding='utf-8'))
                targets = root/'targets.json'
                targets.write_text(json.dumps({'fixture':ready['window_id']}), encoding='utf-8')
                env = {key:os.environ[key] for key in ('PATH','HOME','DISPLAY','XAUTHORITY','LANG') if key in os.environ}
                params = StdioServerParameters(command=sys.executable, args=[str(archive), 'mcp',
                    '--targets',str(targets),'--output-directory',str(root/'output'),
                    '--session-mode','one-shot'], env=env)
                async with stdio_client(params) as (reader, writer):
                    async with ClientSession(reader, writer) as client:
                        await client.initialize()
                        async def invoke(name, args):
                            response = await client.call_tool(name, args)
                            self.assertTrue(response.content)
                            self.assertEqual(response.content[0].type, 'text')
                            return response, json.loads(response.content[0].text)
                        async def observe():
                            response, meta = await invoke('interface_observe', {'target':'fixture',
                                'frame':'window_client','region':[0,0,300,150]})
                            self.assertFalse(response.isError)
                            image = next(block for block in response.content if block.type == 'image')
                            self.assertEqual(hashlib.sha256(base64.b64decode(image.data)).hexdigest(),
                                             meta['image_reference']['sha256'])
                            return meta['receipt']['source']['raw_report']['observation']
                        async def clock():
                            response, meta = await invoke('interface_clock', {})
                            self.assertFalse(response.isError)
                            return meta['monotonic_ns']
                        def program(identifier, sequence, expiry, ops):
                            return {'schema':'agent-interface/program-v1','program_id':identifier,
                                'source':{'observation_seq':sequence,'binding_revision':1},
                                'authority':{'lease_id':identifier,'expires_at_ns':expiry},
                                'terminal':{'release_all_required':True},'ops':ops}
                        async def dispatch(value, sequence):
                            _, meta = await invoke('interface_dispatch', {'program':value,
                                'current_observation_seq':sequence,'current_binding_revision':1})
                            return meta['receipt']['source']['raw_report']['result']
                        await observe()
                        first = program('expire',1,(await clock())+1_000_000_000,[
                            {'op':'focus','target':'fixture'},{'op':'text','text':'pre'},
                            {'op':'wait_update','timeout_ms':1500},{'op':'text','text':'bad'},
                            {'op':'key_chord','keys':['CTRL','S']},{'op':'release_all'}])
                        a = await dispatch(first,1)
                        x = a['execution']
                        self.assertEqual(a['status'],'execution_failed')
                        self.assertEqual(x['completed_ops'],[0,1])
                        self.assertEqual(x['failed_op'],2)
                        self.assertIn('LEASE_EXPIRED_DURING_EXECUTION',x['error'])
                        self.assertTrue(x['releases'][-1]['verified'])
                        self.assertEqual(x['releases'][-1]['keys_down'],[])
                        self.assertEqual(x['releases'][-1]['buttons_down'],[])
                        self.assertFalse(a['recovery_required'])
                        self.assertFalse((root/'saved.txt').exists())
                        new_observation = await observe()
                        second = program('continue',2,(await clock())+5_000_000_000,[
                            {'op':'focus','target':'fixture'},{'op':'text','text':'fix'},
                            {'op':'key_chord','keys':['CTRL','S']},{'op':'release_all'}])
                        b = await dispatch(second,2)
                        y = b['execution']
                        self.assertEqual(b['status'],'completed')
                        self.assertEqual(y['completed_ops'],[0,1,2,3])
                        self.assertTrue(y['releases'][-1]['verified'])
                        self.assertEqual(y['releases'][-1]['keys_down'],[])
                        self.assertEqual(y['releases'][-1]['buttons_down'],[])
                        self.assertLessEqual(x['releases'][-1]['monotonic_ns'],new_observation['capture_started_ns'])
                        self.assertLessEqual(new_observation['capture_ended_ns'],y['started_ns'])
                        deadline = time.monotonic()+3
                        events = []
                        while True:
                            event_file = root/'app-events.jsonl'
                            if event_file.exists():
                                try:
                                    events = [json.loads(line) for line in event_file.read_text().splitlines()]
                                except json.JSONDecodeError:
                                    events = []
                            if (root/'saved.txt').exists() and any(e.get('effect')=='saved' for e in events):
                                break
                            if app.poll() is not None or time.monotonic() >= deadline:
                                self.fail('synthetic editor did not save and publish its event')
                            await asyncio.sleep(.02)
                        self.assertEqual((root/'saved.txt').read_bytes(),b'prefix')
                        self.assertEqual(''.join(e['keysym'] for e in events if e.get('effect')=='typed'),'prefix')
                        self.assertEqual(sum(e.get('effect')=='saved' for e in events),1)
            finally:
                app.terminate()
                try:
                    app.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    app.kill();app.wait(timeout=3)
                stderr.close()


if __name__ == '__main__':
    unittest.main()
