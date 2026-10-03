import json,threading,unittest
from research.live_control import persistent_planner_adapter_v2 as mod
ROWS=[]
def contract():return {'type':'object','properties':{'x':{'type':'integer'}},'required':['x'],'additionalProperties':False}
class Client:
    def __init__(self,answer,transport=False,error=False):self.answer=answer;self.transport=transport;self.error=error;self.turns=0;self.calls=[];self.enter=threading.Event();self.release=threading.Event()
    def start_thread(self,**kw):return {'thread':{'id':'s'}}
    def start_turn(self,*args,**kw):
        self.turns+=1
        if self.transport:kw['outputSchema']['required'].clear()
        return {'turn':{'id':'t'+str(self.turns)}}
    def wait_turn_completed(self,*a,**kw):return {'turn':{'status':'completed','items':[{'type':'agentMessage','text':json.dumps(self.answer)}]}}
    def latest_turn_usage(self,*a):return None
    def interrupt_turn(self,thread,turn):
        self.calls.append([thread,turn])
        if turn=='t1':
            self.enter.set()
            if not self.release.wait(3):raise TimeoutError('own fixture release')
        elif self.error:raise OSError('new interrupt failed')
        return {'turn':turn}
def planner(c):
    p=mod.PersistentPlannerAdapter(c,model='inert',effort='low',cwd='.',base_instructions='inert');p.start_session();return p
class Tests(unittest.TestCase):
    def alias(self,kind):
        c=Client({} if kind in ('caller','transport') else {'x':1},transport=kind=='transport');p=planner(c);s=contract();h=p.begin_turn('p',output_schema=s)
        if kind=='caller':s['required'].clear()
        elif kind=='nested':s['properties']['x']['type']='string'
        res=p.await_turn(h);expect=kind in ('nested','control');ROWS.append({'case':kind,'eligible':res.answer_eligible,'expected':expect,'answer':res.answer,'error':res.error,'starts':c.turns,'handle':str(res.handle)})
        self.assertEqual(res.answer_eligible,expect);self.assertEqual(c.turns,1);self.assertEqual(res.handle,h)
    def test_caller_required(self):self.alias('caller')
    def test_caller_nested(self):self.alias('nested')
    def test_transport_required(self):self.alias('transport')
    def test_schema_control(self):self.alias('control')
    def custody(self,serial,error):
        c=Client({'x':1},error=error);p=planner(c);h1=p.begin_turn('old',output_schema=contract());box={}
        def old():box['response']=p.interrupt(h1)
        t=threading.Thread(target=old);t.start()
        try:
            self.assertTrue(c.enter.wait(3))
            if serial:c.release.set();t.join(3)
            result=p.await_turn(h1);h2=p.begin_turn('new',output_schema=contract());fresh=p.interrupt(h2)
        finally:c.release.set();t.join(3)
        repeated=p.interrupt(h2);ROWS.append({'case':('serial' if serial else 'overlap')+('_error' if error else '_success'),'first':fresh,'repeat':repeated,'old':box,'old_eligible':result.answer_eligible,'old_cancelled':result.cancellation_requested,'calls':c.calls,'worker_alive':t.is_alive()})
        self.assertFalse(t.is_alive());self.assertFalse(result.answer_eligible);self.assertTrue(result.cancellation_requested);self.assertEqual(repeated['response'],fresh['response']);self.assertEqual(c.calls,[['s','t1'],['s','t2']])
    def test_serial_interrupt(self):self.custody(True,False)
    def test_overlap_success(self):self.custody(False,False)
    def test_overlap_error(self):self.custody(False,True)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));print(json.dumps({'rows':ROWS,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}));raise SystemExit(not result.wasSuccessful())
