import json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
freeze=json.loads((p/'FREEZE.json').read_text(encoding='utf-8')); rows=json.loads((p/'reduced_trace.json').read_text(encoding='utf-8')); result=json.loads((p/'RESULT.json').read_text(encoding='utf-8'))
pairs=list(zip(rows,rows[1:]))
checks={
 'posthoc_status_preserved':freeze['kind'].startswith('posthoc') and result['status']=='POSTHOC_DESCRIPTIVE_ONLY',
 'source_identity_pinned':result['source_sha256']==freeze['source_sha256'],
 'typed_row_count':len(rows)==170 and result['typed_observation_count']==170,
 'sequences_strictly_advance':all(b['sequence']>a['sequence'] for a,b in pairs),
 'all_frame_hashes_change':sum(a['frame_rgb_sha256']!=b['frame_rgb_sha256'] for a,b in pairs)==169 and result['frame_hash_changed_pairs']==169,
 'stable_hud_on_changed_frame_count':sum(a['frame_rgb_sha256']!=b['frame_rgb_sha256'] and a['health']==b['health'] and a['ammo']==b['ammo'] for a,b in pairs)==153 and result['frame_changed_and_both_hud_stable_pairs']==153,
 'health_and_ammo_transition_counts':sum(a['health']!=b['health'] for a,b in pairs)==10 and sum(a['ammo']!=b['ammo'] for a,b in pairs)==6,
 'scope_excludes_live_wait_correlation':'Does not correlate' in result['scope'] and 'No correlation with cover-active intervals' in ' '.join(freeze['limits']),
}
print(json.dumps({'status':'PASS_POSTHOC_ARITHMETIC' if all(checks.values()) else 'FAIL_AUDIT','checks':checks},indent=2));sys.exit(0 if all(checks.values()) else 1)