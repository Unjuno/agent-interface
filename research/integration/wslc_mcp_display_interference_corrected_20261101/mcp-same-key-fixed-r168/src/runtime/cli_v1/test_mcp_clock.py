import json,time,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from runtime.cli_v1.mcp_server import create_server

class ExecutionClockTests(unittest.IsolatedAsyncioTestCase):
 async def test_clock_is_current_metadata_without_backend_or_lease(self):
  with tempfile.TemporaryDirectory() as td:
   server=create_server({'fixture':123},td,session_mode='persistent-x11')
   with patch('runtime.cli_v1.mcp_session.MCPSessionOwner.get',side_effect=AssertionError('must not open X11')):
    left=time.monotonic_ns();reply=await server.call_tool('interface_clock',{});right=time.monotonic_ns()
   self.assertFalse(reply.isError);row=json.loads(reply.content[0].text)
   self.assertLessEqual(left,row['monotonic_ns']);self.assertLessEqual(row['monotonic_ns'],right)
   self.assertIs(row['input_dispatched'],False);self.assertIs(row['authority_granted'],False);self.assertIs(row['lease_issued'],False)
   self.assertEqual(row['clock'],'time.monotonic_ns');self.assertEqual(len(row['server_instance_id']),32)
   self.assertEqual(list(Path(td).iterdir()),[])
 async def test_identity_is_stable_per_server_and_changes_on_replacement(self):
  with tempfile.TemporaryDirectory() as td:
   a=create_server({'fixture':123},td);b=create_server({'fixture':123},td)
   first=json.loads((await a.call_tool('interface_clock',{})).content[0].text)
   second=json.loads((await a.call_tool('interface_clock',{})).content[0].text)
   replacement=json.loads((await b.call_tool('interface_clock',{})).content[0].text)
   self.assertEqual(first['server_instance_id'],second['server_instance_id']);self.assertNotEqual(first['server_instance_id'],replacement['server_instance_id'])
   self.assertLessEqual(first['monotonic_ns'],second['monotonic_ns'])
 async def test_clock_accepts_no_authority_or_ttl_arguments(self):
  with tempfile.TemporaryDirectory() as td:
   server=create_server({'fixture':123},td)
   tools=await server.list_tools();schema=next(t.inputSchema for t in tools if t.name=='interface_clock')
   self.assertFalse(schema['additionalProperties']);self.assertEqual(schema.get('properties'),{})
   reply=await server.call_tool('interface_clock',{'ttl_ms':5000});self.assertTrue(reply.isError)
   self.assertFalse(json.loads(reply.content[0].text)['operation_invoked'])