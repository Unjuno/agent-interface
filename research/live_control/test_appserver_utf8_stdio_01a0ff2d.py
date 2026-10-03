"""Native binary-peer regressions for explicit UTF-8 protocol text."""
import json,subprocess,sys,unittest
from codex_app_server_client_v2 import AppServerError,CodexAppServerClient

PEER='''import json,sys
request=json.loads(sys.stdin.buffer.readline().decode("utf-8"))
reply=(json.dumps({"id":request["id"],"result":{"label":"caf\\u00e9 \\u6771\\u4eac"}},ensure_ascii=False)+"\\n").encode("utf-8") if sys.argv[1]=="valid" else b'{"id":1,"result":{"label":"\\x80"}}\\n'
sys.stdout.buffer.write(reply);sys.stdout.buffer.flush()
sys.stderr.buffer.write(b"\\xff\\x00diagnostic\\n");sys.stderr.buffer.flush()
'''

class UTF8StdioTests(unittest.TestCase):
 def exercise(self,kind):
  client=CodexAppServerClient([sys.executable,'-B','-c',PEER,kind]);self.addCleanup(self.cleanup,client)
  if kind=='valid':self.assertEqual(client.request('fixture/test',{},timeout=2),{'label':'caf\u00e9 \u6771\u4eac'})
  else:
   with self.assertRaises(AppServerError):client.request('fixture/test',{},timeout=2)
  self.assertEqual(client.process.wait(timeout=2),0);client.close(timeout=1);self.assertEqual(client._pending,set());self.assertEqual(client._responses,{});self.assertFalse(client._reader.is_alive());self.assertFalse(client._stderr_reader.is_alive());self.assertEqual(client.stderr_snapshot(),{'tail':b'\xff\x00diagnostic\n','bytes_received':13,'complete':True,'error':None})
 def cleanup(self,client):
  client.close(timeout=1)
  for stream in [client.process.stdin,client.process.stdout,client.process.stderr]:stream.close()
 def test_nonascii_utf8_reply_preserved(self):self.exercise('valid')
 def test_invalid_utf8_reply_cannot_complete_request(self):self.exercise('invalid')
