import pathlib,json,threading,tempfile,unittest
ROWS=[]
from research.live_control.integrated_efficiency_app_server_model_v1 import PersistentGroundingModel
ANSWER={'format':'plain-form-points-v1','field':{'point_space':'source_observation_pixels','point':{'x':10,'y':20}},'submit':{'point_space':'source_observation_pixels','point':{'x':30,'y':40}}}
class Client:
    def __init__(self,mode):
        self.mode=mode;self.sent=[];self.closed=0;self.entered=threading.Event();self.release=threading.Event();self.lock=threading.Lock()
    def start_thread(self,**kw):return {'thread':{'id':'thread-1'}}
    def start_turn(self,thread,inputs,**kw):
        with self.lock:
            self.sent.append({'thread':thread,'inputs':inputs,'schema':kw['outputSchema']});n=len(self.sent)
        if self.mode=='timeout':raise TimeoutError('synthetic response lost after recorded send')
        if self.mode=='missing':return {'turn':{}}
        if self.mode=='pending' and n==1:
            self.entered.set()
            if not self.release.wait(3):raise TimeoutError('fixture release absent')
        return {'turn':{'id':f'turn-{n}'}}
    def wait_turn_completed(self,thread,turn,timeout):return {'turn':{'status':'completed','items':[{'type':'agentMessage','text':json.dumps(ANSWER)}]}}
    def latest_turn_usage(self,*args):return None
    def close(self):self.closed+=1
class Bridge(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=pathlib.Path(self.temp.name);self.client=None
    def model(self,mode):
        self.client=Client(mode)
        return PersistentGroundingModel(self.root/'session',self.root,node='unused',cli='unused',contract='plain',client=self.client,path_converter=str)
    def invoke(self,model,name):
        try:return {'kind':'result','value':model.call(self.root/name,'ground two points',self.root/'synthetic.png','plain',self.root)}
        except Exception as e:return {'kind':'error','type':type(e).__name__,'message':str(e)}
    def row(self,model,name,returns,alive=False):
        model.close()
        record={'case':name,'returns':returns,'sends':len(self.client.sent),'sent':self.client.sent,'wrapper_calls':model.calls,'files':sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*') if p.is_file()),'worker_alive':alive,'borrowed_close_count':self.client.closed}
        ROWS.append(record);return record
    def unknown(self,mode):
        m=self.model(mode);r=self.row(m,mode,[self.invoke(m,'first'),self.invoke(m,'second')]);self.assertEqual(r['sends'],1);self.assertEqual([v['kind'] for v in r['returns']],['error','error']);self.assertFalse(any(p.endswith('result.json') for p in r['files']));self.assertEqual(r['borrowed_close_count'],0)
    def test_timeout_unknown(self):self.unknown('timeout')
    def test_missing_id_unknown(self):self.unknown('missing')
    def test_concurrent_pending(self):
        m=self.model('pending');first=[];thread=threading.Thread(target=lambda:first.append(self.invoke(m,'first')))
        thread.start()
        try:
            self.assertTrue(self.client.entered.wait(3));second=self.invoke(m,'second')
        finally:self.client.release.set();thread.join(3)
        r=self.row(m,'pending',{'first':first,'second':second},thread.is_alive());self.assertFalse(r['worker_alive']);self.assertEqual(r['sends'],1);self.assertEqual(second['kind'],'error');self.assertEqual(first[0]['kind'],'result');self.assertIn('first/result.json',r['files']);self.assertNotIn('second/result.json',r['files']);self.assertEqual(r['borrowed_close_count'],0)
    def test_sequential_completed(self):
        m=self.model('healthy');r=self.row(m,'sequential',[self.invoke(m,'first'),self.invoke(m,'second')]);self.assertEqual(r['sends'],2);self.assertEqual(m.calls,2);self.assertEqual([v['kind'] for v in r['returns']],['result','result']);self.assertIn('first/result.json',r['files']);self.assertIn('second/result.json',r['files']);self.assertEqual(r['borrowed_close_count'],0)
if __name__ == '__main__':
    unittest.main(verbosity=2)
