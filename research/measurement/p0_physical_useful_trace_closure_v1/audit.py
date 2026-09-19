from __future__ import annotations
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
f=json.loads((HERE/'fixture.json').read_text()); r=json.loads((HERE/'RESULT.json').read_text())
nodes={x['id']:x for x in f['semantic_nodes']}; gates={x['id']:x for x in f['runtime_live_gates']}
expected={'release_bracket':'PASS_PHYSICAL_RELEASE_BRACKET_CONTRACT_SCOPED','press_bracket':'PASS_PHYSICAL_PRESS_BRACKET_CONTRACT_SCOPED','dual_edge_adapter':'PASS_PHYSICAL_BRACKET_DUAL_EDGE_ADAPTER_SCOPED','dual_edge_occupancy':'PASS_DUAL_EDGE_CENSORING_SCOPED','temporal_effect_gate':'PASS_CENSORED_DOWN_TEMPORAL_GATE_SCOPED','effect_provenance':'PASS_USEFUL_CONTROL_PROVENANCE_COMPOSITION_SCOPED'}
checks={
 'decision':r['decision']=='PASS_P0_CAUSAL_TRACE_GAP_LOCALIZED_SCOPED',
 'six_semantic_nodes':len(nodes)==6 and all(nodes[k]['decision']==v and nodes[k]['proven'] is True for k,v in expected.items()),
 'semantic_classes':all(v['evidence_class']=='SYNTHETIC_CONTRACT' for v in nodes.values()),
 'three_gates':set(gates)=={'OWNER_EDGE_PRODUCER','STABLE_HOLD_IDENTITY','LIVE_CAUSAL_SAMPLE'},
 'gates_unproven':all(v['status']=='UNPROVEN_AT_BASE' for v in gates.values()),
 'gate_classes':gates['OWNER_EDGE_PRODUCER']['evidence_class']=='RUNTIME_RECEIPT' and gates['STABLE_HOLD_IDENTITY']['evidence_class']=='RUNTIME_RECEIPT' and gates['LIVE_CAUSAL_SAMPLE']['evidence_class']=='LIVE_EFFECT',
 'active_not_evidence':f['active_work_not_evidence']==[998,999],
 'live_false':r['live_useful_control_proven'] is False,
 'formal':r['formal_invocations']==1 and r['reruns']==0}
a={'schema':'p0_physical_useful_trace_audit_v1','passed':all(checks.values()),'checks':checks,'errors':[k for k,v in checks.items() if not v]}
(HERE/'AUDIT.json').write_text(json.dumps(a,indent=2,sort_keys=True)+'\n'); print(json.dumps(a,sort_keys=True))
