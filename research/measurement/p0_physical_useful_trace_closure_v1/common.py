from __future__ import annotations
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
EXPECTED_DECISIONS={
'release_bracket':'PASS_PHYSICAL_RELEASE_BRACKET_CONTRACT_SCOPED',
'press_bracket':'PASS_PHYSICAL_PRESS_BRACKET_CONTRACT_SCOPED',
'dual_edge_adapter':'PASS_PHYSICAL_BRACKET_DUAL_EDGE_ADAPTER_SCOPED',
'dual_edge_occupancy':'PASS_DUAL_EDGE_CENSORING_SCOPED',
'temporal_effect_gate':'PASS_CENSORED_DOWN_TEMPORAL_GATE_SCOPED',
'effect_provenance':'PASS_USEFUL_CONTROL_PROVENANCE_COMPOSITION_SCOPED'}
REQUIRED_GATES=['OWNER_EDGE_PRODUCER','STABLE_HOLD_IDENTITY','LIVE_CAUSAL_SAMPLE']

def load_fixture(path: Path|None=None):
    return json.loads((path or HERE/'fixture.json').read_text())

def evaluate(f):
    nodes={n['id']:n for n in f['semantic_nodes']}
    gates={g['id']:g for g in f['runtime_live_gates']}
    identity_ok=(f.get('base')=='159dd3684ffcd0ee78b9ff5939e0173cd77c7b4f' and
      all(nodes.get(k,{}).get('decision')==v and nodes.get(k,{}).get('proven') is True and nodes.get(k,{}).get('evidence_class')=='SYNTHETIC_CONTRACT' for k,v in EXPECTED_DECISIONS.items()))
    expected_edges={('press_bracket','dual_edge_adapter'),('release_bracket','dual_edge_adapter'),('dual_edge_adapter','dual_edge_occupancy'),('dual_edge_occupancy','temporal_effect_gate'),('temporal_effect_gate','effect_provenance')}
    semantic_connected=set(map(tuple,f['semantic_edges']))==expected_edges
    gates_unproven=(set(gates)==set(REQUIRED_GATES) and all(gates[x].get('status')=='UNPROVEN_AT_BASE' for x in REQUIRED_GATES))
    active_not_evidence=sorted(f.get('active_work_not_evidence',[]))==[998,999]
    live_proven = identity_ok and semantic_connected and gates_unproven is False and set(gates)==set(REQUIRED_GATES) and all(gates.get(x,{}).get('status')=='PROVEN_LIVE' for x in REQUIRED_GATES)
    class_ok=all(n.get('evidence_class')=='SYNTHETIC_CONTRACT' for n in nodes.values()) and set(gates)==set(REQUIRED_GATES) and all(gates.get(x,{}).get('evidence_class') in ('RUNTIME_RECEIPT','LIVE_EFFECT') for x in REQUIRED_GATES)
    passed=identity_ok and semantic_connected and gates_unproven and active_not_evidence and class_ok and not live_proven
    return {
      'decision':'PASS_P0_CAUSAL_TRACE_GAP_LOCALIZED_SCOPED' if passed else 'FAIL_EVIDENCE_CLASS_INTEGRITY',
      'identity_ok':identity_ok,'semantic_connected':semantic_connected,'runtime_live_gates_unproven':gates_unproven,
      'active_work_not_evidence':active_not_evidence,'evidence_class_firewall':class_ok,
      'live_useful_control_proven':live_proven,'unproven_gates':REQUIRED_GATES if gates_unproven else [],
      'semantic_node_count':len(nodes),'formal_invocations':1,'reruns':0}
