import json,threading,unittest
from research.live_control import persistent_planner_adapter_v2 as mod
SCHEMA={'type':'object','properties':{'action':{'type':'string'}},'required':['action'],'additionalProperties':False}
rows=[]
class SessionClient:
 def __init__(self,unknown=False):self.unknown=unknown;self.entered=threading.Event();self.release=threading.Event();self.sessions=0;self.turns=0
 def start_thread(self,**kw):
  self.sessions+=1;n=self.sessions
  if n==1:
   self.entered.set()
   if not self.release.wait(3):raise TimeoutError('fixture release missing')
  if self.unknown:raise TimeoutError('session outcome unknown')
  return {'thread':{'id':'s'+str(n)}}
 def start_turn(self,*a,**kw):self.turns+=1;return {'turn':{'id':'new-turn'}}
class Client:
 def __init__(self,kind='normal'):
  self.kind=kind;self.entered=threading.Event();self.release=threading.Event();self.calls=[];self.interrupts=[];self.sessions=0;self.lock=threading.Lock()
 def start_thread(self,**kw):
  self.sessions+=1;return {'thread':{'id':'s'+str(self.sessions)}}
 def start_turn(self,thread,inputs,**kw):
  with self.lock:self.calls.append({'thread':thread,'inputs':inputs});n=len(self.calls)
  if self.kind=='pending' and n==1:
   self.entered.set()
   if not self.release.wait(3):raise TimeoutError('fixture release missing')
  if self.kind=='unknown':raise TimeoutError('synthetic outcome unknown after admitted send')
  if self.kind=='missing':return {'turn':{}}
  return {'turn':{'id':'t'+str(n)}}
 def wait_turn_completed(self,thread,turn,timeout=120):return {'turn':{'status':'completed','items':[{'type':'agentMessage','text':'{"action":"forward"}'}]}}
 def latest_turn_usage(self,*a):return None
 def interrupt_turn(self,thread,turn):self.interrupts.append([thread,turn]);return {}
def planner(c):
 p=mod.PersistentPlannerAdapter(c,model='inert-no-provider',effort='low',cwd='.',base_instructions='inert');p.start_session();return p
class Tests(unittest.TestCase):
 def test_pending_session_refuses_another_session(self):
  c=SessionClient();p=mod.PersistentPlannerAdapter(c,model='inert',effort='low',cwd='.',base_instructions='inert');box={}
  def start():
   try:box['first']=p.start_session()
   except BaseException as e:box['error']=type(e).__name__
  t=threading.Thread(target=start);t.start()
  try:
   self.assertTrue(c.entered.wait(3))
   try:box['second']=p.start_session()
   except mod.PlannerProtocolError:box['refused']=True
  finally:c.release.set();t.join(3)
  rows.append({'case':'pending_session','sessions':c.sessions,'box':box,'worker_alive_after_join':t.is_alive()})
  self.assertFalse(t.is_alive());self.assertEqual(c.sessions,1);self.assertEqual(box.get('first'),'s1');self.assertTrue(box.get('refused'))
 def test_unknown_session_refuses_retry(self):
  c=SessionClient(unknown=True);c.release.set();p=mod.PersistentPlannerAdapter(c,model='inert',effort='low',cwd='.',base_instructions='inert');errors=[]
  for _ in range(2):
   try:p.start_session()
   except BaseException as e:errors.append(type(e).__name__)
  rows.append({'case':'unknown_session','sessions':c.sessions,'errors':errors})
  self.assertEqual(errors,['TimeoutError','PlannerProtocolError']);self.assertEqual(c.sessions,1)
 def pending(self,operation):
  c=Client('pending');p=planner(c);first={};second={}
  def launch():
   try:first['handle']=p.begin_turn('first',output_schema=SCHEMA)
   except BaseException as e:first['error']=type(e).__name__+':'+str(e)
  t=threading.Thread(target=launch,name='own-pending-start');t.start()
  try:
   self.assertTrue(c.entered.wait(3),'first start did not enter fixture')
   try:
    if operation=='turn':second['handle']=p.begin_turn('second',output_schema=SCHEMA)
    else:second['session']=p.start_session()
   except mod.PlannerProtocolError as e:second['refused']=str(e)
  finally:c.release.set();t.join(3)
  h=first.get('handle');interrupt=None
  if h:
   try:interrupt=p.interrupt(h)['outcome']
   except mod.PlannerProtocolError:interrupt='untracked'
  row={'case':'pending_'+operation,'client_calls':c.calls,'sessions':c.sessions,'first_handle':str(h),'first_error':first.get('error'),'second_handle':str(second.get('handle')),'second_session':second.get('session'),'second_refused':second.get('refused'),'interrupt_outcome':interrupt,'interrupts':c.interrupts,'worker_alive_after_join':t.is_alive()};rows.append(row)
  self.assertFalse(t.is_alive());self.assertIn('refused',second);self.assertIsNotNone(h);self.assertEqual(len(c.calls),1);self.assertEqual(c.sessions,1);self.assertEqual(interrupt,'requested');self.assertEqual(len(c.interrupts),1)
 def test_pending_turn_refuses_second_send(self):self.pending('turn')
 def test_pending_turn_refuses_session_reset(self):self.pending('reset')
 def unresolved(self,kind):
  c=Client(kind);p=planner(c);first=None;refused=[]
  try:p.begin_turn('unknown',output_schema=SCHEMA)
  except (TimeoutError,mod.PlannerProtocolError) as e:first=type(e).__name__
  for name,fn in [('turn',lambda:p.begin_turn('retry',output_schema=SCHEMA)),('reset',p.start_session)]:
   try:fn()
   except mod.PlannerProtocolError:refused.append(name)
   except TimeoutError:pass
  rows.append({'case':kind,'first_error':first,'refused':refused,'send_calls':len(c.calls),'sessions':c.sessions})
  self.assertIsNotNone(first);self.assertEqual(refused,['turn','reset']);self.assertEqual(len(c.calls),1);self.assertEqual(c.sessions,1)
 def test_unknown_start_never_blindly_retries(self):self.unresolved('unknown')
 def test_missing_id_never_blindly_retries(self):self.unresolved('missing')
 def test_completed_turn_allows_next_and_reset(self):
  c=Client();p=planner(c);h=p.begin_turn('one',output_schema=SCHEMA);r=p.await_turn(h);h2=p.begin_turn('two',output_schema=SCHEMA);r2=p.await_turn(h2);p.start_session();rows.append({'case':'completed','eligible':[r.answer_eligible,r2.answer_eligible],'sends':len(c.calls),'sessions':c.sessions});self.assertTrue(r.answer_eligible and r2.answer_eligible);self.assertEqual(len(c.calls),2);self.assertEqual(c.sessions,2)
 def test_cancelled_observation_never_eligible(self):
  c=Client();p=planner(c);h=p.begin_turn('old',output_schema=SCHEMA);p.interrupt(h);r=p.await_turn(h);rows.append({'case':'cancelled','eligible':r.answer_eligible,'interrupts':c.interrupts});self.assertFalse(r.answer_eligible);self.assertEqual(len(c.interrupts),1)
if __name__ == '__main__':
 unittest.main(verbosity=2)
