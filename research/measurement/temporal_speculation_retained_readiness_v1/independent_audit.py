import json,hashlib,pathlib,copy
p=pathlib.Path(__file__).parent
r=json.loads((p/'RESULT.json').read_text()); errs=[]
expected_missing={'raw_frame_content','frame_digest','current_state_identity','rectangle_x','rectangle_direction','history_content_identity','future_state_label','reversal_or_invalidation_label','independent_future_outcome'}
if r['decision']!='BLOCKED_DATA_TEMPORAL_SPECULATION_RUNG1': errs.append('decision')
if set(r['missing_required_evidence'])!=expected_missing: errs.append('missing_set')
if r['constructible_same_current_alias_pairs_from_retained_evidence']!=0: errs.append('invented_alias_pairs')
if r['constructible_opposite_history_future_disagreement_pairs_from_retained_evidence']!=0: errs.append('invented_future_pairs')
if r['formal_or_live_actions']!=0 or r['reruns']!=0: errs.append('allocation_drift')
if r['source_blobs']['runner.py']!='c495fad798cc325bd2321a097bd6a3acff081c15': errs.append('runner_identity')
if r['source_blobs']['FORMAL_RESULT.json.gz']!='c36a8c46dfad5e8c1ed01ffd1a0d2864b6ab8bfc': errs.append('result_identity')
mutations=[]
for name,mut in [
 ('invent_hash',lambda x:x['missing_required_evidence'].remove('frame_digest')),
 ('invent_alias_pairs',lambda x:x.__setitem__('constructible_same_current_alias_pairs_from_retained_evidence',32)),
 ('invent_future_pairs',lambda x:x.__setitem__('constructible_opposite_history_future_disagreement_pairs_from_retained_evidence',16)),
 ('promote_decision',lambda x:x.__setitem__('decision','PASS_RETAINED_SPECULATION_DATA_READY_SCOPED')),
 ('fake_current_identity',lambda x:x['readiness_gates'].__setitem__('explicit_fresh_current_identity',True)),
 ('fake_future_label',lambda x:x['readiness_gates'].__setitem__('independent_future_label_per_scored_pair',True))]:
    y=copy.deepcopy(r); mut(y); mutations.append({'name':name,'rejected':y!=r})
a={'passed':not errs and all(x['rejected'] for x in mutations),'errors':errs,'mutations':mutations,'result_sha256':hashlib.sha256((p/'RESULT.json').read_bytes()).hexdigest()}
(p/'AUDIT.json').write_text(json.dumps(a,indent=2,sort_keys=True)+'\n')
print(json.dumps(a,sort_keys=True))
