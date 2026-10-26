import asyncio,io,json,os,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import AsyncMock,patch
from mcp.types import CallToolResult,ImageContent,TextContent
from runtime.cli_v1.mcp_relay import Relay,PUBLIC_TOOLS

class PublicRelayTests(unittest.IsolatedAsyncioTestCase):
    async def test_guarded_recovery_is_an_explicitly_forwardable_public_tool(self):
        client = AsyncMock(); relay = Relay(client)
        client.call_tool.return_value = CallToolResult(content=[])
        arguments = {'current_binding_revision': 7}
        row = await relay.request(json.dumps({'id':1,'tool':'interface_guarded_recover_input',
                                              'arguments':arguments}))
        self.assertEqual(row['status'], 'returned')
        client.call_tool.assert_awaited_once_with('interface_guarded_recover_input', arguments)

    async def test_unpaired_surrogates_refuse_before_sdk_and_keep_same_id(self):
        invalid = [
            {'text': chr(0xd800)}, {'text': chr(0xdfff)},
            {chr(0xd800): 'key'}, {'nested': [{chr(0xdc00): 'key'}]},
            {'nested': ['ok', {'text': chr(0xd800) + 'x' + chr(0xdc00)}]},
        ]
        for arguments in invalid:
            for as_bytes in [False, True]:
                with self.subTest(arguments=repr(arguments), as_bytes=as_bytes):
                    client = AsyncMock();relay = Relay(client)
                    client.call_tool.return_value = CallToolResult(content=[])
                    line = json.dumps({'id':1,'tool':'interface_validate','arguments':arguments})
                    response = await relay.request(line.encode('ascii') if as_bytes else line)
                    self.assertEqual(response['status'], 'refused')
                    self.assertEqual(response['next_id'], 1)
                    client.call_tool.assert_not_awaited()
                    valid = await relay.request(b'{"id":1,"tool":"interface_clock","arguments":{}}')
                    self.assertEqual((valid['status'],valid['next_id']), ('returned',2))
                    client.call_tool.assert_awaited_once_with('interface_clock',{})

    async def test_decoded_literal_surrogates_are_also_refused_before_sdk(self):
        client = AsyncMock();relay = Relay(client)
        client.call_tool.return_value = CallToolResult(content=[])
        response = await relay.request('{"id":1,"tool":"interface_validate","arguments":{"text":"' + chr(0xd800) + '"}}')
        self.assertEqual(response['status'], 'refused')
        self.assertEqual(response['next_id'], 1)
        client.call_tool.assert_not_awaited()

    async def test_unicode_scalars_pairs_and_literal_escape_text_keep_exact_meaning(self):
        arguments = {'text': '\x00' + chr(0xd7ff) + chr(0xe000) + chr(0xffff) + chr(0x10ffff),
                     'pair': chr(0x1f600), chr(0x1f600): ['日本語', '\\ud800']}
        for ensure_ascii in [True, False]:
            with self.subTest(ensure_ascii=ensure_ascii):
                client = AsyncMock();relay = Relay(client)
                client.call_tool.return_value = CallToolResult(content=[])
                line = json.dumps({'id':1,'tool':'interface_validate','arguments':arguments},ensure_ascii=ensure_ascii)
                response = await relay.request(line.encode('utf-8'))
                self.assertEqual((response['status'],response['next_id']), ('returned',2))
                client.call_tool.assert_awaited_once_with('interface_validate',arguments)

    async def test_serve_preserves_utf8_wire_despite_text_stream_encoding(self):
        from runtime.cli_v1 import mcp_relay as module
        duplicate = r'{"id":1,"tool":"interface_validate","arguments":{"program":{"\ud83d\ude00":1,"' + '\U0001f600' + '":2}}}' + '\n'
        arguments = {'program': {'text': '\u65e5\u672c\u8a9e\U0001f600', '\U0001f600': [1, '\u00e9']}}
        valid = json.dumps({'id':1,'tool':'interface_validate','arguments':arguments}, ensure_ascii=False) + '\n'
        invalid = b'{"id":2,"tool":"interface_clock","arguments":{"text":"\x80"}}\n'
        clock = b'{"id":2,"tool":"interface_clock","arguments":{}}\n'
        wire = (duplicate + valid).encode('utf-8') + invalid + clock
        for encoding in ['cp932', 'latin-1']:
            with self.subTest(encoding=encoding):
                client = AsyncMock()
                client.call_tool.return_value = CallToolResult(content=[TextContent(type='text',text='\u65e5\u672c\u8a9e\U0001f600')])
                context = AsyncMock()
                context.__aenter__.return_value = client
                transport = AsyncMock()
                transport.__aenter__.return_value = (object(), object())
                stdin = io.TextIOWrapper(io.BytesIO(wire), encoding=encoding, errors='strict')
                stdout = io.TextIOWrapper(io.BytesIO(), encoding=encoding, errors='strict')
                try:
                    with patch.object(module, 'stdio_client', return_value=transport), \
                         patch.object(module, 'ClientSession', return_value=context), \
                         patch.object(module.sys, 'stdin', stdin), patch.object(module.sys, 'stdout', stdout):
                        try:
                            await module.serve(['--explicit-mocked-server'])
                        except (UnicodeError, OSError) as error:
                            self.fail(f"relay did not preserve UTF-8 bytes through text wrappers: {error!r}")
                    stdout.flush()
                    rows = [json.loads(line) for line in stdout.buffer.getvalue().decode('utf-8').splitlines()]
                finally:
                    stdin.close()
                self.assertEqual(len(rows), 4)
                self.assertEqual(rows[0]['status'], 'refused')
                self.assertEqual(rows[0]['next_id'], 1)
                self.assertEqual((rows[1]['status'],rows[1]['next_id']), ('returned',2))
                self.assertEqual((rows[2]['status'],rows[2]['dispatched'],rows[2]['next_id']), ('refused',False,2))
                self.assertEqual((rows[3]['status'],rows[3]['next_id']), ('returned',3))
                self.assertEqual(rows[1]['result'], client.call_tool.return_value.model_dump(mode='json'))
                self.assertEqual(client.call_tool.await_count, 2)
                self.assertEqual(client.call_tool.await_args_list[0].args, ('interface_validate',arguments))
                self.assertEqual(client.call_tool.await_args_list[1].args, ('interface_clock',{}))

    async def test_bytes_require_utf8_before_dispatch_and_id_consumption(self):
        text = '{"id":1,"tool":"interface_clock","arguments":{}}'
        for wire in [text.encode('utf-16'), text.encode('utf-32'),
                     b'{"id":1,"tool":"interface_clock","arguments":{"text":"\x80"}}']:
            with self.subTest(wire_prefix=wire[:4]):
                client = AsyncMock();relay = Relay(client)
                client.call_tool.return_value = CallToolResult(content=[])
                row = await relay.request(wire)
                self.assertEqual(row['status'], 'refused')
                self.assertEqual(row['next_id'], 1)
                client.call_tool.assert_not_awaited()
                valid = await relay.request(text.encode('utf-8'))
                self.assertEqual((valid['status'],valid['next_id']), ('returned',2))
                client.call_tool.assert_awaited_once_with('interface_clock',{})

    async def test_unicode_bytes_keep_sdk_uncertainty_and_never_replay(self):
        client = AsyncMock();relay = Relay(client)
        client.call_tool.side_effect = OSError('distinct SDK failure after acceptance')
        arguments = {'text': '\u65e5\u672c\u8a9e\U0001f600', '\U0001f600': '\u00e9'}
        wire = json.dumps({'id':1,'tool':'interface_validate','arguments':arguments},ensure_ascii=False).encode('utf-8')
        row = await relay.request(wire)
        self.assertEqual((row['status'],row['next_id']), ('unknown_requires_reconciliation',2))
        client.call_tool.assert_awaited_once_with('interface_validate',arguments)
        repeated = await relay.request(wire)
        self.assertEqual((repeated['status'],repeated['dispatched'],repeated['next_id']), ('refused',False,2))
        bad = await relay.request(b'{"id":2,"tool":"interface_clock","arguments":{"text":"\x80"}}')
        self.assertEqual((bad['status'],bad['next_id']), ('refused',2))
        self.assertEqual(client.call_tool.await_count,1)

    async def test_serve_keeps_already_decoded_text_stream_compatibility(self):
        from runtime.cli_v1 import mcp_relay as module
        arguments = {'text': '\u65e5\u672c\u8a9e\U0001f600'}
        stdin = io.StringIO(json.dumps({'id':1,'tool':'interface_validate','arguments':arguments},ensure_ascii=False)+'\n')
        stdout = io.StringIO();client = AsyncMock()
        client.call_tool.return_value = CallToolResult(content=[])
        context = AsyncMock();context.__aenter__.return_value = client
        transport = AsyncMock();transport.__aenter__.return_value = (object(),object())
        with patch.object(module,'stdio_client',return_value=transport), \
             patch.object(module,'ClientSession',return_value=context), \
             patch.object(module.sys,'stdin',stdin),patch.object(module.sys,'stdout',stdout):
            await module.serve(['--explicit-mocked-server'])
        row = json.loads(stdout.getvalue())
        self.assertEqual((row['status'],row['next_id']), ('returned',2))
        client.call_tool.assert_awaited_once_with('interface_validate',arguments)

    async def test_cancel_is_dispatched_while_prior_stdout_write_is_blocked(self):
        from runtime.cli_v1 import mcp_relay as module

        output_entered=threading.Event();release_output=threading.Event()
        cancel_dispatched=threading.Event();read_lock=threading.Lock()
        lines=(b'{"id":1,"tool":"interface_guarded_compiled","arguments":{"wait_for_result_ms":10}}\n'
               b'{"id":2,"tool":"interface_cancel","arguments":{"call_id":"' + b'a'*32 + b'"}}\n')
        class TrackingInput:
            def __init__(self):
                self.stream=io.BytesIO(lines);self.read_count=0
            def readline(self):
                row=self.stream.readline()
                with read_lock:self.read_count+=1
                return row
            @property
            def buffer(self):return self
        class BlockingOutput:
            def __init__(self):self.writes=0
            @property
            def buffer(self):return self
            def write(self,row):
                self.writes+=1
                if self.writes==1:
                    output_entered.set()
                    if not release_output.wait(3):raise OSError('test output gate was not released')
                return len(row)
            def flush(self):pass
        class AsyncContext:
            def __init__(self,value):self.value=value
            async def __aenter__(self):return self.value
            async def __aexit__(self,*_args):return False
        class Client:
            def __init__(self):self.calls=[]
            async def initialize(self):pass
            async def call_tool(self,name,arguments):
                self.calls.append(name)
                if name=='interface_cancel':cancel_dispatched.set()
                return CallToolResult(content=[TextContent(type='text',text=name)])

        client=Client();stdin=TrackingInput();stdout=BlockingOutput();errors=[]
        transport=AsyncContext((object(),object()))
        client_context=AsyncContext(client)
        def run_server():
            try:asyncio.run(module.serve(['--mocked-server']))
            except BaseException as error:errors.append(error)
        server_thread=threading.Thread(target=run_server,daemon=True)
        with patch.object(module,'stdio_client',return_value=transport), \
             patch.object(module,'ClientSession',return_value=client_context), \
             patch.object(module.sys,'stdin',stdin),patch.object(module.sys,'stdout',stdout):
            server_thread.start()
            try:
                self.assertTrue(await asyncio.to_thread(output_entered.wait,2),
                                f'first response never reached blocked stdout; errors={errors!r}')
                self.assertTrue(await asyncio.to_thread(cancel_dispatched.wait,1),
                                'queued cancellation did not reach the MCP server while stdout was blocked')
            finally:
                release_output.set()
                await asyncio.to_thread(server_thread.join,2)
        self.assertFalse(server_thread.is_alive(),'relay did not finish after stdout resumed')
        self.assertEqual(errors,[])
        self.assertEqual(client.calls,['interface_guarded_compiled','interface_cancel'])

    async def test_pending_stdout_limit_reads_past_one_queued_ordinary_for_cancel(self):
        from runtime.cli_v1 import mcp_relay as module

        output_entered=threading.Event();release_output=threading.Event()
        cancel_dispatched=threading.Event();queued_ordinary_dispatched=threading.Event()
        cancel_calls=[]
        tail_dispatched=threading.Event();read_lock=threading.Lock()
        ordinary=[json.dumps({'id':i,'tool':'interface_guarded_compiled','arguments':{}}).encode()+b'\n'
                  for i in range(1,module.MAX_PENDING_STDOUT_RESPONSES+1)]
        queued_ordinary=(json.dumps({'id':len(ordinary)+1,'tool':'interface_guarded_compiled',
                                     'arguments':{'marker':'queued-before-cancel'}}).encode()+b'\n')
        cancel=(json.dumps({'id':len(ordinary)+2,'tool':'interface_cancel',
                            'arguments':{'call_id':'a'*32}}).encode()+b'\n')
        second_cancel=(json.dumps({'id':len(ordinary)+3,'tool':'interface_cancel',
                                   'arguments':{'call_id':'b'*32}}).encode()+b'\n')
        tail=(json.dumps({'id':len(ordinary)+4,'tool':'interface_guarded_compiled',
                          'arguments':{'marker':'tail'}}).encode()+b'\n')
        class TrackingInput:
            def __init__(self):
                self.stream=io.BytesIO(
                    b''.join(ordinary)+queued_ordinary+cancel+second_cancel+tail)
                self.read_count=0
            def readline(self):
                row=self.stream.readline()
                with read_lock:self.read_count+=1
                return row
            @property
            def buffer(self):return self
        class BlockingOutput:
            def __init__(self):self.writes=0
            @property
            def buffer(self):return self
            def write(self,row):
                self.writes+=1
                if self.writes==1:
                    output_entered.set()
                    if not release_output.wait(3):raise OSError('test output gate was not released')
                return len(row)
            def flush(self):pass
        class AsyncContext:
            def __init__(self,value):self.value=value
            async def __aenter__(self):return self.value
            async def __aexit__(self,*_args):return False
        class Client:
            def __init__(self):self.calls=[]
            async def initialize(self):pass
            async def call_tool(self,name,arguments):
                self.calls.append((name,arguments))
                if name=='interface_cancel':
                    cancel_calls.append(arguments['call_id'])
                    cancel_dispatched.set()
                if arguments.get('marker')=='queued-before-cancel':queued_ordinary_dispatched.set()
                if arguments.get('marker')=='tail':tail_dispatched.set()
                return CallToolResult(content=[TextContent(type='text',text=name)])

        client=Client();stdin=TrackingInput();stdout=BlockingOutput();errors=[]
        transport=AsyncContext((object(),object()));client_context=AsyncContext(client)
        def run_server():
            try:asyncio.run(module.serve(['--mocked-server']))
            except BaseException as error:errors.append(error)
        server_thread=threading.Thread(target=run_server,daemon=True)
        with patch.object(module,'stdio_client',return_value=transport), \
             patch.object(module,'ClientSession',return_value=client_context), \
             patch.object(module.sys,'stdin',stdin),patch.object(module.sys,'stdout',stdout):
            server_thread.start()
            try:
                self.assertTrue(await asyncio.to_thread(output_entered.wait,2),
                                'first response never reached the blocked stdout writer')
                deadline=asyncio.get_running_loop().time()+2
                while stdin.read_count<module.MAX_PENDING_STDOUT_RESPONSES and \
                        asyncio.get_running_loop().time()<deadline:
                    await asyncio.sleep(0.005)
                self.assertGreaterEqual(stdin.read_count,module.MAX_PENDING_STDOUT_RESPONSES,
                                        'relay did not reach its bounded pending-response limit')
                self.assertTrue(await asyncio.to_thread(cancel_dispatched.wait,1),
                                'cancellation behind one queued ordinary request was not dispatched')
                self.assertFalse(queued_ordinary_dispatched.is_set(),
                                 'ordinary request ahead of cancellation was dispatched first')
                self.assertEqual(stdin.read_count,
                                 module.MAX_PENDING_STDOUT_RESPONSES+2)
                self.assertEqual(cancel_calls,['a'*32],
                                 'more than one cancellation consumed the reserved slot')
                self.assertFalse(tail_dispatched.is_set(),
                                 'ordinary work consumed the reserved cancellation response slot')
            finally:
                release_output.set()
                await asyncio.to_thread(server_thread.join,2)
        self.assertFalse(server_thread.is_alive(),'relay did not finish after stdout resumed')
        self.assertEqual(errors,[])
        self.assertEqual(client.calls,
                         [('interface_guarded_compiled',{})]*module.MAX_PENDING_STDOUT_RESPONSES+
                         [('interface_cancel',{'call_id':'a'*32}),
                          ('interface_guarded_compiled',{'marker':'queued-before-cancel'}),
                          ('interface_cancel',{'call_id':'b'*32}),
                          ('interface_guarded_compiled',{'marker':'tail'})])
        self.assertTrue(tail_dispatched.is_set())

    async def test_cancel_response_writer_failure_stops_later_tool_dispatch(self):
        from runtime.cli_v1 import mcp_relay as module

        output_entered=threading.Event();release_output=threading.Event()
        cancel_dispatched=threading.Event();tail_dispatched=threading.Event()
        ordinary=[json.dumps({'id':i,'tool':'interface_guarded_compiled','arguments':{}}).encode()+b'\n'
                  for i in range(1,module.MAX_PENDING_STDOUT_RESPONSES+1)]
        cancel_id=len(ordinary)+1
        cancel=(json.dumps({'id':cancel_id,'tool':'interface_guarded_cancel',
                            'arguments':{'call_id':'a'*32}}).encode()+b'\n')
        tail=(json.dumps({'id':cancel_id+1,'tool':'interface_guarded_compiled',
                          'arguments':{'marker':'tail'}}).encode()+b'\n')

        class TrackingInput:
            def __init__(self):self.stream=io.BytesIO(b''.join(ordinary)+cancel+tail)
            def readline(self):return self.stream.readline()
            @property
            def buffer(self):return self
        class FailingOutput:
            def __init__(self):self.writes=0
            @property
            def buffer(self):return self
            def write(self,row):
                self.writes+=1
                response=json.loads(row)
                if self.writes==1:
                    output_entered.set()
                    if not release_output.wait(3):
                        raise OSError('test output gate was not released')
                if response.get('id')==cancel_id:
                    raise OSError('injected cancellation response write failure')
                return len(row)
            def flush(self):pass
        class AsyncContext:
            def __init__(self,value):self.value=value
            async def __aenter__(self):return self.value
            async def __aexit__(self,*_args):return False
        class Client:
            def __init__(self):self.calls=[]
            async def initialize(self):pass
            async def call_tool(self,name,arguments):
                self.calls.append((name,arguments))
                if name=='interface_guarded_cancel':cancel_dispatched.set()
                if arguments.get('marker')=='tail':tail_dispatched.set()
                return CallToolResult(content=[TextContent(type='text',text=name)])

        client=Client();stdin=TrackingInput();stdout=FailingOutput();errors=[]
        transport=AsyncContext((object(),object()));client_context=AsyncContext(client)
        def run_server():
            try:asyncio.run(module.serve(['--mocked-server']))
            except BaseException as error:errors.append(error)
        server_thread=threading.Thread(target=run_server,daemon=True)
        with patch.object(module,'stdio_client',return_value=transport), \
             patch.object(module,'ClientSession',return_value=client_context), \
             patch.object(module.sys,'stdin',stdin),patch.object(module.sys,'stdout',stdout):
            server_thread.start()
            try:
                self.assertTrue(await asyncio.to_thread(output_entered.wait,2))
                self.assertTrue(await asyncio.to_thread(cancel_dispatched.wait,1),
                                'saturated relay did not dispatch cancellation')
            finally:
                release_output.set()
                await asyncio.to_thread(server_thread.join,2)
        self.assertFalse(server_thread.is_alive(),'relay did not stop after writer failure')
        self.assertEqual(len(errors),1,errors)
        self.assertIsInstance(errors[0],OSError)
        self.assertIn('injected cancellation response write failure',str(errors[0]))
        self.assertFalse(tail_dispatched.is_set(),client.calls)
        self.assertNotIn(('interface_guarded_compiled',{'marker':'tail'}),client.calls)

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

    async def test_duplicate_json_keys_refuse_before_dispatch_and_id_consumption(self):
        lines=[
            '{"id":0,"id":1,"tool":"interface_dispatch","arguments":{}}',
            '{"id":1,"id":1,"tool":"interface_dispatch","arguments":{}}',
            '{"id":1,"tool":"interface_close","tool":"interface_dispatch","arguments":{}}',
            '{"id":1,"tool":"interface_dispatch","arguments":{"first":1},"arguments":{}}',
            '{"id":1,"tool":"interface_dispatch","arguments":{"program":{"ops":[{"op":"key_state","key":"x","down":false,"down":true}]}}}',
            r'{"\u0069d":0,"id":1,"tool":"interface_dispatch","arguments":{}}',
            r'{"id":1,"tool":"interface_dispatch","arguments":{"key":false,"\u006bey":true}}',
            '{"id":1,"tool":"interface_dispatch","arguments":{"flag":null,"flag":true}}',
        ]
        for line in lines:
            with self.subTest(line=line):
                client=AsyncMock();relay=Relay(client)
                client.call_tool.return_value=CallToolResult(content=[])
                row=await relay.request(line)
                self.assertEqual(row['status'],'refused')
                self.assertFalse(row['dispatched'])
                self.assertEqual(row['next_id'],1)
                client.call_tool.assert_not_awaited();client.list_tools.assert_not_awaited()
                valid=await relay.request('{"id":1,"tool":"interface_dispatch","arguments":{}}')
                self.assertEqual(valid['status'],'returned')
                self.assertEqual(valid['next_id'],2)
                client.call_tool.assert_awaited_once_with('interface_dispatch',{})

    async def test_equal_keys_in_distinct_objects_and_distinct_case_remain_valid(self):
        client=AsyncMock();relay=Relay(client)
        client.call_tool.return_value=CallToolResult(content=[])
        arguments={'key':1,'Key':2,'nested':{'key':3},'array':[{'key':4},{'key':5}],
                   'text':'"key":0,"key":1'}
        row=await relay.request(json.dumps({'id':1,'tool':'interface_dispatch','arguments':arguments}))
        self.assertEqual(row['status'],'returned')
        client.call_tool.assert_awaited_once_with('interface_dispatch',arguments)

    async def test_excessive_json_nesting_refuses_without_dispatch_or_id_consumption(self):
        for value in ('['*10000+'0'+']'*10000,
                      '{"key":'*10000+'0'+'}'*10000):
            with self.subTest(container=value[0]):
                client=AsyncMock();relay=Relay(client)
                client.call_tool.return_value=CallToolResult(content=[])
                line='{"id":1,"tool":"interface_dispatch","arguments":{"value":'+value+'}}'
                try:
                    row=await relay.request(line)
                except RecursionError as error:
                    self.fail(f"deep JSON escaped relay admission: {error}")
                self.assertEqual(row['status'],'refused')
                self.assertFalse(row['dispatched'])
                self.assertEqual(row['next_id'],1)
                client.call_tool.assert_not_awaited();client.list_tools.assert_not_awaited()
                valid=await relay.request('{"id":1,"tool":"interface_dispatch","arguments":{}}')
                self.assertEqual(valid['status'],'returned')
                self.assertEqual(valid['next_id'],2)
                client.call_tool.assert_awaited_once_with('interface_dispatch',{})

    async def test_decoder_recursion_after_acceptance_preserves_current_id(self):
        client=AsyncMock();relay=Relay(client)
        client.call_tool.return_value=CallToolResult(content=[])
        accepted=await relay.request('{"id":1,"tool":"interface_dispatch","arguments":{}}')
        self.assertEqual(accepted['status'],'returned')
        value='['*10000+'0'+']'*10000
        try:
            row=await relay.request('{"id":2,"tool":"interface_dispatch","arguments":{"value":'+value+'}}')
        except RecursionError as error:
            self.fail(f"deep JSON escaped relay admission after a prior accepted id: {error}")
        self.assertEqual(row['status'],'refused')
        self.assertFalse(row['dispatched'])
        self.assertEqual(row['next_id'],2)
        self.assertEqual(client.call_tool.await_count,1)
        valid=await relay.request('{"id":2,"tool":"interface_dispatch","arguments":{}}')
        self.assertEqual(valid['status'],'returned')
        self.assertEqual(valid['next_id'],3)
        self.assertEqual(client.call_tool.await_count,2)

    async def test_moderately_nested_json_preserves_forwarded_values(self):
        client=AsyncMock();relay=Relay(client)
        client.call_tool.return_value=CallToolResult(content=[])
        array=0;obj=0
        for _ in range(32):
            array=[array];obj={'key':obj}
        arguments={'array':array,'object':obj}
        row=await relay.request(json.dumps({'id':1,'tool':'interface_dispatch',
                                           'arguments':arguments}))
        self.assertEqual(row['status'],'returned')
        client.call_tool.assert_awaited_once_with('interface_dispatch',arguments)

    async def test_legacy_public_protocol_parity_without_changing_research(self):
        from research.live_control.native_mcp_relay_v1 import Relay as Legacy,PUBLIC_TOOLS as LEGACY_TOOLS
        self.assertEqual(tuple(t for t in PUBLIC_TOOLS if t not in {
            'interface_clock', 'interface_guarded_activate_window', 'interface_guarded_recover_input',
            'interface_guarded_cancel','interface_guarded_compiled'}),
            LEGACY_TOOLS)
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
            duplicate='{"id":1,"id":1,"tool":"list_tools","arguments":{}}\n'
            deep_value='['*10000+'0'+']'*10000
            deep='{"id":1,"tool":"interface_validate","arguments":{"program":{"value":'+deep_value+'}}}\n'
            lines=json.dumps(requests[0])+'\n'+overflow+duplicate+deep+''.join(json.dumps(r)+'\n' for r in requests[1:])
            stdout,stderr=await asyncio.wait_for(process.communicate(lines.encode()),30)
            self.assertEqual(process.returncode,0,stderr.decode())
            rows=[json.loads(line) for line in stdout.splitlines()]
            self.assertEqual(len(rows),7)
            self.assertEqual(rows[0]['status'],'refused');self.assertFalse(rows[0]['dispatched'])
            self.assertEqual(rows[1]['status'],'refused');self.assertFalse(rows[1]['dispatched'])
            self.assertEqual(rows[1]['next_id'],1)
            self.assertEqual(rows[2]['status'],'refused');self.assertFalse(rows[2]['dispatched'])
            self.assertEqual(rows[2]['next_id'],1)
            self.assertEqual(rows[3]['status'],'refused');self.assertFalse(rows[3]['dispatched'])
            self.assertEqual(rows[3]['next_id'],1)
            names={t['name'] for t in rows[4]['result']['tools']}
            self.assertIn('interface_dispatch',names);self.assertFalse(any(n.startswith('native_') for n in names))
            self.assertLessEqual(names,set(PUBLIC_TOOLS))
            self.assertEqual(rows[4]['status'],'returned')
            validation=json.loads(rows[5]['result']['content'][0]['text'])
            self.assertFalse(validation['static_valid'])
            close=json.loads(rows[6]['result']['content'][0]['text'])
            self.assertEqual(close['status'],'closed');self.assertFalse(close['connection_close_attempted'])

if __name__=='__main__':unittest.main()
