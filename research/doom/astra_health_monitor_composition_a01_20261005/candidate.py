#!/usr/bin/env python3
"""One-shot exact V39 health invalidation/cancel software-composition probe."""
import hashlib,json,sys,time
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path[:0]=[str(REPO/'research/doom'),str(REPO/'research/live_control')]
import map01_overlap_controller_v39 as c
FREEZE=json.loads((HERE/'FREEZE.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
controller=REPO/'research/doom/map01_overlap_controller_v39.py'
guard_source=REPO/'research/live_control/observable_signal_guard_v2.py'
if sha(controller)!=FREEZE['controller_source_sha256']: raise SystemExit('STOP_CONTROLLER_HASH')
if sha(guard_source)!=FREEZE['guard_source_sha256']: raise SystemExit('STOP_GUARD_HASH')
binding={'focus':7,'surface':9,'geometry':[0,0,640,560]}
def sig(name,value,seq,capture): return {'format':'observable-signal-v1','status':'observed','signal_id':name,'value':value,'sequence':seq,'capture_ns':capture,'binding':binding}
source_obs={'event':'observation','sequence':10,'capture_ns':1_000_000_000,'pointer_binding':binding}
health={10:sig('health',100,10,1_000_000_000),11:sig('health',96,11,3_400_000_000)}
ammo={10:sig('ammo',46,10,1_000_000_000),11:sig('ammo',44,11,3_400_000_000)}
class Reader:
 def __init__(self,rows): self.rows=rows
 def read(self,row): return self.rows[row['sequence']]
monitor,receipt=c.build_cover_monitor(Reader(health),source_obs,{'signal_id':'health','critical_health_minimum':35,'maximum_health_loss':3,'max_source_age_ms':30000},4,ammo_reader=Reader(ammo),requires_ammo=True)
observation={'event':'typed_observation','sequence':11,'capture_ns':3_400_000_000,'pointer_binding':binding,'frame_rgb_sha256':'f'*64,'signals':{'health':health[11],'ammo':ammo[11]}}
event=monitor.observe(observation)
if event is None: raise SystemExit('FAIL_NO_MONITOR_INVALIDATION')
planner_result=SimpleNamespace(handle=SimpleNamespace(turn_id='turn-4'),status='interrupted',answer_eligible=False)
admission=c.final_admission_from_planner_result(planner_result,event['outcome_evaluated_ns'],event,time.perf_counter_ns()+1000)
class Stdin:
 def __init__(self): self.writes=[]
 def write(self,s): self.writes.append(s)
 def flush(self): pass
class Process:
 def __init__(self): self.stdin=Stdin()
class Planner:
 def __init__(self): self.interrupted=[]
 def interrupt(self,h): self.interrupted.append(h); return {'status':'interrupted'}
process,planner=Process(),Planner()
terminal={'event':'terminal','id':'cover-4','status':'cancelled','release':{'verified':True,'keys_down':[],'buttons_down':[]}}
interrupt,result=c.cancel_invalidated_cover(planner,'turn-4',process,lambda predicate:terminal,'cover-4')
out={'source_admission':receipt['status'],'hard_minimum':receipt['effective']['hard_minimum'],'invalidation_event':event['event'],'reason':event['reason'],'health_outcome':event['outcomes']['health']['status'],'ammo_outcome':event['outcomes']['ammo']['status'],'grants_input_authority':event['grants_input_authority'],'final_admission':admission['status'],'planner_interrupt':interrupt['status'],'cancel_request':json.loads(process.stdin.writes[0]),'terminal_status':result['status'],'release':result['release'],'cancel_helper_returned':result is terminal}
if not (receipt['status']=='admitted' and out['hard_minimum']==97 and out['reason']=='health:below_hard_minimum' and out['health_outcome']=='HARD_INVALIDATED' and out['ammo_outcome']=='SOFT_CHANGED' and not out['grants_input_authority'] and admission['status']=='REJECTED_POLICY_INVALIDATED' and planner.interrupted==['turn-4'] and out['cancel_request']=={'op':'cancel','id':'cover-4'} and result is terminal): raise SystemExit('FAIL_COMPOSITION_ASSERTION')
(HERE/'raw.json').write_text(json.dumps({'schema':'astra-health-monitor-composition-a01-v1','main_base':FREEZE['main_base'],'controller_sha256':sha(controller),'guard_sha256':sha(guard_source),'input_readout_sha256':FREEZE['input_readout_sha256'],'observation_game_time_s':47.0,'health':96,'ammo':44,'output':out},indent=2)+'\n')
print(json.dumps(out,indent=2))
