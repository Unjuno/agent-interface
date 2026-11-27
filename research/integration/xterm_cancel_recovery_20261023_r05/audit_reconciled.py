"""Independent read-only audit; no runtime scorer import or live GUI action."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def input_request_count(root):
    return sum(json.loads(path.read_text()).get('operation') == 'guarded_input'
               for path in root.glob('*/request.json'))


def audit():
    report = json.loads((HERE/'result.json').read_text())
    conditions = json.loads((HERE/'conditions.json').read_text())
    sources = json.loads((HERE/'SOURCES.json').read_text())
    for name, expected in sources.items():
        data = (HERE.parents[2]/name).read_bytes().replace(b'\r\n',b'\n')
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'source changed after freeze: {name}')
    checks = []
    def check(name, ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:
            raise ValueError(name)

    old_rows = report['old_effect_rows_at_horizon'] or []
    fresh_rows = report['fresh_effect_rows_at_horizon'] or []
    old_terminal = report['old_terminal']
    old_cancel = old_terminal.get('cancellation') or report['cancel_response'].get('cancellation') or {}
    old_close = report.get('old_close') or report.get('old_final_close') or {}
    fresh_close = report.get('fresh_close') or report.get('fresh_final_close') or {}
    old_release = old_close.get('owner_release_attempt') or {}
    fresh_done = report.get('fresh_done_receipt') or {}
    old_binding = report['old_observation']['binding']
    fresh_binding = report['fresh_observation']['binding']
    old_effect_well_formed = (not old_rows or (
        len(old_rows) == 1
        and old_rows[0].get('argv') == [conditions['old_task_argument']]
        and old_rows[0].get('stdin_tty') is True
        and old_rows[0].get('stdout_tty') is True
        and report['old_app']['pid'] in (old_rows[0].get('ppid'),old_rows[0].get('parent_ppid'))))
    check('formal runner completed and Xvfb cleaned',
        report['status'] == 'OBSERVED_XTERM_CANCEL_AND_NEW_GENERATION_PENDING_AUDIT'
        and report.get('xvfb_exit_code') == 0 and not report.get('cleanup_errors'))
    preflight_bytes=(HERE/conditions['app_preflight_report']).read_bytes()
    preflight=json.loads(preflight_bytes)
    check('frozen real xterm and interactive PTY preflight passed with no input',
        hashlib.sha256(preflight_bytes).hexdigest()==conditions['app_preflight_sha256']
        and preflight.get('status')==conditions['app_preflight_status']
        and preflight.get('mapped_xterm_with_interactive_pty') is True
        and preflight.get('input_calls')==0 and preflight.get('task_effects')==0
        and preflight.get('journal_exists_after_cleanup') is False
        and preflight.get('xterm_exit_code')==15 and preflight.get('xvfb_exit_code')==0
        and not preflight.get('cleanup_errors'))
    check('actual xterm targets in private Xvfb',
        report['old_app']['wm_class'][1] == 'XTerm'
        and report['fresh_app']['wm_class'][1] == 'XTerm'
        and report['xvfb_vendor'] and report['xvfb_pid'] > 1)
    check('initial input had one pending public request',
        report['old_input_response'].get('status') == 'pending'
        and input_request_count(HERE/'attempt/old-owner') == 1)
    check('delay was flushed before real sync reply wait',
        report['fault_marker']['delay_ms'] == conditions['late_request_delay_ms']
        and report['owner_sync_entry']['call'] == 'python-xlib Display.sync'
        and report['fault_marker']['flushed_ns'] <= report['owner_sync_entry']['entered_ns']
        and report['cancel_invoked_ns'] >= report['owner_sync_entry']['entered_ns'])
    check('caller cancellation returned within frozen bound',
        0 <= report['cancel_elapsed_ms'] <= conditions['cancel_bound_ms'])
    check('old runtime outcome remains conservative UNKNOWN',
        old_terminal.get('status') != 'pending'
        and old_terminal.get('cleanup_status') == 'UNKNOWN'
        and old_terminal.get('release_confirmed') is False
        and old_terminal.get('task_success') is None
        and old_terminal.get('replay_allowed') is False)
    check('prestarted supervisor verified all-up while old result remains UNKNOWN',
        old_release.get('status')=='readback_verified'
        and old_release.get('release',{}).get('verified') is True
        and old_release.get('release',{}).get('keys_down')==[]
        and old_release.get('release',{}).get('buttons_down')==[]
        and old_terminal.get('cleanup_status')=='UNKNOWN'
        and old_terminal.get('release_confirmed') is False
        and old_terminal.get('late_server_request_possible') is True
        and old_terminal.get('replay_allowed') is False)
    check('old attempt not replayed and effect count preserved as observed',
        input_request_count(HERE/'attempt/old-owner') == 1
        and old_effect_well_formed
        and report['old_effect_rows_at_cancel'] is not None)
    check('finite delayed request horizon reached before changing focus',
        report['late_horizon_reached_ns'] >= report['fault_marker']['flushed_ns']
            + conditions['late_request_horizon_ms']*1_000_000
        and report['old_effect_rows_at_cancel'] in ([], old_rows)
        and set(bytes.fromhex(report['independent_keymap_at_horizon'])) == {0}
        and report['late_horizon_reached_ns'] <= report['fresh_xterm_started_ns']
        <= report['fresh_focus_started_ns'] <= report['fresh_input_started_ns'])
    check('old target/session retired before fresh application started',
        report['old_close'].get('status') in ('closed','cleanup_failed')
        and report['old_process_cleanup'].get('exit_code') in (15,-15)
        and not report['old_process_cleanup'].get('remaining_session_pids')
        and report['old_xterm_absent_before_new_generation'] is True
        and report['fresh_app']['pid'] != report['old_app']['pid'])
    check('standard caller observed distinct new generations',
        old_binding.get('process_generation') != fresh_binding.get('process_generation')
        and old_binding.get('window_generation') != fresh_binding.get('window_generation'))
    check('fresh task created one independently saved PTY effect',
        report['fresh_input_response'].get('status') == 'completed'
        and len(fresh_rows) == 1 and fresh_rows[0].get('argv') == [conditions['fresh_task_argument']]
        and fresh_rows[0].get('stdin_tty') is True
        and fresh_rows[0].get('stdout_tty') is True
        and report['fresh_app']['pid'] in (fresh_rows[0].get('ppid'),fresh_rows[0].get('parent_ppid'))
        and fresh_done.get('argv') == [conditions['fresh_task_argument']]
        and fresh_done.get('pid') == fresh_rows[0].get('pid'))
    check('effect timing and horizon readback follow input',
        report['fresh_input_started_ns'] <= fresh_rows[0]['started_ns']
        <= fresh_done['effect_committed_ns'] <= report['fresh_oracle_read_ns']
        and fresh_done['effect_committed_ns'] >= report['fresh_input_started_ns'])
    check('fresh close and xterm cleanup completed',
        fresh_close.get('status') == 'closed'
        and report['fresh_process_cleanup'].get('exit_code') in (15,-15)
        and not report['fresh_process_cleanup'].get('remaining_session_pids'))
    check('no model calls or input retries', report['model_calls'] == 0
        and input_request_count(HERE/'attempt/fresh-owner') == 1)
    return {'status':'PASS_XTERM_CANCEL_NEW_GENERATION_EFFECT_SCOPED','checks':checks,
        'old_effect_count':len(old_rows),'fresh_effect_count':len(fresh_rows),
        'cancel_elapsed_ms':report['cancel_elapsed_ms'],
        'fresh_input_to_fsync_ms':(fresh_done['effect_committed_ns']-report['fresh_input_started_ns'])/1e6,
        'fresh_input_to_public_return_ms':(report['fresh_input_returned_ns']-report['fresh_input_started_ns'])/1e6,
        'fresh_fsync_after_public_return_ms':(fresh_done['effect_committed_ns']-report['fresh_input_returned_ns'])/1e6,
        'native_surface_reused':old_binding.get('surface')==fresh_binding.get('surface'),
        'scope':'One injected XTEST delayed-request fault in a real xterm, one old attempt retained UNKNOWN, then a distinct xterm process/window and task. Repeat sample; custom saved-file oracle; no model/provider economics.'}


if __name__ == '__main__':
    result=audit()
    result['auditor_revision']='This independent repeat checks distinct process_generation and window_generation, whether or not Xvfb reuses the numeric surface XID. The retained xterm session exit code may be 15 after SIGTERM; exact PID/session absence remains required.'
    (HERE/'audit-reconciled.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
