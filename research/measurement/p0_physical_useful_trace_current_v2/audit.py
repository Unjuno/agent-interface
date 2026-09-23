from __future__ import annotations
import json,sys
from pathlib import Path
SEM={
'release_bracket':('SYNTHETIC_CONTRACT','PASS_PHYSICAL_RELEASE_BRACKET_CONTRACT_SCOPED','e5166e924b6c1cb5d99f5dde6f5b29ef6014dff0'),
'press_bracket':('SYNTHETIC_CONTRACT','PASS_PHYSICAL_PRESS_BRACKET_CONTRACT_SCOPED','ffc1eec9bbf30843515b1ca0c5fcbd5a9a525e50'),
'dual_edge_adapter':('SYNTHETIC_CONTRACT','PASS_PHYSICAL_BRACKET_DUAL_EDGE_ADAPTER_SCOPED','6cda6cf2f91b3e23e3758bffbdcaae8c444e615d'),
'dual_edge_occupancy':('SYNTHETIC_CONTRACT','PASS_DUAL_EDGE_CENSORING_SCOPED','b534ac82996622e7d6ab337f408ebaf9322e5c52ed3e1f258075f6f1a5923165'),
'temporal_effect_gate':('SYNTHETIC_CONTRACT','PASS_CENSORED_DOWN_TEMPORAL_GATE_SCOPED','7e1806486e83699b3a6d118a44731f8e9f4aad24'),
'effect_provenance':('SYNTHETIC_CONTRACT','PASS_USEFUL_CONTROL_PROVENANCE_COMPOSITION_SCOPED','db1f4a497464897cb9b28e27b08ab09e4ab36c59')}
IMPL={
'sample_sequencing':('OFFLINE_RUNTIME_SOURCE','PASS_OWNER_PHYSICAL_SAMPLE_SEQUENCING_SCOPED','17806e9ee6da361eb160f907c8cf993689dedad2'),
'stable_hold_identity':('CONSTRUCTION_IDENTITY','PASS_PHYSICAL_HOLD_IDENTITY_AUDITABLE_V4_SCOPED','11017cc3298061ced9cb3eb16016a4c35c94dd15'),
'v12_offline':('OFFLINE_RUNTIME_SOURCE','PASS_INPUT_OWNER_V12_OFFLINE_MECHANICS_SCOPED','fbc43a770865274adf716e6959f4e072be774fc7'),
'clock_provenance_gate':('SYNTHETIC_CONTRACT','PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_FORMAL_SCOPED','2a4bec93f5df774df2c0456d390c60d9d5363dc3')}
def audit(f,r):
    e=[]
    if f.get('base')!='51d9f5b3b534286f9a4ac50e6a2321e919300a0d':e.append('base')
    sem={x.get('id'):x for x in f.get('semantic_nodes',[])}; imp={x.get('id'):x for x in f.get('implementation_nodes',[])}; live={x.get('id'):x for x in f.get('live_gates',[])}
    if set(sem)!=set(SEM):e.append('semantic_set')
    for k,(c,d,s) in SEM.items():
        x=sem.get(k,{})
        if (x.get('class'),x.get('decision'),x.get('source_id'))!=(c,d,s):e.append('semantic:'+k)
    if set(imp)!=set(IMPL):e.append('implementation_set')
    for k,(c,d,s) in IMPL.items():
        x=imp.get(k,{})
        if (x.get('class'),x.get('decision'),x.get('source_id'))!=(c,d,s):e.append('implementation:'+k)
    if imp.get('v12_offline',{}).get('source_bundle_sha256')!='5960543c9d9193b5615da2b545eb7a385a4d2e17bfe12513731bf9e92f948422':e.append('v12_bundle')
    if imp.get('v12_offline',{}).get('v12_sha256')!='b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508':e.append('v12_source')
    exp={'LIVE_PHYSICAL_EDGE_TRANSFER':('LIVE_PHYSICAL_RECEIPT','UNPROVEN_CURRENT'),'LIVE_CAUSAL_EFFECT_SAMPLE':('LIVE_EFFECT','UNPROVEN_CURRENT'),'CROSS_PROCESS_CLOCK_AXIS':('LIVE_CLOCK_RELATION','UNPROVEN_CURRENT')}
    if set(live)!=set(exp):e.append('live_set')
    for k,(c,s) in exp.items():
        x=live.get(k,{})
        if (x.get('class'),x.get('status'))!=(c,s):e.append('live:'+k)
    plans=f.get('plan_intent_not_evidence',[])
    if not any(x.get('issue')==1099 and str(x.get('status','')).startswith('QUEUED_') for x in plans):e.append('1099_intent')
    if not any(x.get('issue')==60 and x.get('kind')=='LIVE_LEASE_REQUEST_NOT_GRANT' for x in plans):e.append('lease_intent')
    if not any(x.get('issue')==1000 and x.get('kind')=='OPEN_CLOCK_CONSTRUCTION_CLAIM_NOT_RESULT' for x in plans):e.append('clock_claim_intent')
    expected={'decision':'PASS_P0_CURRENT_GAP_LOCALIZED_SCOPED','offline_ready':True,'same_process_live_useful_control_proven':False,'cross_process_live_useful_control_proven':False,'live_gates_unproven':True,'plan_intent_excluded':True}
    for k,v in expected.items():
        if r.get(k)!=v:e.append('result:'+k)
    if r.get('remaining_current_gates')!=['LIVE_PHYSICAL_EDGE_TRANSFER','LIVE_CAUSAL_EFFECT_SAMPLE']:e.append('remaining_gates')
    return {'audit_pass':not e,'errors':e}
if __name__=='__main__':
    f=json.loads(Path(sys.argv[1]).read_text());r=json.loads(Path(sys.argv[2]).read_text());print(json.dumps(audit(f,r),sort_keys=True,indent=2))
