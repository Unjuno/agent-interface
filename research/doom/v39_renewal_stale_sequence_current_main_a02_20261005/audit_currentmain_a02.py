import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parent
freeze = json.loads((root/'FREEZE.json').read_text())
checks = []
snapshots = {
    'research/doom/map01_overlap_controller_v39.py':'baseline_map01_overlap_controller_v39.py',
    'research/doom/doom_controller_failure_cleanup_v1.py':'baseline_doom_controller_failure_cleanup_v1.py',
}
for path, identity in freeze['sources'].items():
    file = root/snapshots[path]
    raw = file.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    checks.append({'check':'source_sha256','path':path,'pass':actual==identity['sha256'] and len(raw)==identity['bytes'],'sha256':actual,'bytes':len(raw)})
runner = json.loads((root/'PROCESS_RESULTS.json').read_text())
checks.append({'check':'normal_exit_0','pass':runner['normal']['exit_code']==0})
checks.append({'check':'optimized_exit_0','pass':runner['optimized']['exit_code']==0})
checks.append({'check':'py_compile_exit_0','pass':runner['py_compile']['exit_code']==0})
for mode in ('normal','optimized'):
    observed = json.loads((root/f'observed_{mode}.json').read_text())
    cleanup = observed['failure_cleanup']
    timeline = observed['timeline']
    checks.extend([
        {'check':f'{mode}_sequence_7_to_8','pass':observed['initial_expected_sequence']==7 and observed['new_observation_sequence']==8},
        {'check':f'{mode}_stale_rejection','pass':observed['submission_response']=={'event':'rejected','id':'cover-0-renew-1','reason':'latest observation sequence required before input'}},
        {'check':f'{mode}_expected_runtime_error','pass':observed['raised_exception']['type']=='RuntimeError' and 'latest observation sequence required before input' in observed['raised_exception']['text']},
        {'check':f'{mode}_no_planner_interrupt','pass':observed['planner_interrupt_count']==0 and 'planner_interrupted' not in timeline},
        {'check':f'{mode}_await_precedes_cleanup_close','pass':timeline.index('stale_sequence_rejection_consumed')<timeline.index('planner_await_returned')<timeline.index('planner_closed')},
        {'check':f'{mode}_prior_release_empty','pass':cleanup['input_terminals_complete'] and cleanup['input_releases_verified_empty'] and not cleanup['input_release_verified']},
        {'check':f'{mode}_cleanup_incomplete','pass':not cleanup['scorer_terminal_observed'] and not cleanup['score_file_present'] and not cleanup['owner_events_closed'] and not cleanup['cleanup_complete']},
        {'check':f'{mode}_no_live_input','pass':observed['live_game_or_native_input'] is False},
    ])
if not all(row['pass'] for row in checks):
    raise SystemExit(json.dumps([row for row in checks if not row['pass']],indent=2))
result = {'schema':'v39-renewal-stale-sequence-frozen-source-a02-audit-v2','disposition':'FROZEN_SOURCE_STALE_RENEWAL_REJECTION_REPRODUCED','main_sha':freeze['main_sha'],'test_modes':['normal','optimized'],'checks':checks,'scope':freeze['limits']}
(root/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
files = sorted(p for p in root.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt')
(root/'SHA256SUMS.txt').write_text('\n'.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}' for p in files)+'\n',encoding='utf-8')
print(json.dumps({'disposition':result['disposition'],'checks':len(checks),'passed':sum(row['pass'] for row in checks),'audit_sha256':hashlib.sha256((root/'AUDIT.json').read_bytes()).hexdigest(),'manifest_entries':len(files)}))

