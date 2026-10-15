import copy, hashlib, json, os, queue, sys, threading, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WT=ROOT/'worktree'
PKG=WT/'research'/'doom'/'v39_pending_ammo_executor_release_composition_a01_20261012'
SRC=PKG/'source'
sys.path[:0]=[str(WT/'research'/'doom'),str(WT/'research'/'live_control'),str(SRC),str(PKG)]
import observable_signal_guard_v2 as monitor_module
import test_composition as composition
from types import SimpleNamespace
controller=SimpleNamespace(ObservableSignalPolicyMonitor=monitor_module.ObservableSignalPolicyMonitor, build_cover_monitor=composition.H['build_cover_monitor'], cancel_invalidated_cover=composition.H['cancel_invalidated_cover'])
import fake_x
from executor_v13 import Executor
from input_owner_v12 import InputOwner as OwnerV12
from input_transition_owner_v4 import InputOwner as OwnerV4
from persistent_planner_adapter_v2 import PersistentPlannerAdapter
from test_composition import FakeBackend, FakeClient, FakeProcess
class Reader:
 def __init__(self,name): self.name=name
 def read(self,obs): return {'format':'observable-signal-v1','status':'observed','signal_id':self.name,'value':obs[self.name],'sequence':obs['sequence'],'capture_ns':obs['capture_ns'],'binding':obs['pointer_binding'],'wad_sha256':'b'*64}
binding={'focus':42,'surface':7,'geometry':[0,0,800,600]}
fake_x.state.keys.clear(); fake_x.state.buttons.clear()
rows=[]; cond=threading.Condition(); ev=[]; planner_events=[]
def emit(row):
 with cond: rows.append(copy.deepcopy(row)); cond.notify_all()
 if row.get('event')=='input_released': ev.append(('input_released',row['published_ns'],copy.deepcopy(row)))
 if row.get('event')=='terminal': ev.append(('terminal',row.get('terminal_ns'),copy.deepcopy(row)))
owner=OwnerV4('health-typed-fake-x',_owner_cls=OwnerV12)
backend=FakeBackend(owner); executor=Executor(backend,emit)
client=FakeClient(planner_events); planner=PersistentPlannerAdapter(client,model='fixture',effort='low',cwd='.',base_instructions='fixed health-only typed cancellation integration')
planner.start_session(); handle=planner.begin_turn('pending model answer',output_schema={'type':'object','required':['next_cover'],'properties':{'next_cover':{'type':'array'}},'additionalProperties':False})
try:
 source={'event':'observation','sequence':1,'capture_ns':1_000_000_000,'pointer_binding':binding,'health':97}
 validity={'signal_id':'health','critical_health_minimum':45,'maximum_health_loss':8,'max_source_age_ms':5000}
 monitor,admission=controller.build_cover_monitor(Reader('health'),source,validity,1)
 assert type(monitor) is controller.ObservableSignalPolicyMonitor
 assert admission['monitor_mode']=='health_only'
 executor.submit('cover-health-1',[{'op':'fire_hold','key':'space'}],expected_sequence=12,valid_until_ns=time.perf_counter_ns()+10_000_000_000)
 assert backend.started.wait(1) and 65 in fake_x.state.keys
 cap=1_100_000_000
 health={'format':'observable-signal-v1','status':'observed','signal_id':'health','value':40,'sequence':2,'capture_ns':cap,'binding':binding,'wad_sha256':'b'*64}
 ammo={'format':'observable-signal-v1','status':'observed','signal_id':'ammo','value':8,'sequence':2,'capture_ns':cap,'binding':binding,'wad_sha256':'b'*64}
 typed={'event':'typed_observation','schema':'doom-typed-observation-v1','id':'synthetic-typed','step':2,'sequence':2,'capture_ns':cap,'pointer_binding':binding,'signals':{'health':health,'ammo':ammo},'frame_rgb_sha256':'a'*64,'frame_size':[800,600],'typed_extraction_started_ns':cap+1,'typed_ready_ns':cap+2,'artifact_published':False,'grants_input_authority':False}
 key_was_down_before_invalidation=65 in fake_x.state.keys
 assert key_was_down_before_invalidation
 delay_ms=float(os.environ.get('INJECT_DELAY_MS','0'))
 time.sleep(delay_ms/1000.0)
 invalidation=monitor.observe(typed)
 assert invalidation['outcome']['status']=='HARD_INVALIDATED' and invalidation['outcome']['current_value']==40
 process=FakeProcess(executor,ev)
 def wait(predicate):
  deadline=time.monotonic()+2
  with cond:
   while time.monotonic()<deadline:
    match=next((row for row in rows if predicate(row)),None)
    if match is not None:return match
    cond.wait(.01)
  raise TimeoutError('terminal after early health invalidation not observed')
 interrupt,terminal=controller.cancel_invalidated_cover(planner,handle,process,wait,'cover-health-1')
 planner_result=planner.await_turn(handle)
 assert terminal['status']=='cancelled'
 assert terminal['release']['verified'] is True and terminal['release']['keys_down']==[] and terminal['release']['buttons_down']==[]
 assert 65 not in fake_x.state.keys
 assert not planner_result.answer_eligible and planner_result.cancellation_requested
 owner_release=next(r for r in owner._inner.records if r.get('event')=='owner_release' and r.get('reason')=='cancelled')
 release=next(e[2] for e in ev if e[0]=='input_released')
 cancel_ns=next(e[1] for e in ev if e[0]=='executor_cancel_command')
 planner_ns=next(e[1] for e in planner_events if e[0]=='planner_interrupt')
 assert owner_release['verified'] and owner_release['keys_down']==[]
 assert cancel_ns<planner_ns<=owner_release['verified_ns']<=release['published_ns']<=terminal['terminal_ns']
 assert release['grants_input_authority'] is False
 result={'schema':'health-only-typed-to-owner-release-composition-v1','head':'synthetic stack b6f0cc68adc1c67d6b1c878b7d9ce1af6abe3152','monitor_blob':'PR #8866 eb1367cc3ac1184862c454440a418dcf1add9267','monitor_module_path':str(Path(monitor_module.__file__).resolve()),'monitor_module_sha256':hashlib.sha256(Path(monitor_module.__file__).read_bytes()).hexdigest(),'trigger':{'kind':'typed_observation','sequence':2,'health':40,'hard_minimum':89,'monitor_status':invalidation['outcome']['status'],'monitor_event':invalidation},'admission':admission,'executor':{'injected_delay_ms':delay_ms,'held_key_to_verified_release_ms':(owner_release['verified_ns']-backend.events[0]['at_ns'])/1e6,'terminal_status':terminal['status'],'key_was_down_before_invalidation':key_was_down_before_invalidation,'release':terminal['release'],'input_released_event':release,'owner_release_verified':owner_release['verified'],'remaining_keys':sorted(fake_x.state.keys),'remaining_buttons':sorted(fake_x.state.buttons),'pending_answer_eligible':planner_result.answer_eligible,'cancellation_requested':planner_result.cancellation_requested},'ordering':['executor_cancel_command','planner_interrupt','owner_release_verified','input_released','terminal'],'timestamps_ns':{'executor_cancel':cancel_ns,'planner_interrupt':planner_ns,'owner_verified_release':owner_release['verified_ns'],'release_published':release['published_ns'],'terminal':terminal['terminal_ns']},'all_assertions_passed':True,'scope':'Synthetic integration of current V39 health-only monitor and cancel helper with Executor V13/V4->V3->V12 using in-memory fake X. No physical input, GUI, game, live allocation, latency claim, useful feedback, recovery, survival, or task-success claim.'}
 (Path('/out')/(os.environ.get('RESULT_NAME','result')+'.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(result,indent=2,sort_keys=True))
finally:
 try: executor.close()
 finally:
  owner.close()









