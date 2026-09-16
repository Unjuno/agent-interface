from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    f=json.loads((ROOT/'fixture.json').read_text()); r=json.loads((ROOT/'RESULT.json').read_text())
    t=r['valid_trace']; c=r['controls']; checks={}
    checks['formal_count']=r['formal_invocation']==1 and r['formal_reruns']==0 and r['provider_calls']==0
    checks['phase_order']=[x['phase'] for x in t]==['cold','reuse_A1','reuse_A2','invalidate_B','repair_B','reuse_B1','reuse_B2']
    checks['statuses']=[x['status'] for x in t]==['INSTALLED','EFFECT_VERIFIED','EFFECT_VERIFIED','STALE_WORLD_BINDING','REPAIR_PROMOTED','EFFECT_VERIFIED','EFFECT_VERIFIED']
    checks['charges']=[x['logical_generation_charge'] for x in t]==[1,0,0,0,1,0,0]
    checks['reuse_zero_charge']=all(t[i]['logical_generation_charge']==0 for i in (1,2,5,6))
    checks['invalidation_no_effect']=t[3]['effect_id'] is None and t[3]['versions_before']==t[3]['versions_after']
    rb=t[4]['versions_before']; ra=t[4]['versions_after']
    checks['world_only_repair']=(rb['palette']==ra['palette']=='P1' and rb['method_id']==ra['method_id']=='M1' and rb['method_version']==ra['method_version']=='1' and rb['world']=='W1' and ra['world']=='W2')
    effects=[x['effect_id'] for x in t if x['effect_id']]
    checks['effects_exact_once']=len(effects)==4 and len(set(effects))==4 and len(r['valid_final']['effects'])==4
    checks['neutral']=r['valid_final']['owned_resources']==[]
    checks['stale_replay']=c['stale_W1_after_repair']['status']=='STALE_WORLD_GENERATION' and c['stale_W1_after_repair']['effect_id'] is None
    checks['repair_no_fresh']=c['repair_without_fresh_evidence']['status']=='REPAIR_REFUSED' and c['repair_without_fresh_evidence']['versions_before']==c['repair_without_fresh_evidence']['versions_after']
    checks['overbroad']=c['overbroad_repair']['status']=='OVERBROAD_REPAIR_REJECTED' and c['overbroad_repair']['versions_before']==c['overbroad_repair']['versions_after']
    checks['duplicate']=c['duplicate_effect_replay']['status']=='IDEMPOTENT_REPLAY'
    checks['missing']=c['missing_binding_evidence']['status']=='NO_TARGET_AUTHORITY' and c['missing_binding_evidence']['effect_id'] is None
    expected='PASS_MINDUSTRY_PERSISTENT_LIFECYCLE_MECHANICS_SCOPED' if all(checks.values()) else 'FAIL_INTEGRITY'
    checks['decision']=r['decision']==expected
    passed=all(checks.values())
    out={'schema':'mindustry_integrated_lifecycle_mechanics_audit_v1','passed':passed,'decision':r['decision'],'checks':checks,
         'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2)); raise SystemExit(0 if passed else 1)
if __name__=='__main__': main()
