import ast, hashlib, inspect, json, queue, sys, threading, time, unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
DOOM=ROOT/'research'/'doom'
sys.path[:0]=[str(DOOM),str(ROOT/'research'/'live_control')]
import map01_overlap_controller_v39 as c
from observable_signal_guard_v2 import ObservableSignalGuard
B={'focus':7,'surface':9,'geometry':[0,0,640,480]}
def sig(n,v,s): return {'status':'observed','signal_id':n,'value':v,'sequence':s,'capture_ns':1_000_000_000+s*100_000_000,'binding':B}
def obs(kind,s,h,a=4): return {'event':kind,'sequence':s,'capture_ns':1_000_000_000+s*100_000_000,'pointer_binding':B,'frame_rgb_sha256':format(s,'064x'),'signals':{'health':sig('health',h,s),'ammo':sig('ammo',a,s)}}
def extract_wait(incoming,process):
 t=ast.parse(inspect.getsource(c)); main=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='main'); wait=next(n for n in ast.walk(main) if isinstance(n,ast.FunctionDef) and n.name=='wait'); f=ast.parse('def factory(incoming, process):\n latest=None\n').body[0]; f.body.append(wait); f.body+=ast.parse('return wait\n').body; ns={'queue':queue,'time':time}; exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'<v39-wait>','exec'),ns); return ns['factory'](incoming,process)
class P:
 def __init__(self): self.stdin=self; self.writes=[]; self.events=[]
 def write(self,s): self.writes.append(s); self.events.append('executor_cancel')
 def flush(self): pass
class R:
 def __init__(self,n): self.n=n
 def read(self,row): return row['signals'][self.n]
class Tests(unittest.TestCase):
 def test_hard_crossing_remains_terminal_through_recovery_during_cancel(self):
  src=obs('observation',10,100)
  hg=ObservableSignalGuard({'op':'observable_signal_guard','guard_id':'h','source_sequence':10,'signal_id':'health','source_value':100,'hard_minimum':88,'max_source_age_ms':30000,'on_soft_change':'preserve_existing_policy','on_hard_change':'needs_decision','on_unknown':'needs_decision'},src['signals']['health'],B)
  ag=ObservableSignalGuard({'op':'observable_signal_guard','guard_id':'a','source_sequence':10,'signal_id':'ammo','source_value':4,'hard_minimum':1,'max_source_age_ms':30000,'on_soft_change':'preserve_existing_policy','on_hard_change':'needs_decision','on_unknown':'needs_decision'},src['signals']['ammo'],B)
  mon=c.DoomCoverSignalPairMonitor({'health':hg,'ammo':ag},R('health'),R('ammo'))
  low=obs('typed_observation',11,80); recovery=obs('typed_observation',12,96); recovery_full=obs('observation',12,96)
  inv=mon.observe(low); self.assertEqual(inv['outcome']['status'],'HARD_INVALIDATED'); self.assertEqual(hg.evaluate(recovery['signals']['health'])['status'],'SOFT_CHANGED')
  q=queue.Queue(); q.put(recovery); q.put({'event':'terminal','id':'cover-0','status':'cancelled','release':{'verified':True,'keys_down':[],'buttons_down':[]}}); proc=P(); wait=extract_wait(q,proc)
  term=wait(lambda x:x['event']=='terminal' and x.get('id')=='cover-0',observation_monitor=None)
  c.require_cover_terminal(term,cancellation_requested=True)
  # A new full frame is emitted after the cancel terminal, as at the response-boundary drain.
  q.put(recovery_full)
  drained=c.drain_pending_observation_events(q,c.DoomCoverSignalPairMonitor({'health':hg,'ammo':ag},R('health'),R('ammo')),'cover-0')
  recovered_source=drained['latest']; recovered_health=R('health').read(recovered_source); recovered_ammo=R('ammo').read(recovered_source)
  fresh_monitor,fresh_admission=c.build_cover_monitor(R('health'),recovered_source,None,1,ammo_reader=R('ammo'),requires_ammo=True)
  class Planner:
   def __init__(self): self.started=threading.Event(); self.done=threading.Event(); self.return_ns=None
   def await_turn(self,h,t): self.started.set(); self.done.wait(t); self.return_ns=time.perf_counter_ns(); return SimpleNamespace(handle=h,status='completed',answer_eligible=True,answer={'state':'active','commands':[{'action':'forward'}]})
   def interrupt(self,h,*,before_transport=None):
    if before_transport: before_transport()
    proc.events.append('planner_interrupt'); self.done.set(); return {'status':'interrupt_requested'}
  planner=Planner(); handle=SimpleNamespace(turn_id='t0'); pool=ThreadPoolExecutor(1); fut=pool.submit(planner.await_turn,handle,3); self.assertTrue(planner.started.wait(1))
  result=planner.interrupt(handle,before_transport=lambda:(proc.write(json.dumps({'op':'cancel','id':'cover-0'})+'\n'),proc.flush())); plan=fut.result(2); pool.shutdown()
  adm=c.final_admission_from_planner_result(plan,planner.return_ns,inv,time.perf_counter_ns()+1000)
  self.assertEqual(proc.events,['executor_cancel','planner_interrupt']); self.assertEqual(term['release']['keys_down'],[]); self.assertEqual(drained['latest']['sequence'],12); self.assertIsNone(drained['invalidation']); self.assertEqual(adm['status'],'REJECTED_POLICY_INVALIDATED'); self.assertFalse(adm['input_authority_admitted'])
  raw={'case':'health 100->80 hard invalidation at seq11; 80->96 recovery at seq12 during cancel wait; pending answer remains discarded','source_commit':__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'controller_sha256':hashlib.sha256((DOOM/'map01_overlap_controller_v39.py').read_bytes()).hexdigest(),'guard_sha256':hashlib.sha256((ROOT/'research/live_control/observable_signal_guard_v2.py').read_bytes()).hexdigest(),'hard_outcome':inv['outcome'],'recovery_guard_counterfactual':hg.evaluate(recovery['signals']['health']),'cancel_terminal':term,'recovery_observation':recovery,'recovered_fresh_source':{'sequence':recovered_source['sequence'],'health':recovered_health['value'],'ammo':recovered_ammo['value'],'cover_admission':fresh_admission['status'],'guard_source_sequence':fresh_monitor.guards['health'].spec['source_sequence'],'guard_source_value':fresh_monitor.guards['health'].spec['source_value']},'drained_latest':drained['latest']['sequence'],'drained_invalidation':drained['invalidation'],'planner_answer_eligible':plan.answer_eligible,'final_admission':adm,'event_order':proc.events,'formal_allocation_invocations':0,'game_model_gui_os_input':False}
  (Path(__file__).parent/'results'/'candidate.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n',encoding='utf-8')
if __name__=='__main__': unittest.main(verbosity=2)
