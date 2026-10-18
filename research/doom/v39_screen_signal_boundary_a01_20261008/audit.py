import json, sys
from pathlib import Path
root=Path(__file__).resolve().parent
freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8'))
result=json.loads((root/'candidate-output.json').read_text(encoding='utf-8'))
s=result['screen_only_change']; h=result['typed_hard_crossing']; hit=h['result']
checks={
  'probe_is_labeled_synthetic': freeze['kind']=='synthetic construction boundary; not a live allocation',
  'source_controller_identity_is_frozen': freeze['main_commit']=='a0d0602b89b1f5a05f851728fe90684ec4bfeff5' and freeze['controller_git_blob']=='3f43c261e2de0b54cc1e83d2a9d53fd984d70f0a',
  'source_guard_identity_is_frozen': freeze['guard_git_blob']=='c0955f976e3a0af6ce926f22cee4a5ddf70ef543',
  'frame_hash_differs_in_screen_case': s['frame_hash_changed'] is True,
  'typed_health_ammo_unchanged_in_screen_case': s['health_source']==s['health_current']==100 and s['ammo_source']==s['ammo_current']==50,
  'screen_only_case_does_not_cancel': s['result'] is None,
  'typed_health_crossing_is_below_floor': h['health_current']==79 and hit['outcome']['hard_minimum']==80,
  'typed_hard_crossing_cancels': hit['event']=='paired_signal_invalidation' and hit['reason']=='health:below_hard_minimum' and hit['requires_new_decision'] is True,
  'invalidation_does_not_grant_input_authority': hit['grants_input_authority'] is False and hit['outcome']['grants_input_authority'] is False,
  'scope_disclaims_live_efficacy': 'not live threat efficacy' in result['scope'],
}
print(json.dumps({'status':'PASS_CONSTRUCTION_BOUNDARY' if all(checks.values()) else 'FAIL_AUDIT','checks':checks},indent=2))
sys.exit(0 if all(checks.values()) else 1)