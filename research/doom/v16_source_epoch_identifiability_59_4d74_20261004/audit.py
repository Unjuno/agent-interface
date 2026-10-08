"""Independent audit of the V16 source-epoch identifiability result."""
import hashlib
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
freeze=json.loads((ROOT/'FREEZE.json').read_text(encoding='utf-8-sig'))
result=json.loads((ROOT/'result.json').read_text(encoding='utf-8'))
runner=json.loads((ROOT/'runner-attempt-01.json').read_text(encoding='utf-8'))
repo=Path(__file__).resolve().parents[3]

def blob(path):
    return subprocess.run(['git','-C',str(repo),'rev-parse',f"{freeze['main_commit']}:{path}"],
        check=True,capture_output=True,text=True).stdout.strip()

checks={
    'clock_blob_pinned':blob('research/doom/independent_progress_clock_v2.py')==freeze['clock_blob'],
    'sampler_blob_pinned':blob('research/doom/acknowledged_scorer_v1.py')==freeze['acknowledged_scorer_blob'],
    'main_commit_matches':result['main_commit']==freeze['main_commit'],
    'counterexample_status':result['status']=='PASS_COUNTEREXAMPLE',
    'runner_checks_all_pass':all(result['checks'].values()),
    'current_states_differ':result['fresh_current_kills']==2 and result['stale_world_current_kills']==3,
    'reported_samples_equal':result['fresh_reported_samples']==result['stale_reported_samples'],
    'client_update_rows_equal':result['fresh_client_update_rows']==result['stale_client_update_rows'],
    'progress_events_equal':result['fresh_progress_clock_events']==result['stale_progress_clock_events'],
    'one_event_emitted':len(result['stale_progress_clock_events'])==1,
    'event_is_kill_increase':result['stale_progress_clock_events'][0]['kind']=='KILL_COUNT_INCREASE',
    'event_time_matches_sample':result['stale_progress_clock_events'][0]['observed_ns']==60,
}
producer=result['stale_reported_samples'][-1]['producer']
checks['wrapper_identity_present']=producer['run_id']=='fixed-current-run' and producer['update_sequence']==2
checks['source_epoch_missing']='source_epoch' not in producer
checks['failed_attempt_retained']=runner['status']=='STOP_BEFORE_CANDIDATE_RESULT' and runner['candidate_calls_completed']==0
inventory=json.loads((ROOT/'FILES.sha256.json').read_text(encoding='utf-8'))
for rel,expected in inventory.items():
    actual=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    checks[f'file_hash:{rel}']=actual==expected
assert all(checks.values()),checks
print(json.dumps({'schema':'v16-source-epoch-probe-a01-audit-v1','status':'PASS',
    'checks':len(checks),'failure_attempt_retained':True,
    'scope':result['scope']},indent=2))
