import json, subprocess, sys, time, unittest
from pathlib import Path
ROOT=Path(__file__).parent
class T(unittest.TestCase):
 def server(self):
  return subprocess.Popen([sys.executable,"-S","-B",str(ROOT/"server.py"),"--offset-ns","5000000000"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 def ask(self,p,row):
  p.stdin.write(json.dumps(row)+"\n");p.stdin.flush();return json.loads(p.stdout.readline())
 def tear(self,p):
  try:self.ask(p,{"cmd":"shutdown"})
  finally:
   p.wait(timeout=2)
   for stream in (p.stdin,p.stdout,p.stderr):
    if stream is not None: stream.close()
 def test_token_wrong_request(self):
  p=self.server();t=self.ask(p,{"cmd":"issue_token","request_id":"a","generation":1,"ttl_ns":160000000,"inbound_ms":0,"processing_ms":0,"outbound_ms":0});r=self.ask(p,{"cmd":"activate_token","request_id":"b","generation":1,"token_id":t["token_id"],"activation_window_ns":250000000});self.assertEqual(r["reason"],"WRONG_REQUEST");self.tear(p)
 def test_token_wrong_generation(self):
  p=self.server();t=self.ask(p,{"cmd":"issue_token","request_id":"a","generation":1,"ttl_ns":160000000,"inbound_ms":0,"processing_ms":0,"outbound_ms":0});r=self.ask(p,{"cmd":"activate_token","request_id":"a","generation":2,"token_id":t["token_id"],"activation_window_ns":250000000});self.assertEqual(r["reason"],"WRONG_GENERATION");self.tear(p)
 def test_token_unknown(self):
  p=self.server();r=self.ask(p,{"cmd":"activate_token","request_id":"a","generation":1,"token_id":"0"*32,"activation_window_ns":250000000});self.assertEqual(r["reason"],"UNKNOWN_TOKEN");self.tear(p)
 def test_token_replay(self):
  p=self.server();t=self.ask(p,{"cmd":"issue_token","request_id":"a","generation":1,"ttl_ns":160000000,"inbound_ms":0,"processing_ms":0,"outbound_ms":0});q={"cmd":"activate_token","request_id":"a","generation":1,"token_id":t["token_id"],"activation_window_ns":250000000};self.assertEqual(self.ask(p,q)["status"],"ACTIVATED");self.assertEqual(self.ask(p,q)["reason"],"REPLAY");self.tear(p)
 def test_token_stale(self):
  p=self.server();t=self.ask(p,{"cmd":"issue_token","request_id":"a","generation":1,"ttl_ns":160000000,"inbound_ms":0,"processing_ms":0,"outbound_ms":0});time.sleep(.27);r=self.ask(p,{"cmd":"activate_token","request_id":"a","generation":1,"token_id":t["token_id"],"activation_window_ns":250000000});self.assertEqual(r["reason"],"STALE_TOKEN");self.tear(p)
 def test_token_authority_neutral_before_activation(self):
  p=self.server();t=self.ask(p,{"cmd":"issue_token","request_id":"a","generation":1,"ttl_ns":160000000,"inbound_ms":0,"processing_ms":0,"outbound_ms":0});self.assertFalse(t["lease_activated"]);self.assertFalse(t["task_input_authority"]);self.tear(p)
 def test_activation_ttl_exact(self):
  p=self.server();t=self.ask(p,{"cmd":"issue_token","request_id":"a","generation":1,"ttl_ns":160000000,"inbound_ms":0,"processing_ms":0,"outbound_ms":0});r=self.ask(p,{"cmd":"activate_token","request_id":"a","generation":1,"token_id":t["token_id"],"activation_window_ns":250000000});self.assertEqual(r["deadline_ns"]-r["activation_check_ns"],160000000);self.tear(p)
 def test_lease_source(self):
  import hashlib; self.assertEqual(hashlib.sha1((b"blob "+str((ROOT/"lease.py").stat().st_size).encode()+b"\0"+(ROOT/"lease.py").read_bytes())).hexdigest(),"b9dac6bb4063928354733d79bf371909a288a3d1")
if __name__=="__main__":unittest.main()
