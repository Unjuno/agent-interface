"""Run affected MAP01 local/Fake X regressions in isolated Python processes.

No live resource allocation. A fresh output directory preserves every first result.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

MODULES = [
    'research.live_control.test_appserver_close_waiter_stop',
    'research.live_control.test_app_server_eof_stop',
    'research.live_control.test_app_server_known_eof',
    'research.live_control.test_app_server_reply_id_5156',
    'research.live_control.test_appserver_bounded_close_e0cc',
    'research.live_control.test_codex_app_server_send_deadline_v1',
    'research.live_control.test_appserver_journal_close_01a0ff2d',
    'research.live_control.test_appserver_process_tree_cleanup_20261004',
    'research.live_control.test_input_owner_v12_process_identity',
    'research.live_control.test_input_owner_v12_explicit_up_cancel',
    'research.live_control.test_input_owner_v12_cleanup_after_explicit_up',
    'research.live_control.test_input_owner_v12_terminal_presample_release',
    'research.live_control.test_input_owner_v12_wheel_cleanup',
    'research.live_control.test_input_transition_owner_v4',
    'research.live_control.test_input_transition_owner_v3',
    'research.live_control.test_input_transition_owner_v3_owner_queue',
    'research.live_control.test_input_transition_owner_v15_cleanup_lease_identity',
    'research.live_control.test_input_transition_owner_v15_cancelled_up_batch',
    'research.live_control.test_executor_v12',
    'research.live_control.test_executor_v13',
    'research.live_control.test_executor_v12_owner_release_rpc_failure',
    'research.live_control.test_executor_owner_cancel_cause_v1',
    'research.live_control.test_lease',
    'research.live_control.test_running_action_guard_v1',
    'research.live_control.test_running_action_guard_v2',
    'research.live_control.test_running_action_guard_v3',
    'research.doom.test_map01_process_identity_backend',
    'research.doom.test_map01_window_lifecycle',
    'research.doom.test_map01_unverified_release_custody',
    'research.doom.test_map01_backend_executor_custody',
    'research.doom.test_map01_session_retirement_boundary',
    'research.doom.test_session_map01_v12_cleanup',
    'research.doom.test_controller_retirement_failure',
    'research.doom.test_controller_failure_cleanup_v1',
    'research.doom.test_v39_cancel_release_failure',
    'research.doom.test_v39_cover_local_invalidation',
    'research.doom.test_v39_terminal_release_receipt_completeness',
    'research.live_control.test_persistent_planner_adapter_v2',
    'research.doom.test_cancel_invalidated_cover_order',
    'research.doom.test_v39_cancel_composition_saved_v2',
    'research.doom.test_map01_identity_selection',
    'research.doom.test_session_map01_v15',
    'research.doom.test_doom_typed_release_backend_v2',
    'research.doom.test_doom_typed_release_backend_v3',
    'research.doom.test_release_backend_v3_composition',
    'research.doom.test_release_backend_v3_actual_composition',
    'research.doom.test_map01_overlap_controller_v39',
    'research.doom.test_map01_overlap_controller_v39_cover_terminal',
    'research.doom.test_map01_overlap_controller_v39_dual_signal',
    'research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency',
    'research.doom.test_map01_overlap_controller_v39_mcp_preflight',
    'research.doom.test_map01_overlap_controller_v39_appserver_command',
    'research.doom.test_map01_v39_pending_observation_drain',
    'research.doom.test_doom_typed_observation_epoch_exact',
    'research.doom.test_doom_typed_artifact_reconciliation_v1',
    'runtime.guarded_x11_v1.test_target_queries',
    'runtime.guarded_x11_v1.test_process_identity',
    'runtime.guarded_x11_v1.test_window_lifecycle',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--optimized', action='store_true')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(map(str, (
        root, root / 'research/live_control', root / 'research/doom')))
    # This suite deliberately skips the optional real-Codex handshake.
    env['CODEX_CLI_PATH'] = ''
    env['AGENT_INTERFACE_CODEX_APP_SERVER_EXE'] = ''
    rows = []
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True)
    for module in MODULES:
        command = [sys.executable] + (['-O'] if args.optimized else []) + ['-m', 'unittest', module]
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
        output = result.stdout + result.stderr
        (args.output_dir / (module + '.log')).write_text(output, encoding='utf-8')
        count = re.search(r'Ran (\d+) tests?', output)
        skipped = re.search(r'skipped=(\d+)', output)
        row = dict(module=module, exit=result.returncode,
                   tests=int(count[1]) if count else 0,
                   skipped=int(skipped[1]) if skipped else 0)
        rows.append(row)
        print(json.dumps(row), flush=True)
    report = dict(head=head, dirty_status=dirty, optimized=args.optimized,
                  modules=len(rows), tests=sum(row['tests'] for row in rows),
                  skipped=sum(row['skipped'] for row in rows),
                  failed_modules=[row for row in rows if row['exit']], rows=rows,
                  scope='isolated local/Fake X checks; optional real-Codex handshake skipped')
    (args.output_dir / 'summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return bool(report['failed_modules'])


if __name__ == '__main__':
    raise SystemExit(main())
