import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from native_exchange_v1 import encoded


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_observe_submit_pending_resume_and_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pixels = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=')
            (root/'frame.png').write_bytes(pixels)
            source = {'sequence':1, 'capture_ns':123, 'native':{
                'sha256':'raw', 'capture_started_ns':123, 'artifact':{
                    'path':str(root/'frame.png'), 'sha256':hashlib.sha256(pixels).hexdigest(),
                    'source_raw_sha256':'raw','mime_type':'image/png'}}}
            (root/'source-1.json').write_bytes(encoded(source))
            parameters = StdioServerParameters(command=sys.executable, args=[
                str(Path(__file__).with_name('native_mcp_v1.py')), '--run-directory', tmp], env=dict(os.environ))
            async with stdio_client(parameters) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    listed = await client.list_tools()
                    self.assertEqual({t.name for t in listed.tools}, {'native_observe','native_submit','native_resume'})
                    observed = await client.call_tool('native_observe', {'stage':1})
                    self.assertFalse(observed.isError)
                    self.assertEqual([b.type for b in observed.content], ['text','image'])
                    self.assertEqual(base64.b64decode(observed.content[1].data), pixels)
                    self.assertNotIn('"data":', observed.content[0].text)
                    invalid = await client.call_tool('native_submit', {'stage':True,'decision':{},'timeout':0})
                    self.assertTrue(invalid.isError)
                    self.assertFalse((root/'request-1.json').exists())
                    decision = {'source_sequence':1,'finish':True}
                    pending = await client.call_tool('native_submit', {'stage':1,'decision':decision,'timeout':0})
                    row = json.loads(pending.content[0].text)
                    self.assertEqual(row['status'],'pending')
                    raw = (root/'request-1.json').read_bytes()
                    before = (root/'request-1.json').stat().st_mtime_ns
                    duplicate = await client.call_tool('native_submit', {'stage':1,'decision':decision,'timeout':0})
                    self.assertTrue(duplicate.isError)
                    self.assertIsNone(json.loads(duplicate.content[0].text)['program_attempted'])
                    wrong = await client.call_tool('native_resume', {'stage':1,'decision_sha256':'0'*64,'timeout':0})
                    self.assertTrue(wrong.isError)
                    (root/'reply-1.json').write_bytes(encoded({'stage':1,'status':'finished',
                        'decision_sha256':row['decision_sha256'], 'evaluation':{'success':False},
                        'observation':source}))
                    resumed = await client.call_tool('native_resume', {'stage':1,'decision_sha256':row['decision_sha256'],'timeout':0})
                    self.assertFalse(resumed.isError)
                    result = json.loads(resumed.content[0].text)
                    self.assertTrue(result['exchange']['resumed_read_only'])
                    self.assertFalse(result['outcome_summary']['evaluation_success'])
                    self.assertEqual(base64.b64decode(resumed.content[1].data),pixels)
                    self.assertEqual((root/'request-1.json').read_bytes(),raw)
                    self.assertEqual((root/'request-1.json').stat().st_mtime_ns,before)


if __name__ == '__main__':
    unittest.main()
