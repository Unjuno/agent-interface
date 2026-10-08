import json,sys
from pathlib import Path
p=Path(sys.argv[1]); r=json.loads(p.read_text())
expected={'valid_pair_preserves_cover':None,'health_ammo_sequence_mismatch':'signal_pair_epoch_mismatch','health_ammo_capture_mismatch':'signal_pair_epoch_mismatch','health_ammo_binding_mismatch':'signal_pair_epoch_mismatch','health_below_floor':'health:below_floor','ammo_below_floor':'ammo:below_floor','duplicate_epoch_same_projection':None,'duplicate_epoch_frame_disagreement':'signal_pair_duplicate_epoch_mismatch','missing_typed_signal':'signal_pair_epoch_mismatch'}
assert r['case_count']==len(expected)
assert all(c['case'] in expected and c['expected']==expected[c['case']] and c['observed']==expected[c['case']] for c in r['cases'])
assert len({c['case'] for c in r['cases']})==len(expected)
assert r['real_input_used'] is False and r['live_game_used'] is False and r['planner_used'] is False
print(json.dumps({'independent_audit':'PASS','checks':len(expected)+3,'source_sha256':r['source_sha256']}))
