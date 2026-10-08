import json,sys
from pathlib import Path
p=Path(__file__).resolve().parent; f=json.loads((p/'FREEZE.json').read_text()); t=json.loads((p/'reduced_trace.json').read_text()); r=json.loads((p/'RESULT.json').read_text())
initial=json.loads((p/'AUDIT_INITIAL_FAILURE.json').read_text())
spans=[]
for turn in t['turns']:
 for cover in t['covers']:
  lo=max(turn['start_ns'],cover['start_ns']); hi=min(turn['completed_ns'],cover['end_ns'])
  if lo>=hi: continue
  sample=[o for o in t['observations'] if lo<=o['emit_ns']<=hi]
  if not sample: continue
  pairs=list(zip(sample,sample[1:]))
  spans.append({'turn_index':turn['index'],'cover_id':cover['id'],'overlap_start_ns':lo,'overlap_end_ns':hi,'overlap_ms':(hi-lo)/1e6,'observation_ids':[o['id'] for o in sample],'observation_count':len(sample),'adjacent_pair_count':len(pairs),'frame_hash_changed_pairs':sum(a['frame_rgb_sha256']!=b['frame_rgb_sha256'] for a,b in pairs),'frame_changed_hud_stable_pairs':sum(a['frame_rgb_sha256']!=b['frame_rgb_sha256'] and a['health']==b['health'] and a['ammo']==b['ammo'] for a,b in pairs),'health_changed_pairs':sum(a['health']!=b['health'] for a,b in pairs),'ammo_changed_pairs':sum(a['ammo']!=b['ammo'] for a,b in pairs)})
checks={
 'initial_audit_failure_preserved':initial['status']=='FAIL_AUDIT' and initial['checks']['source_run_labeled_protocol_deviation'] is False and all(v is True for k,v in initial['checks'].items() if k!='source_run_labeled_protocol_deviation'),
 'source_run_labeled_protocol_deviation':'EXPLORATORY_PROTOCOL_DEVIATION' in f['source_run'],
 'source_hashes_match_freeze':r['source_hashes']['runtime_events']==f['runtime_events']['sha256'] and r['source_hashes']['planner_protocol']==f['planner_protocol']['sha256'],
 'six_planner_turns_and_seven_cover_spans':len(t['turns'])==6 and len(t['covers'])==7,
 'all_interval_pairs_recomputed':r['spans']==spans,
 'overlap_summary_recomputed':r['overlap_span_count']==len(spans) and r['observations_in_overlaps']==sum(s['observation_count'] for s in spans) and r['adjacent_pairs_in_overlaps']==sum(s['adjacent_pair_count'] for s in spans) and r['frame_hash_changed_pairs']==sum(s['frame_hash_changed_pairs'] for s in spans) and r['frame_changed_hud_stable_pairs']==sum(s['frame_changed_hud_stable_pairs'] for s in spans),
 'no_semantic_screen_claim':'does not assign semantic meaning' in r['scope'],
}
print(json.dumps({'status':'PASS_POSTHOC_INTERVAL_ARITHMETIC' if all(checks.values()) else 'FAIL_AUDIT','checks':checks},indent=2));sys.exit(0 if all(checks.values()) else 1)