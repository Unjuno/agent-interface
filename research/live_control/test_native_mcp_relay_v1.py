import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock

from mcp.types import CallToolResult, ImageContent, TextContent
from native_mcp_relay_v1 import Relay


class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_relay_pending_resume_then_second_stage(self):
        # Inert file-exchange fixture: verifies transport composition, not GUI effects.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            pixels=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=')
            (root/'frame.png').write_bytes(pixels)
            source={'sequence':1,'capture_ns':123,'native':{'sha256':'raw',
                'capture_started_ns':123,'artifact':{'path':str(root/'frame.png'),
                'sha256':hashlib.sha256(pixels).hexdigest(),'source_raw_sha256':'raw','mime_type':'image/png'}}}
            (root/'source-1.json').write_text(json.dumps(source))
            process=await asyncio.create_subprocess_exec(sys.executable,
                str(Path(__file__).with_name('native_mcp_relay_v1.py')),'--','--run-directory',tmp,
                stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,env=dict(os.environ))
            async def request(identifier,tool,arguments):
                process.stdin.write((json.dumps({'id':identifier,'tool':tool,'arguments':arguments})+'\n').encode())
                await process.stdin.drain()
                row=json.loads(await asyncio.wait_for(process.stdout.readline(),timeout=10))
                self.assertEqual(row['id'],identifier)
                return row['result']
            try:
                pending=await request(1,'native_submit',{'stage':1,'decision':{
                    'source_sequence':1,'point':[1,1],'expected_title':'fixture'},'timeout':0})
                metadata=json.loads(pending['content'][0]['text'])
                self.assertEqual(metadata['status'],'pending')
                original=(root/'request-1.json').read_bytes()
                before=(root/'request-1.json').stat().st_mtime_ns
                digest=metadata['decision_sha256']
                second=dict(source,sequence=2)
                (root/'source-2.json').write_text(json.dumps(second))
                (root/'reply-1.json').write_text(json.dumps({'stage':1,'status':'boundary',
                    'decision_sha256':digest,'observation':second}))
                resumed=await request(2,'native_resume',{'stage':1,'decision_sha256':digest,'timeout':0})
                self.assertTrue(json.loads(resumed['content'][0]['text'])['exchange']['resumed_read_only'])
                self.assertEqual(base64.b64decode(resumed['content'][1]['data']),pixels)
                self.assertEqual((root/'request-1.json').read_bytes(),original)
                self.assertEqual((root/'request-1.json').stat().st_mtime_ns,before)
                next_pending=await request(3,'native_submit',{'stage':2,'decision':{'source_sequence':2,'finish':True},'timeout':0})
                next_meta=json.loads(next_pending['content'][0]['text'])
                self.assertEqual(next_meta['status'],'pending')
                (root/'reply-2.json').write_text(json.dumps({'stage':2,'status':'finished',
                    'decision_sha256':next_meta['decision_sha256'],'observation':second,
                    'evaluation':{'success':False}}))
                final=await request(4,'native_resume',{'stage':2,'decision_sha256':next_meta['decision_sha256'],'timeout':0})
                self.assertFalse(json.loads(final['content'][0]['text'])['outcome_summary']['evaluation_success'])
                self.assertEqual(len(list(root.glob('request-*.json'))),2)
                self.assertEqual((root/'request-1.json').read_bytes(),original)
            finally:
                process.stdin.close()
                try:
                    await asyncio.wait_for(process.wait(),timeout=10)
                except asyncio.TimeoutError:
                    process.kill(); await process.wait()
            self.assertEqual(process.returncode,0)

    @unittest.skipUnless(hasattr(os, 'openpty'), 'Linux PTY regression')
    async def test_terminal_output_refuses_before_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            master,slave=os.openpty()
            try:
                path=Path(tmp)/'allocation'
                process=await asyncio.create_subprocess_exec(sys.executable,
                    str(Path(__file__).with_name('native_mcp_relay_v1.py')),'--',
                    '--allocation-directory',str(path),'--app','inkscape',
                    stdin=asyncio.subprocess.DEVNULL,stdout=slave,stderr=asyncio.subprocess.PIPE)
                _,stderr=await asyncio.wait_for(process.communicate(),timeout=10)
                self.assertEqual(process.returncode,2)
                self.assertIn(b'not a terminal',stderr)
                self.assertFalse(path.exists())
            finally:
                os.close(master); os.close(slave)

    async def test_exact_content_and_duplicate_refusal(self):
        result = CallToolResult(content=[TextContent(type='text',text='{"status":"pending"}'),
            ImageContent(type='image',data='YWJj',mimeType='image/png')])
        client = AsyncMock()
        client.call_tool.return_value = result
        relay = Relay(client)
        line=json.dumps({'id':1,'tool':'native_submit','arguments':{'decision':{'extension':[1,2]}}})
        response=await relay.request(line)
        self.assertEqual(response['result'], result.model_dump(mode='json'))
        self.assertLessEqual(response['sdk_entry_ns'],response['sdk_return_ns'])
        self.assertEqual((await relay.request(line))['status'],'refused')
        client.call_tool.assert_awaited_once_with('native_submit',{'decision':{'extension':[1,2]}})

    async def test_ambiguous_failure_consumes_id_without_retry(self):
        client=AsyncMock()
        client.call_tool.side_effect=OSError('transport lost')
        relay=Relay(client)
        line='{"id":1,"tool":"native_submit","arguments":{}}'
        self.assertEqual((await relay.request(line))['status'],'unknown_requires_reconciliation')
        self.assertEqual((await relay.request(line))['status'],'refused')
        self.assertEqual(client.call_tool.await_count,1)

    async def test_bad_envelopes_never_dispatch(self):
        client=AsyncMock(); relay=Relay(client)
        for line in ['{','[]','{"id":true,"tool":"native_start","arguments":{}}',
                     '{"id":1,"tool":"native_start","arguments":{"timeout":NaN}}',
                     '{"id":1,"tool":"other","arguments":{}}']:
            self.assertEqual((await relay.request(line))['status'],'refused')
        client.call_tool.assert_not_awaited()
        self.assertEqual(relay.next_id,1)

    async def test_real_stdio_pipeline_keeps_one_managed_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'allocation'
            process=await asyncio.create_subprocess_exec(sys.executable,
                str(Path(__file__).with_name('native_mcp_relay_v1.py')),'--',
                '--allocation-directory',str(path),'--app','inkscape',
                '--harness-python',str(Path(tmp)/'missing'),
                stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,env=dict(os.environ))
            requests=[{'id':1,'tool':'list_tools','arguments':{}},
                      {'id':2,'tool':'native_start','arguments':{'timeout':0}},
                      {'id':3,'tool':'native_start','arguments':{'timeout':0}}]
            stdout,stderr=await asyncio.wait_for(process.communicate(
                ''.join(json.dumps(r)+'\n' for r in requests).encode()),timeout=20)
            self.assertEqual(process.returncode,0,stderr.decode())
            rows=[json.loads(line) for line in stdout.splitlines()]
            self.assertEqual([r['id'] for r in rows],[1,2,3])
            self.assertIn('native_start',{t['name'] for t in rows[0]['result']['tools']})
            first=json.loads(rows[1]['result']['content'][0]['text'])['allocation']
            second=json.loads(rows[2]['result']['content'][0]['text'])['allocation']
            self.assertEqual(first,second)
            self.assertEqual(first['status'],'needs_review')
            self.assertTrue((path/'launch.json').exists())
            self.assertFalse((path/'run').exists())


if __name__ == '__main__':
    unittest.main()
