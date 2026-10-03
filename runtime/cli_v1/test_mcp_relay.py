import asyncio,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import AsyncMock
from mcp.types import CallToolResult,ImageContent,TextContent
from runtime.cli_v1.mcp_relay import Relay,PUBLIC_TOOLS

class PublicRelayTests(unittest.IsolatedAsyncioTestCase):
    async def test_exact_content_duplicate_and_ambiguous_failure(self):
        client=AsyncMock()
        result=CallToolResult(content=[TextContent(type='text',text='{"status":"completed"}'),ImageContent(type='image',data='YWJj',mimeType='image/png')])
        client.call_tool.return_value=result
        relay=Relay(client)
        line=json.dumps({'id':1,'tool':'interface_dispatch','arguments':{'program':{'extension':[1,2]}}})
        response=await relay.request(line)
        self.assertEqual(response['result'],result.model_dump(mode='json'))
        self.assertLessEqual(response['sdk_entry_ns'],response['sdk_return_ns'])
        self.assertEqual((await relay.request(line))['status'],'refused')
        client.call_tool.assert_awaited_once()
        client.call_tool.side_effect=OSError('transport lost')
        ambiguous=json.dumps({'id':2,'tool':'interface_dispatch','arguments':{}})
        self.assertEqual((await relay.request(ambiguous))['status'],'unknown_requires_reconciliation')
        self.assertEqual((await relay.request(ambiguous))['status'],'refused')
        self.assertEqual(client.call_tool.await_count,2)

    async def test_bad_envelopes_and_native_tools_never_dispatch(self):
        client=AsyncMock();relay=Relay(client)
        for line in ['{','[]','{"id":true,"tool":"interface_close","arguments":{}}',
                     '{"id":1,"tool":"interface_dispatch","arguments":{"value":NaN}}',
                     '{"id":1,"tool":"native_start","arguments":{}}',
                     '{"id":1,"tool":"list_tools","arguments":{"extra":1}}']:
            with self.subTest(line=line):
                row=await relay.request(line)
                self.assertEqual(row['status'],'refused');self.assertFalse(row['dispatched'])
        client.call_tool.assert_not_awaited();client.list_tools.assert_not_awaited()
        self.assertEqual(relay.next_id,1)

    async def test_overflowing_json_numbers_refuse_before_consuming_id(self):
        for value in ['1e400','-1e400','1.7976931348623159e308',
                      '[0,{"nested":1e400}]']:
            with self.subTest(value=value):
                client=AsyncMock();relay=Relay(client)
                client.call_tool.return_value=CallToolResult(content=[])
                line='{"id":1,"tool":"interface_dispatch","arguments":{"value":'+value+'}}'
                row=await relay.request(line)
                self.assertEqual(row['status'],'refused')
                self.assertFalse(row['dispatched'])
                self.assertEqual(row['next_id'],1)
                client.call_tool.assert_not_awaited()
                valid=await relay.request('{"id":1,"tool":"interface_dispatch","arguments":{}}')
                self.assertEqual(valid['status'],'returned')
                self.assertEqual(valid['next_id'],2)

    async def test_finite_json_numbers_and_number_strings_remain_unchanged(self):
        client=AsyncMock();relay=Relay(client)
        client.call_tool.return_value=CallToolResult(content=[])
        arguments={'values':[1e308,-1e308,5e-324,0.0,2**64],
                   'text':['1e400','NaN','Infinity']}
        row=await relay.request(json.dumps({'id':1,'tool':'interface_dispatch',
                                           'arguments':arguments}))
        self.assertEqual(row['status'],'returned')
        client.call_tool.assert_awaited_once_with('interface_dispatch',arguments)

    async def test_legacy_public_protocol_parity_without_changing_research(self):
        from research.live_control.native_mcp_relay_v1 import Relay as Legacy,PUBLIC_TOOLS as LEGACY_TOOLS
        self.assertEqual(tuple(t for t in PUBLIC_TOOLS if t not in {'interface_clock', 'interface_guarded_activate_window'}),LEGACY_TOOLS)
        result=CallToolResult(content=[TextContent(type='text',text='{"status":"pending"}')])
        a,b=AsyncMock(),AsyncMock();a.call_tool.return_value=b.call_tool.return_value=result
        public,legacy=Relay(a),Legacy(b,tools=LEGACY_TOOLS)
        for request in [{'id':1,'tool':'native_start','arguments':{}},
                        {'id':1,'tool':'interface_dispatch','arguments':{}},
                        {'id':1,'tool':'interface_dispatch','arguments':{}},
                        {'id':2,'tool':'interface_close','arguments':{}}]:
            rows=[await r.request(json.dumps(request)) for r in (public,legacy)]
            for row in rows:
                row.pop('sdk_entry_ns',None);row.pop('sdk_return_ns',None)
            self.assertEqual(rows[0],rows[1])

    async def test_portable_relay_outside_checkout_lists_validates_and_closes(self):
        from runtime.distribution_v2.build import build
        repo=Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);archive=root/'runtime.pyz'
            build(repo,archive,root/'manifest.json',root/'SHA256SUMS')
            (root/'targets.json').write_text('{"app":123}')
            env=dict(os.environ);env.pop('PYTHONPATH',None)
            process=await asyncio.create_subprocess_exec(sys.executable,'-I',str(archive),'relay','--',
                '--targets',str(root/'targets.json'),'--output-directory',str(root/'calls'),
                '--session-mode','persistent-x11',cwd=root,env=env,
                stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            requests=[{'id':1,'tool':'native_start','arguments':{}},
                      {'id':1,'tool':'list_tools','arguments':{}},
                      {'id':2,'tool':'interface_validate','arguments':{'program':{}}},
                      {'id':3,'tool':'interface_close','arguments':{}}]
            overflow='{"id":1,"tool":"interface_validate","arguments":{"program":{"value":1e400}}}\n'
            lines=json.dumps(requests[0])+'\n'+overflow+''.join(json.dumps(r)+'\n' for r in requests[1:])
            stdout,stderr=await asyncio.wait_for(process.communicate(lines.encode()),30)
            self.assertEqual(process.returncode,0,stderr.decode())
            rows=[json.loads(line) for line in stdout.splitlines()]
            self.assertEqual(len(rows),5)
            self.assertEqual(rows[0]['status'],'refused');self.assertFalse(rows[0]['dispatched'])
            self.assertEqual(rows[1]['status'],'refused');self.assertFalse(rows[1]['dispatched'])
            self.assertEqual(rows[1]['next_id'],1)
            names={t['name'] for t in rows[2]['result']['tools']}
            self.assertIn('interface_dispatch',names);self.assertFalse(any(n.startswith('native_') for n in names))
            self.assertLessEqual(names,set(PUBLIC_TOOLS))
            self.assertEqual(rows[3]['status'],'returned')
            validation=json.loads(rows[3]['result']['content'][0]['text'])
            self.assertFalse(validation['static_valid'])
            close=json.loads(rows[4]['result']['content'][0]['text'])
            self.assertEqual(close['status'],'closed');self.assertFalse(close['connection_close_attempted'])

if __name__=='__main__':unittest.main()
