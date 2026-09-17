import json,hashlib,pathlib
p=pathlib.Path(__file__).parent
s=json.loads((p/'runner_schema.json').read_text())
retained=set(s['ring_trial_fields']+s['jit_trial_fields']+s['arm_fields']+s['top_fields'])
required={
 'raw_frame_content': {'data','frame_data','pixels','image_bytes'},
 'frame_digest': {'frame_hash','frame_digest','image_sha256','payload_sha256'},
 'current_state_identity': {'current_state_id','state_id','current_frame_hash','visual_identity'},
 'rectangle_x': {'x','rect_x','rectangle_x'},
 'rectangle_direction': {'dx','direction','velocity','rect_dx'},
 'history_content_identity': {'selected_frame_hashes','selected_frame_ids','history_frame_hashes'},
 'future_state_label': {'future_state','future_x','future_frame_hash','future_label'},
 'reversal_or_invalidation_label': {'reversal','invalidated','invalidation_reason','direction_changed'},
 'independent_future_outcome': {'future_outcome','oracle_future','future_score','ground_truth_future'}
}
field_presence={k:sorted(v & retained) for k,v in required.items()}
missing=[k for k,v in field_presence.items() if not v]
assert 'frame_bytes' in retained and 'data' not in retained
assert s['capture_transient_only_fields']==['data']
assert 'x' not in retained and 'dx' not in retained
ready=(not missing and s['summary_audit']['ring_trials']>=32)
result={
 'task':'TEMPORAL-SPECULATION-RETAINED-DATA-READINESS-20260918-001',
 'decision':'PASS_RETAINED_SPECULATION_DATA_READY_SCOPED' if ready else 'BLOCKED_DATA_TEMPORAL_SPECULATION_RUNG1',
 'source_blobs':s['source_blobs'],
 'retained_field_count':len(retained),
 'field_presence':field_presence,
 'missing_required_evidence':missing,
 'retained_ring_trials':s['summary_audit']['ring_trials'],
 'retained_jit_trials':s['summary_audit']['jit_trials'],
 'constructible_same_current_alias_pairs_from_retained_evidence':0 if missing else None,
 'constructible_opposite_history_future_disagreement_pairs_from_retained_evidence':0 if missing else None,
 'readiness_gates':{
   'same_current_alias_pairs_ge_32':False if missing else None,
   'opposite_history_future_disagreement_pairs_ge_16':False if missing else None,
   'explicit_fresh_current_identity':bool(field_presence['current_state_identity']),
   'independent_future_label_per_scored_pair':bool(field_presence['future_state_label'] or field_presence['independent_future_outcome']),
   'no_replay_or_regeneration_required':False if missing else None
 },
 'minimum_collection_additions':['content-derived current frame digest/state projection','content IDs/digests for retained history frames','observable direction/temporal feature derived from retained frames','future frame digest/state projection at frozen horizon','explicit reversal/invalidation marker or independently derivable retained future transition','per-row source/session/sequence timestamps binding history-current-future'],
 'formal_or_live_actions':0,
 'reruns':0,
 'note':'fixture source documents motion but is not accepted as a retained per-row state/future label'
}
(p/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
