import asyncio
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
