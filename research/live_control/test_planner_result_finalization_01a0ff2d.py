import threading,json,unittest
from research.live_control import persistent_planner_adapter_v2 as mod
ROWS=[]
def schema(value):return {'type':'object','required':['action'],'properties':{'action':{'type':'string','const':value}},'additionalProperties':False}
class Client:
    def __init__(self,answer):self.answer=answer;self.entered=threading.Event();self.release=threading.Event();self.starts=0;self.sessions=0;self.interrupts=0
    def start_thread(self,**kw):self.sessions+=1;return {'thread':{'id':'s'+str(self.sessions)}}
    def start_turn(self,*args,**kw):self.starts+=1;return {'turn':{'id':'t'+str(self.starts)}}
    def wait_turn_completed(self,*args,**kw):return {'turn':{'status':'completed','items':[{'type':'agentMessage','text':json.dumps({'action':self.answer})}]}}
    def latest_turn_usage(self,*args):
        self.entered.set()
        if not self.release.wait(3):raise TimeoutError('fixture release missing')
        return None
    def interrupt_turn(self,*args):self.interrupts+=1;return {}
def make(c):
    p=mod.PersistentPlannerAdapter(c,model='inert',effort='low',cwd='.',base_instructions='inert');p.start_session();return p
class Tests(unittest.TestCase):
    def staged(self,answer,operation):
        c=Client(answer);p=make(c);h=p.begin_turn('old',output_schema=schema('allowed'));box={}
        def awaiter():
            try:
                result=p.await_turn(h);box['eligible']=result.answer_eligible;box['answer']=result.answer;box['error']=result.error;box['cancelled']=result.cancellation_requested;box['handle']=str(result.handle)
            except BaseException as e:box['exception']=type(e).__name__+':'+str(e)
        t=threading.Thread(target=awaiter);t.start();effect={}
        try:
            self.assertTrue(c.entered.wait(3))
            try:
                if operation=='turn':effect['next']=str(p.begin_turn('next',output_schema=schema('forbidden')))
                elif operation=='reset':effect['next']=p.start_session()
                else:effect['interrupt']=p.interrupt(h)
            except mod.PlannerProtocolError as e:effect['refused']=str(e)
        finally:c.release.set();t.join(3)
        row={'case':answer+'_'+operation,'effect':effect,'result':box,'starts':c.starts,'sessions':c.sessions,'interrupts':c.interrupts,'worker_alive':t.is_alive()};ROWS.append(row)
        self.assertFalse(t.is_alive());self.assertNotIn('exception',box)
        if operation in ('turn','reset'):self.assertIn('refused',effect);self.assertEqual(c.starts,1);self.assertEqual(c.sessions,1);self.assertEqual(box['eligible'],answer=='allowed')
        else:self.assertTrue(box['cancelled']);self.assertFalse(box['eligible']);self.assertIsNone(box['answer']);self.assertEqual(c.interrupts,1)
    def test_valid_old_schema(self):self.staged('allowed','turn')
    def test_invalid_old_schema(self):self.staged('forbidden','turn')
    def test_reset_during_finalization(self):self.staged('allowed','reset')
    def test_late_cancel_during_finalization(self):self.staged('allowed','cancel')
    def test_sequential_completed(self):
        c=Client('allowed');c.release.set();p=make(c);one=p.await_turn(p.begin_turn('one',output_schema=schema('allowed')));two=p.await_turn(p.begin_turn('two',output_schema=schema('allowed')));p.start_session();ROWS.append({'case':'sequential','eligible':[one.answer_eligible,two.answer_eligible],'starts':c.starts,'sessions':c.sessions,'worker_alive':False});self.assertTrue(one.answer_eligible and two.answer_eligible);self.assertEqual(c.starts,2);self.assertEqual(c.sessions,2)
if __name__ == '__main__':
    unittest.main(verbosity=2)
