import ast, copy, json, sys, threading, time, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent; SRC=ROOT/'source'; sys.path.insert(0,str(SRC))
import fake_x
from executor_v13 import Executor
from executor_v3 import Cancelled
from input_owner_v12 import InputOwner as OwnerV12
from input_transition_owner_v4 import InputOwner as OwnerV4
from persistent_planner_adapter_v2 import PersistentPlannerAdapter
from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor

class Reader:
    def __init__(self,name): self.name=name
    def read(self,obs):
        return {'format':'observable-signal-v1','status':'observed','signal_id':self.name,
                'value':obs[self.name],'sequence':obs['sequence'],'capture_ns':obs['capture_ns'],
                'binding':obs['pointer_binding']}

def load_controller_helpers():
    tree=ast.parse((SRC/'map01_overlap_controller_v39.py').read_text(encoding='utf-8'))
    top={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    names=('guard_spec','ammo_guard_spec','_typed_json_equal','_signal_pair_matches',
           '_signal_pair_content_matches','DoomCoverSignalPairMonitor','build_cover_monitor',
           'cancel_invalidated_cover')
    ns={'json':json,'time':time,'ObservableSignalGuard':ObservableSignalGuard,'ObservableSignalPolicyMonitor':ObservableSignalPolicyMonitor,
        'MAX_AUTHORED_HEALTH_LOSS':20}
    exec(compile(ast.Module(body=[top[n] for n in names],type_ignores=[]),str(SRC/'map01_overlap_controller_v39.py'),'exec'),ns)
    return ns
H=load_controller_helpers()

class FakeBackend:
    sequence=12
    def __init__(self, owner): self.owner=owner; self.lease=None; self.started=threading.Event(); self.events=[]
    def validate(self,steps):
        if steps != [{'op':'fire_hold','key':'space'}]: raise ValueError('unexpected frozen command')
    def execute(self,step,cancel,identifier,index):
        self.lease.expected_focus=fake_x.state.focus
        self.lease.intent_token='deterministic-intent-'+identifier
        self.owner.call('down',self.lease,step['key'])
        self.events.append({'event':'fire_key_down','at_ns':time.perf_counter_ns(),'key':step['key']})
        self.started.set()
        while not cancel.wait(.001): pass
        raise Cancelled()
    def release_all(self):
        deadline=time.monotonic()+2
        inner=self.owner._inner
        while time.monotonic()<deadline:
            if any(r.get('event')=='owner_release' and r.get('reason')=='cancelled' for r in inner.records): break
            time.sleep(.001)
        receipt=self.owner.call('release',self.lease)
        return {'verified':receipt.get('verified') is True,'keys_down':receipt.get('keys_down'),
                'buttons_down':receipt.get('buttons_down'),'owner_receipt':receipt}

class FakeClient:
    def __init__(self,events): self.events=events
    def start_thread(self,**kw): return {'thread':{'id':'fake-thread'}}
    def start_turn(self,thread_id,inputs,**kw): self.events.append(('turn_started',time.perf_counter_ns())); return {'turn':{'id':'fake-turn'}}
    def interrupt_turn(self,thread_id,turn_id): self.events.append(('planner_interrupt',time.perf_counter_ns())); return {'accepted':True}
    def wait_turn_completed(self,thread_id,turn_id,timeout=120):
        return {'turn':{'status':'completed','items':[{'type':'agentMessage','text':'{"next_cover":[]}'}]}}
    def latest_turn_usage(self,*args): return {'input_tokens':0,'output_tokens':0}
    def close(self,timeout=5): pass

class FakeStdin:
    def __init__(self,executor,events): self.executor=executor; self.events=events
    def write(self,value):
        row=json.loads(value); self.events.append(('executor_cancel_command',time.perf_counter_ns(),row))
        self.executor.cancel(row['id']); return len(value)
    def flush(self): pass
class FakeProcess:
    def __init__(self,executor,events): self.stdin=FakeStdin(executor,events)

class AmmoExecutorReleaseComposition(unittest.TestCase):
    def run_case(self,ammo,hard):
        fake_x.state.keys.clear(); fake_x.state.buttons.clear()
        events=[]; rows=[]; row_cv=threading.Condition()
        def emit(row):
            with row_cv: rows.append(copy.deepcopy(row)); row_cv.notify_all()
            if row.get('event')=='input_released': events.append(('input_released',row['published_ns'],copy.deepcopy(row)))
            if row.get('event')=='terminal': events.append(('terminal',row.get('terminal_ns'),copy.deepcopy(row)))
        owner=OwnerV4('deterministic-fake-x',_owner_cls=OwnerV12)
        backend=FakeBackend(owner); executor=Executor(backend,emit)
        planner_events=[]; client=FakeClient(planner_events)
        planner=PersistentPlannerAdapter(client,model='fixture',effort='low',cwd='.',base_instructions='fixed deterministic test')
        planner.start_session(); handle=planner.begin_turn('pending frozen question',output_schema={'type':'object','required':['next_cover'],'properties':{'next_cover':{'type':'array'}},'additionalProperties':False})
        source={'event':'observation','sequence':1,'capture_ns':100,'pointer_binding':{'focus':42,'surface':7,'geometry':[0,0,800,600]},'health':97,'ammo':8}
        monitor,_=H['build_cover_monitor'](Reader('health'),source,{'signal_id':'health','critical_health_minimum':45,'maximum_health_loss':8,'max_source_age_ms':5000},'composition',ammo_reader=Reader('ammo'),requires_ammo=True)
        executor.submit('cover-1',[{'op':'fire_hold','key':'space'}],expected_sequence=12,valid_until_ns=time.perf_counter_ns()+10_000_000_000)
        self.assertTrue(backend.started.wait(1),'Executor did not begin fire hold')
        self.assertIn(65,fake_x.state.keys,'real V12 owner did not admit fake-X keydown')
        observation={'event':'observation','sequence':2,'capture_ns':200,'pointer_binding':source['pointer_binding'],'health':97,'ammo':ammo}
        invalidation=monitor.observe(observation)
        if hard:
            self.assertIsNotNone(invalidation)
            proc=FakeProcess(executor,events)
            def wait(predicate):
                deadline=time.monotonic()+2
                with row_cv:
                    while time.monotonic()<deadline:
                        match=next((r for r in rows if predicate(r)),None)
                        if match is not None:return match
                        row_cv.wait(.01)
                raise TimeoutError('terminal event not observed')
            result=H['cancel_invalidated_cover'](planner,handle,proc,wait,'cover-1')
            self.assertEqual(result[1]['status'],'cancelled')
            self.assertEqual(result[1]['release']['keys_down'],[])
            self.assertEqual(result[1]['release']['buttons_down'],[])
            self.assertTrue(result[1]['release']['verified'])
            self.assertNotIn(65,fake_x.state.keys)
            planner_result=planner.await_turn(handle)
            self.assertFalse(planner_result.answer_eligible)
            self.assertTrue(planner_result.cancellation_requested)
            owner_release=next(r for r in owner._inner.records if r.get('event')=='owner_release' and r.get('reason')=='cancelled')
            release_event=next(e[2] for e in events if e[0]=='input_released')
            self.assertTrue(owner_release['verified']); self.assertEqual(owner_release['keys_down'],[])
            self.assertFalse(release_event['grants_input_authority'])
            self.assertLessEqual(owner_release['verified_ns'],release_event['published_ns'])
            self.assertLessEqual(release_event['published_ns'],result[1]['terminal_ns'])
            cancel_at=next(x[1] for x in events if x[0]=='executor_cancel_command')
            planner_at=next(x[1] for x in planner_events if x[0]=='planner_interrupt')
            self.assertLess(cancel_at,planner_at,'Executor cancel must be sent before planner interrupt')
            executor.close(); owner.close()
            return {'arm':'hard_zero','ammo':ammo,'monitor_invalidation':invalidation,'executor_terminal':result[1],
                    'owner_release':owner_release,'input_released':release_event,'planner_result':planner_result.__dict__,
                    'order':['executor_cancel_command','planner_interrupt','owner_release','input_released','terminal'],
                    'remaining_fake_x_keys':sorted(fake_x.state.keys)}
        else:
            self.assertIsNone(invalidation)
            self.assertEqual(monitor.soft_event_count,1)
            immediate_action_minimum_ammo=5
            self.assertLess(ammo,immediate_action_minimum_ammo)
            time.sleep(.03)
            self.assertTrue(executor.active is not None,'soft boundary unexpectedly cancelled Executor')
            self.assertIn(65,fake_x.state.keys,'soft boundary should preserve active cover key')
            planner_result=planner.await_turn(handle)
            self.assertTrue(planner_result.answer_eligible)
            executor.cancel('cover-1')
            with row_cv:
                deadline=time.monotonic()+2
                while not any(r.get('event')=='terminal' for r in rows) and time.monotonic()<deadline: row_cv.wait(.01)
            terminal=next(r for r in rows if r.get('event')=='terminal')
            self.assertTrue(terminal.get('release',{}).get('verified'))
            self.assertNotIn(65,fake_x.state.keys)
            owner_release=next(r for r in owner._inner.records if r.get('event')=='owner_release' and r.get('reason')=='cancelled')
            executor.close(); owner.close()
            return {'arm':'soft_above_cover_floor','ammo':ammo,'monitor_invalidation':None,'soft_event_count':monitor.soft_event_count,
                    'executor_remained_active_during_pending_turn':True,'key_down_during_pending_turn':True,
                    'planner_answer_eligible':planner_result.answer_eligible,'manual_cleanup_terminal':terminal,'owner_release':owner_release}
    def test_soft_change_preserves_active_executor_and_hard_zero_cancels_before_interrupt(self):
        soft=self.run_case(4,False); hard=self.run_case(0,True)
        summary={
            'soft':{'ammo':soft['ammo'],'immediate_action_minimum_ammo':5,
                    'monitor_invalidation':soft['monitor_invalidation'],'soft_event_count':soft['soft_event_count'],
                    'executor_active_during_pending_turn':soft['executor_remained_active_during_pending_turn'],
                    'fire_key_down_during_pending_turn':soft['key_down_during_pending_turn'],
                    'pending_answer_eligible':soft['planner_answer_eligible'],
                    'eventual_cleanup_verified':soft['manual_cleanup_terminal']['release']['verified']},
            'hard':{'ammo':hard['ammo'],'monitor_reason':hard['monitor_invalidation']['reason'],
                    'executor_terminal_status':hard['executor_terminal']['status'],
                    'owner_release_verified':hard['owner_release']['verified'],
                    'owner_release_to_terminal_ns':hard['executor_terminal']['terminal_ns']-hard['owner_release']['verified_ns'],
                    'pending_answer_eligible':hard['planner_result']['answer_eligible'],
                    'executor_cancel_precedes_planner_interrupt':True,
                    'remaining_fake_x_keys':hard['remaining_fake_x_keys'],
                    'input_authority_admitted':False},
            'scope':'current-main Executor/owner source with in-memory fake X; no OS input, game, model, or live allocation'}
        print('COMPOSITION_RESULT='+json.dumps(summary,sort_keys=True))

if __name__=='__main__': unittest.main(verbosity=2)


