"""Packaged guarded MCP rejects a changed target before explicit reacquisition."""
import asyncio
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
           all(importlib.util.find_spec(name) is not None for name in ('mcp','Xlib','PIL')))


@unittest.skipUnless(ENABLED, 'requires explicitly enabled private Xvfb and optional MCP/Xlib/Pillow')
class PackagedGuardedMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_changed_pixels_refuse_before_input_then_fresh_alias_saves_once(self):
        from Xlib import display
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        checkout=Path(__file__).resolve().parents[2]
        fixture=Path(__file__).with_name('x11_editor_fixture.py')
        with tempfile.TemporaryDirectory(prefix='packaged-guarded-x11-') as temp:
            root=Path(temp);archive=root/'runtime.pyz'
            build(checkout,archive,root/'manifest.json',root/'sums')
            stderr=(root/'app.stderr').open('wb')
            app=subprocess.Popen([sys.executable,str(fixture),str(root),'textured'],
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=stderr)
            try:
                deadline=time.monotonic()+5
                while not (root/'app-ready.json').exists():
                    if app.poll() is not None or time.monotonic()>=deadline:
                        self.fail('synthetic editor did not become ready')
                    await asyncio.sleep(.02)
                ready=json.loads((root/'app-ready.json').read_text())
                targets=root/'targets.json';targets.write_text(json.dumps({'fixture':ready['window_id']}))
                env={k:os.environ[k] for k in ('PATH','HOME','DISPLAY','XAUTHORITY','LANG') if k in os.environ}
                params=StdioServerParameters(command=sys.executable,args=[str(archive),'mcp',
                    '--targets',str(targets),'--output-directory',str(root/'output'),
                    '--session-mode','guarded-x11','--guarded-process-identity',
                    '--guarded-query-worker','--guarded-window-lifecycle','--guarded-owned-process'],env=env)
                async with stdio_client(params) as (reader,writer):
                    async with ClientSession(reader,writer) as client:
                        await client.initialize()
                        async def invoke(name,args):
                            result=await asyncio.wait_for(client.call_tool(name,args),20)
                            self.assertTrue(result.content)
                            self.assertEqual(result.content[0].type,'text')
                            return result,json.loads(result.content[0].text)
                        async def observe():
                            response,row=await invoke('interface_guarded_observe',{})
                            self.assertFalse(response.isError)
                            self.assertEqual(row['status'],'observed')
                            self.assertTrue(any(x.type=='image' for x in response.content))
                            return row['source']
                        async def mint(alias,sequence):
                            response,row=await invoke('interface_guarded_mint',{'alias':alias,
                                'source_sequence':sequence,'point':[68,68],'region_size':[24,24]})
                            self.assertFalse(response.isError,row)
                            self.assertEqual(row['status'],'minted',row)
                            return row
                        async def action(alias,offset):
                            return await invoke('interface_guarded_input',{'alias':alias,'offset':offset,
                                'interaction':'keyboard','observe_after':False,
                                'tail':[{'op':'text','text':'agent'},{'op':'key_chord','keys':['CTRL','S']}]})
                        original=await observe();old=await mint('old',original['sequence'])
                        painter=display.Display()
                        try:
                            window=painter.create_resource_object('window',ready['window_id'])
                            gc=window.create_gc(foreground=0)
                            try:
                                window.fill_rectangle(gc,36,36,24,24);painter.sync()
                                response,refused=await action('old',old['offset'])
                                self.assertTrue(response.isError,refused)
                                self.assertEqual(refused['status'],'refused')
                                self.assertFalse(refused['result']['input_dispatched'])
                                self.assertTrue(any(x.get('stage')=='before_admission' and
                                    x.get('status')=='MISSING' and x.get('reason')=='region_pixels_missing'
                                    for x in refused['result']['guard_checks']))
                                await asyncio.sleep(.2)
                                self.assertFalse((root/'saved.txt').exists())
                                self.assertEqual((root/'app-events.jsonl').read_text().strip(),'')
                                window.fill_rectangle(gc,0,0,300,150);gc.change(foreground=0xffffff)
                                for y in range(10):
                                    for x in range(18):
                                        if (x+y)%2==0:window.fill_rectangle(gc,x*16,y*16,16,16)
                                painter.sync()
                            finally:
                                gc.free()
                        finally:
                            painter.close()
                        fresh=await observe()
                        self.assertGreater(fresh['sequence'],original['sequence'])
                        new=await mint('new',fresh['sequence'])
                        response,completed=await action('new',new['offset'])
                        self.assertFalse(response.isError,completed)
                        self.assertEqual(completed['status'],'completed')
                        execution=completed['result']['execution']
                        self.assertEqual(execution['completed_ops'],[0,1,2,3])
                        release=execution['releases'][-1]
                        self.assertTrue(release['verified'])
                        self.assertEqual(release['keys_down'],[])
                        self.assertEqual(release['buttons_down'],[])
                        deadline=time.monotonic()+3;events=[]
                        while True:
                            if (root/'app-events.jsonl').exists():
                                try:events=[json.loads(line) for line in (root/'app-events.jsonl').read_text().splitlines()]
                                except json.JSONDecodeError:events=[]
                            if (root/'saved.txt').exists() and any(e.get('effect')=='saved' for e in events):break
                            if app.poll() is not None or time.monotonic()>=deadline:self.fail('application did not save')
                            await asyncio.sleep(.02)
                        self.assertEqual((root/'saved.txt').read_bytes(),b'agent')
                        self.assertEqual(''.join(e['keysym'] for e in events if e.get('effect')=='typed'),'agent')
                        self.assertEqual(sum(e.get('effect')=='saved' for e in events),1)
                        response,closed=await invoke('interface_close',{})
                        self.assertFalse(response.isError,closed)
                        self.assertTrue(closed['verified'])
                        self.assertTrue(closed['owner_process_retired'])
                        self.assertEqual(closed['owner_process_exitcode'],0)
            finally:
                app.terminate()
                try:app.wait(timeout=3)
                except subprocess.TimeoutExpired:app.kill();app.wait(timeout=3)
                stderr.close()


if __name__=='__main__':unittest.main()
