"""Saved-data baseline reduction, no inference producer replay."""
import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
raw=(root/'first-result.json').read_bytes();j=json.loads(raw.decode('utf-8-sig'))
truths=sum(d['truth_shared'] for r in j['rows'] for d in r['decisions'])
claims=j['metrics']['intervention']['true_edges']
cost=json.loads((root/'supplement-first.json').read_text(encoding='utf-8-sig'))
print(json.dumps(dict(input_sha256=hashlib.sha256(raw).hexdigest(),pair_decisions=2187,declared_graph=dict(true_claims=truths,false_claims=0,probes=0,condition='complete trustworthy current service assignment metadata is available'),intervention=dict(true_claims=claims,false_claims=j['metrics']['intervention']['false_edges'],missed_shared_pairs=truths-claims,probes=cost['probe_jobs'],added_service_ticks=cost['probe_service_ticks'],added_task_endpoint_ticks=cost['aggregate_probe_added_endpoint_ticks']),decision='PREFER_EXPLICIT_METADATA_WHEN_QUALIFIED; HOLD_OPERATIONAL_PROBING_WITHOUT_METADATA_OR_MATCHED_EVIDENCE',scope='metadata oracle is conditional fixture baseline, not evidence real backend metadata exists or is current'),indent=2))
