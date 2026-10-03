import io,json,threading,unittest
from types import SimpleNamespace
from codex_app_server_client_v2 import CodexAppServerClient

class CurrentNumericOwnership(unittest.TestCase):
    def read(self,packet):
        c=object.__new__(CodexAppServerClient);c._condition=threading.Condition();c._pending={1};c._responses={};c._notifications=[];c._journal=None;c._closed=False;c.process=SimpleNamespace(stdout=io.StringIO(json.dumps(packet)+'\n'));c._read();self.assertTrue(c._closed);return c
    def accepted(self,packet):
        c=self.read(packet);self.assertEqual(c._responses,{1:packet});self.assertEqual(c._notifications,[])
    def excluded(self,packet):
        c=self.read(packet);self.assertEqual(c._responses,{})
    def test_integer_echo_keeps_existing_value(self):self.accepted({'id':1,'result':'issued'})
    def test_integral_number_echo_keeps_current_main_value(self):self.accepted({'id':1.0,'result':'issued'})
    def test_integral_number_error_keeps_current_main_error(self):self.accepted({'id':1.0,'error':{'code':-1,'message':'issued'}})
    def test_boolean_cannot_own_integer_one(self):self.excluded({'id':True,'result':'noise'})
    def test_string_cannot_own_integer_one(self):self.excluded({'id':'1','result':'noise'})
    def test_fractional_number_cannot_own_integer_one(self):self.excluded({'id':1.5,'result':'noise'})
    def test_unissued_integral_number_cannot_be_cached(self):self.excluded({'id':2.0,'result':'future'})
    def test_server_request_number_cannot_complete_client_request(self):self.excluded({'id':1.0,'method':'server/request','params':{}})

if __name__=='__main__':unittest.main()
