from __future__ import annotations
import json
from pathlib import Path
from lifecycle import Lifecycle

ROOT=Path(__file__).resolve().parent
FIX=ROOT/'fixture.json'; OUT=ROOT/'RESULT.json'

def fresh(f): return Lifecycle(f)

def main():
    if OUT.exists(): raise SystemExit('formal output already exists; rerun forbidden')
    f=json.loads(FIX.read_text())
    lc=fresh(f); trace=[]
    trace.append(lc.cold(f['cold_receipt']))
    trace.append(lc.reuse('reuse_A1',f['tasks']['A1'],'A1',f['evidence']['A1']))
    trace.append(lc.reuse('reuse_A2',f['tasks']['A2'],'A2',f['evidence']['A2']))
    trace.append(lc.reuse('invalidate_B','probe-B','B_invalid',f['evidence']['B_invalid']))
    trace.append(lc.repair('repair_B',f['repair_receipt'],'B_repair',f['evidence']['B_repair']))
    trace.append(lc.reuse('reuse_B1',f['tasks']['B1'],'B1',f['evidence']['B1']))
    trace.append(lc.reuse('reuse_B2',f['tasks']['B2'],'B2',f['evidence']['B2']))
    valid_final=lc.snapshot()

    controls={}
    controls['stale_W1_after_repair']=lc.reuse('control_stale_W1','stale-after-repair','B1',f['evidence']['B1'],requested_world_generation='W1')
    controls['duplicate_effect_replay']=lc.reuse('control_duplicate',f['tasks']['B2'],'B2',f['evidence']['B2'])
    controls['missing_binding_evidence']=lc.reuse('control_missing','missing-task','missing',f['evidence']['missing'])

    nofresh=fresh(f); nofresh.cold(f['cold_receipt'])
    controls['repair_without_fresh_evidence']=nofresh.repair('control_repair_no_fresh',f['repair_receipt'],'stale_A',f['evidence']['stale_A'])
    over=fresh(f); over.cold(f['cold_receipt'])
    controls['overbroad_repair']=over.repair('control_overbroad',f['repair_receipt'],'B_repair',f['evidence']['B_repair'],overbroad=True)

    valid_status=[r['status'] for r in trace]
    charges=[r['logical_generation_charge'] for r in trace]
    valid_effects=[r['effect_id'] for r in trace if r['effect_id']]
    invariants={
      'valid_statuses':valid_status==['INSTALLED','EFFECT_VERIFIED','EFFECT_VERIFIED','STALE_WORLD_BINDING','REPAIR_PROMOTED','EFFECT_VERIFIED','EFFECT_VERIFIED'],
      'valid_generation_charges':charges==[1,0,0,0,1,0,0] and sum(charges)==2,
      'selective_repair':trace[4]['versions_before']['palette']=='P1' and trace[4]['versions_after']['palette']=='P1' and trace[4]['versions_before']['method_id']=='M1' and trace[4]['versions_after']['method_id']=='M1' and trace[4]['versions_before']['world']=='W1' and trace[4]['versions_after']['world']=='W2',
      'invalidation_no_effect':trace[3]['effect_id'] is None,
      'unique_valid_effects':len(valid_effects)==4 and len(set(valid_effects))==4,
      'terminal_neutral':valid_final['owned_resources']==[],
      'palette_method_stable':valid_final['palette']['generation']=='P1' and valid_final['method']['method_id']=='M1' and valid_final['method']['version']=='1',
      'stale_replay_refused':controls['stale_W1_after_repair']['status']=='STALE_WORLD_GENERATION' and controls['stale_W1_after_repair']['effect_id'] is None,
      'no_fresh_repair_refused':controls['repair_without_fresh_evidence']['status']=='REPAIR_REFUSED' and controls['repair_without_fresh_evidence']['versions_before']==controls['repair_without_fresh_evidence']['versions_after'],
      'overbroad_repair_refused':controls['overbroad_repair']['status']=='OVERBROAD_REPAIR_REJECTED' and controls['overbroad_repair']['versions_before']==controls['overbroad_repair']['versions_after'],
      'duplicate_idempotent':controls['duplicate_effect_replay']['status']=='IDEMPOTENT_REPLAY' and len(lc.effects)==4,
      'missing_evidence_refused':controls['missing_binding_evidence']['status']=='NO_TARGET_AUTHORITY' and controls['missing_binding_evidence']['effect_id'] is None,
      'no_real_model_calls':True
    }
    if not invariants['stale_replay_refused']: decision='FAIL_STALE_BINDING_ESCAPE'
    elif not invariants['selective_repair'] or not invariants['overbroad_repair_refused']: decision='FAIL_NONSELECTIVE_REPAIR'
    elif not (invariants['valid_statuses'] and invariants['valid_generation_charges'] and invariants['unique_valid_effects'] and invariants['terminal_neutral'] and invariants['palette_method_stable'] and invariants['duplicate_idempotent'] and invariants['missing_evidence_refused'] and invariants['no_fresh_repair_refused']): decision='HOLD_COMPOSED_REUSE_NOT_CLOSED'
    else: decision='PASS_MINDUSTRY_PERSISTENT_LIFECYCLE_MECHANICS_SCOPED'
    result={'schema':'mindustry_integrated_lifecycle_mechanics_result_v1','task':f['task'],'formal_invocation':1,'formal_reruns':0,
            'provider_calls':0,'decision':decision,'valid_trace':trace,'valid_final':valid_final,'controls':controls,'invariants':invariants,
            'logical_generation_semantics':'fixture accounting only; not provider usage',
            'scope':'deterministic lifecycle mechanics only; no live Mindustry/model/token/latency/engine-effect claim'}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'charges':charges,'valid_effects':valid_effects,'controls':{k:v['status'] for k,v in controls.items()}},indent=2))
if __name__=='__main__': main()
