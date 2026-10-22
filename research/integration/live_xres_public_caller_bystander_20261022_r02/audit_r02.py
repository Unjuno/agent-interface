"""Independent result/receipt audit; never starts the experiment runner."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw' / 'r02'
REPO = ROOT.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


conditions = json.loads((RAW / 'CONDITIONS.json').read_text(encoding='utf-8'))
result = json.loads((RAW / 'result.json').read_text(encoding='utf-8'))
public_cancel = result['terminal_result']['cancellation']['result']
worker = result['worker_result']
disconnect = worker['owner_client_disconnect']
bystander = result['bystander']
frozen = {}
for line in (RAW / 'FROZEN-SHA256.txt').read_text(encoding='ascii').splitlines():
    digest, relative = line.split(None, 1)
    frozen[relative] = digest

freeze_checks = {
    relative: sha256(ROOT / relative) == digest
    for relative, digest in frozen.items()
}
source_checks = {}
for relative, expected in conditions['source_blobs'].items():
    actual = subprocess.check_output(
        ['git', 'rev-parse', f"{conditions['source_revision']}:{relative}"],
        cwd=REPO, text=True).strip()
    source_checks[relative] = actual == expected

checks = {
    'frozen_runner_protocol_hashes_match': all(freeze_checks.values()),
    'source_blob_identities_match': all(source_checks.values()),
    'one_formal_trial_recorded': result.get('trial_count') == 1,
    'public_observe_and_mint_succeeded': (
        result['observation']['status'] == 'observed'
        and result['mint']['status'] == 'minted'),
    'owner_reached_real_sync_block': (
        result['owner_sync_marker']['call'] == 'python-xlib Display.sync'
        and result['delayed_request_marker']['blocked_boundary']
        == 'real python-xlib Display.sync response wait'),
    'bystander_naturally_reused_retired_base': (
        bystander['same_resource_base'] is True
        and bystander['owner_resource_base'] == bystander['bystander_resource_base']),
    'bystander_pid_differs_from_owner': (
        bystander['owner_pid'] != bystander['bystander_pid']),
    'bystander_pid_is_xres_observed_pid': (
        disconnect['observed_pid'] == bystander['bystander_pid']),
    'worker_refused_for_stale_owner_identity': (
        worker['status'] == 'unknown'
        and worker['reason'] == 'stale_owner_identity'
        and disconnect['reason'] == 'resource_base_reused_by_unrelated_client'),
    'worker_did_not_attempt_release': (
        worker['owner_release_attempt']['status'] == 'not_attempted'
        and worker['release_confirmed'] is False),
    'independent_keymap_still_down_after_worker': (
        result['key_down_after_cleanup']['a'] is True),
    'public_cancellation_remained_unknown_and_replay_denied': (
        public_cancel['cleanup_status'] == 'UNKNOWN'
        and public_cancel['release_confirmed'] is False
        and public_cancel['task_success'] is None
        and public_cancel['replay_allowed'] is False),
    'caller_cancel_response_returned_pending': (
        result['cancel_response']['status'] == 'pending'
        and result['cancel_response']['cancellation']['status'] == 'pending'),
    'terminal_cancel_receipt_preserved_unknown': (
        result['terminal_result']['cancellation']['status'] == 'completed'
        and result['terminal_result']['status'] == 'runtime_failed'),
    'delayed_request_horizon_readback_neutral': (
        not any(result['key_down_after_late_horizon'].values())),
    'harness_final_key_state_neutral': (
        not any(result['key_down_after_harness_cleanup'].values())),
    'owner_and_bystander_closed': (
        result['owner_sync_marker']['owner_pid'] == result['bystander']['owner_pid']
        and result['bystander_closed']['stop_seen'] is True),
    'xvfb_cleanup_recorded': (
        'xvfb_alive_after_cleanup=false'
        in (RAW / 'preflight.txt').read_text(encoding='utf-8')),
    'runner_exit_zero': (RAW / 'runner.exit').read_text().strip() == '0',
}
report = {
    'schema': 'agent-interface/live-xres-public-caller-bystander-audit-r02-v1',
    'status': 'PASS_SCOPED' if all(checks.values()) else 'HOLD_OR_FAIL',
    'checks': checks,
    'failed': [name for name, passed in checks.items() if not passed],
    'frozen_file_checks': freeze_checks,
    'source_blob_checks': source_checks,
    'claim_limits': [
        'one WSL2 private-Xvfb sample', 'test-only supervisor target wrapper',
        'no global XTest input exclusivity proof', 'no physical GUI/MAP01',
        'no task-success promotion', 'not a broad reliability estimate',
        'no matched efficiency claim', 'no WSLc portability claim'],
}
(RAW / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, sort_keys=True))
if report['failed']:
    raise SystemExit(1)
