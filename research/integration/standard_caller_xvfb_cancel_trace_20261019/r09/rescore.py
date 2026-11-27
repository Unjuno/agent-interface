"""Re-score preserved run 39276306835 receipts with the merged synthetic oracle."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from runtime.cli_v1.test_synthetic_task_oracle import score_synthetic_application_task

RAW = Path(__file__).resolve().parent / 'raw'
rows = []
for path in sorted(RAW.glob('standard-mcp-xvfb-*.json')):
    if 'blocked-release' not in path.name and 'cancel-retirement-' not in path.name:
        continue
    raw = json.loads(path.read_text(encoding='utf-8'))
    score = score_synthetic_application_task(
        initial_effect=raw.get('effect_before_cancel', {}).get('property_value'),
        final_effect=raw.get('synthetic_application_effect', {}).get('property_value'),
        release_readback=raw.get('independent_release_readback', {}).get('keys_down'),
        horizon_readback=raw.get('late_request_horizon_readback', {}).get('keys_down'))
    row = {
        'file': path.name,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'workflow_status': raw.get('status'),
        'cancel_status': raw.get('cancel', {}).get('status'),
        'cancel_elapsed_ms': raw.get('cancel_elapsed_ms'),
        'owner_retired': raw.get('cancel', {}).get('owner_process_retired'),
        'owner_disconnect_status': raw.get('cancel', {}).get('owner_client_disconnect', {}).get('status'),
        'release_attempt_status': raw.get('cancel', {}).get('owner_release_attempt', {}).get('status'),
        'release_elapsed_ms': raw.get('cancel', {}).get('owner_release_attempt', {}).get('elapsed_ms'),
        'independent_task_oracle': score,
        'runtime_task_success': raw.get('cancel', {}).get('task_success'),
        'release_confirmed': raw.get('cancel', {}).get('release_confirmed'),
        'cleanup_status': raw.get('cancel', {}).get('cleanup_status'),
        'replay_allowed': raw.get('cancel', {}).get('replay_allowed'),
        'horizon_late_b_press': raw.get('late_request_horizon_readback', {}).get('late_keypress_b_observed'),
    }
    if score.get('status') != 'pass' or row['runtime_task_success'] is not None:
        raise SystemExit(f'unexpected rescore state: {path.name}: {row}')
    rows.append(row)
if len(rows) != 5:
    raise SystemExit(f'expected five blocked-release receipts, found {len(rows)}')
negative = score_synthetic_application_task(
    initial_effect=[1], final_effect=[1],
    release_readback={'a': False, 'b': False},
    horizon_readback={'a': True, 'b': False})
if negative.get('status') != 'fail' or negative.get('task_success') is not False:
    raise SystemExit(f'negative control did not fail: {negative}')
generation_path = RAW / 'standard-mcp-xvfb-generation.json'
generation = json.loads(generation_path.read_text(encoding='utf-8'))
ticks = generation['monotonic_ns']
generation_timing = {
    'file': generation_path.name,
    'sha256': hashlib.sha256(generation_path.read_bytes()).hexdigest(),
    'scenario_status': generation.get('status'),
    'observation_call_ms': (ticks['observe_returned'] - ticks['observe_started']) / 1_000_000,
    'recovery_to_independent_keyup_readback_ms': generation.get('recovery_elapsed_ms'),
    'recovery_fault_effect_commit_from_call_start_ms': generation.get(
        'recovery_app_effect_before_release', {}).get('call_start_to_effect_commit_ms'),
    'post_recovery_effect_commit_from_call_start_ms': generation.get(
        'post_recovery_task_oracle', {}).get('call_start_to_effect_commit_ms'),
    'process_generation': generation.get('observe', {}).get(
        'source', {}).get('pointer_binding', {}).get('process_generation'),
    'window_generation': generation.get('observe', {}).get(
        'source', {}).get('pointer_binding', {}).get('window_generation'),
    'post_recovery_effect': generation.get('post_recovery_task_oracle'),
    'runtime_task_success': generation.get('post_recovery_task_oracle', {}).get(
        'runtime_task_success_api'),
}
if (generation_timing['scenario_status'] != 'PASS_SCOPED_XVFB_STANDARD_CALLER_RECOVERY'
        or generation_timing['runtime_task_success'] is not None
        or generation_timing['recovery_to_independent_keyup_readback_ms'] >= 3000.0):
    raise SystemExit(f'unexpected generation/recovery report: {generation_timing}')
result = {
    'schema': 'agent-interface/synthetic-task-oracle-rescore-v1',
    'source_run': 'https://github.com/Unjuno/agent-interface/actions/runs/39276306835',
    'source_head': 'f4e02b64f0d324ffa8c3525a9f822691c1e06fa4',
    'scorer': 'runtime.cli_v1.test_synthetic_task_oracle.score_synthetic_application_task',
    'scope': 'offline independent re-score of preserved standard-caller private-Xvfb receipts; does not change raw runtime results',
    'rows': rows,
    'negative_control_horizon_a_still_down': negative,
    'separate_generation_recovery_scenario': generation_timing,
}
Path(__file__).resolve().parent.joinpath('offline-rescore.json').write_text(
    json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'rows': len(rows), 'scores': [row['independent_task_oracle']['status'] for row in rows],
                  'runtime_task_success': [row['runtime_task_success'] for row in rows],
                  'negative_control': negative,
                  'generation_recovery_ms': generation_timing[
                      'recovery_to_independent_keyup_readback_ms'],
                  'post_recovery_effect_ms': generation_timing[
                      'post_recovery_effect_commit_from_call_start_ms']}, sort_keys=True))
