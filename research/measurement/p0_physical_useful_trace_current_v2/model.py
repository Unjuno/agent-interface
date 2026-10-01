from __future__ import annotations
import json,sys
from pathlib import Path
EXPECTED_SEM={
'release_bracket':'PASS_PHYSICAL_RELEASE_BRACKET_CONTRACT_SCOPED',
'press_bracket':'PASS_PHYSICAL_PRESS_BRACKET_CONTRACT_SCOPED',
'dual_edge_adapter':'PASS_PHYSICAL_BRACKET_DUAL_EDGE_ADAPTER_SCOPED',
'dual_edge_occupancy':'PASS_DUAL_EDGE_CENSORING_SCOPED',
'temporal_effect_gate':'PASS_CENSORED_DOWN_TEMPORAL_GATE_SCOPED',
'effect_provenance':'PASS_USEFUL_CONTROL_PROVENANCE_COMPOSITION_SCOPED'}
EXPECTED_IMPL={
'sample_sequencing':'PASS_OWNER_PHYSICAL_SAMPLE_SEQUENCING_SCOPED',
'stable_hold_identity':'PASS_PHYSICAL_HOLD_IDENTITY_AUDITABLE_V4_SCOPED',
'v12_offline':'PASS_INPUT_OWNER_V12_OFFLINE_MECHANICS_SCOPED',
'clock_provenance_gate':'PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_FORMAL_SCOPED'}

def evaluate(f):
    sem={x['id']:x for x in f['semantic_nodes']}; impl={x['id']:x for x in f['implementation_nodes']}; live={x['id']:x for x in f['live_gates']}
    sem_ok=set(sem)==set(EXPECTED_SEM) and all(sem[k]['decision']==v and sem[k]['class']=='SYNTHETIC_CONTRACT' for k,v in EXPECTED_SEM.items())
    impl_ok=set(impl)==set(EXPECTED_IMPL) and all(impl[k]['decision']==v for k,v in EXPECTED_IMPL.items())
    class_ok=(impl['sample_sequencing']['class']=='OFFLINE_RUNTIME_SOURCE' and impl['stable_hold_identity']['class']=='CONSTRUCTION_IDENTITY' and impl['v12_offline']['class']=='OFFLINE_RUNTIME_SOURCE' and impl['clock_provenance_gate']['class']=='SYNTHETIC_CONTRACT')
    live_required={'LIVE_PHYSICAL_EDGE_TRANSFER','LIVE_CAUSAL_EFFECT_SAMPLE','CROSS_PROCESS_CLOCK_AXIS'}
    live_unproven=set(live)==live_required and all(live[x]['status']=='UNPROVEN_CURRENT' for x in live_required)
    plans=f.get('plan_intent_not_evidence',[])
    plans_ok=any(x.get('issue')==1099 and str(x.get('status','')).startswith('QUEUED_') for x in plans) and any(x.get('issue')==60 and x.get('kind')=='LIVE_LEASE_REQUEST_NOT_GRANT' for x in plans) and any(x.get('issue')==1000 and x.get('kind')=='OPEN_CLOCK_CONSTRUCTION_CLAIM_NOT_RESULT' for x in plans)
    offline_ready=sem_ok and impl_ok and class_ok
    same_process_live_ready=offline_ready and live['LIVE_PHYSICAL_EDGE_TRANSFER']['status']=='PROVEN_LIVE' and live['LIVE_CAUSAL_EFFECT_SAMPLE']['status']=='PROVEN_LIVE'
    cross_process_live_ready=same_process_live_ready and live['CROSS_PROCESS_CLOCK_AXIS']['status']=='PROVEN_LIVE'
    passed=(f.get('base')=='51d9f5b3b534286f9a4ac50e6a2321e919300a0d' and offline_ready and live_unproven and plans_ok and not same_process_live_ready and not cross_process_live_ready)
    return {
      'decision':'PASS_P0_CURRENT_GAP_LOCALIZED_SCOPED' if passed else 'FAIL_EVIDENCE_CLASS_INTEGRITY',
      'offline_ready':offline_ready,'semantic_nodes_ok':sem_ok,'implementation_nodes_ok':impl_ok,'evidence_classes_ok':class_ok,
      'live_gates_unproven':live_unproven,'plan_intent_excluded':plans_ok,
      'same_process_live_useful_control_proven':same_process_live_ready,
      'cross_process_live_useful_control_proven':cross_process_live_ready,
      'remaining_current_gates':['LIVE_PHYSICAL_EDGE_TRANSFER','LIVE_CAUSAL_EFFECT_SAMPLE'],
      'cross_process_additional_gate':'CROSS_PROCESS_CLOCK_AXIS',
      'invocations':1,'reruns':0}
if __name__=='__main__':
    p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('facts.json')
    print(json.dumps(evaluate(json.loads(p.read_text())),sort_keys=True,indent=2))
