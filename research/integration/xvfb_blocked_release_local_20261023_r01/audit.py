"""Offline reconstruction and event-multiplicity check; never replays the trial."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit():
    checks = []
    def check(name, ok):
        checks.append({'check': name, 'passed': bool(ok)})
        if not ok:
            raise ValueError(name)
    def load(name):
        return json.loads((HERE / name).read_text())
    def all_up(mapping):
        return bool(mapping) and all(value is False for value in mapping.values())
    r, launcher = load('result.json'), load('launcher-result.json')
    t, fresh = r['timing_ns'], r['fresh_session_recovery']
    check('host and inner exit zero', load('host-launch.json')['exit_code'] == 0
          and launcher['test_exit_code'] == 0)
    summary = load('unittest-summary.json')
    check('one actual test, no skips/errors/failures', summary == {'tests_run': 1,
          'skipped': 0, 'failures': 0, 'errors': 0, 'successful': True})
    check('frozen sources unchanged', launcher['postrun_sources_match'] is True)
    cancel_ms = (t['cancel_returned']-t['cancel_tool_invoked'])/1e6
    check('actual cancel response within 300ms', 0 <= cancel_ms <= 300
          and abs(cancel_ms-r['cancel_invocation_elapsed_ms']) < 1e-9)
    check('composite cancel interval within 3000ms',
          0 <= (t['cancel_returned']-t['cancel_started'])/1e6 < 3000)
    pause = r['xvfb_server_pause']
    resumed = pause['resume_receipt']['monotonic_ns']
    check('exact owned pidfd pause and successful resume',
          pause['signal_identity'] == 'retained_pidfd'
          and pause['pid'] == launcher['xvfb_pid'] and pause['requested_pause_ms'] == 1000
          and pause['resume_receipt']['error'] is None and resumed > pause['stopped_monotonic_ns'])
    cancel = r['cancel']
    check('exact owner retired before recorded supervisor release',
          cancel['owner_process_retired'] is True and cancel['owner_process_exitcode'] == -15
          and cancel['owner_client_disconnect']['owner_process_retired'] is True
          and cancel['owner_client_disconnect']['observed_monotonic_ns']
          <= cancel['owner_release_attempt']['release']['release_started_monotonic_ns'])
    release = r['independent_release_readback']
    check('independent all-up after resume', all_up(release['keys_down'])
          and release['observed_ns'] >= resumed)
    check('8.5 second horizon and independent all-up',
          r['late_request_horizon_readback']['observed_ns']-t['cancel_started'] >= 8_500_000_000
          and all_up(r['late_request_horizon_readback']['keys_down']))
    check('fresh target distinct from old target', fresh['new_target_xid']
          != r['observation']['pointer_binding']['surface'])
    check('fresh property transition and horizon value', fresh['effect_before_input'] == [0]
          and fresh['effect_after_input'] == [3] and fresh['effect_at_horizon'] == [3])
    events = r['synthetic_application_effect']['app_key_events']
    fresh_presses = [e for e in events if e['type'] == 2 and e['window'] == fresh['new_target_xid']]
    check('one fresh keypress in captured app trace', len(fresh_presses) == 1
          and fresh_presses[0]['monotonic_ns'] == fresh['keypress_event_observed_monotonic_ns']
          and fresh_presses[0]['effect_committed_ns'] == fresh['application_effect_committed_monotonic_ns'])
    start, event, commit, end = (fresh['input_started_monotonic_ns'],
        fresh['keypress_event_observed_monotonic_ns'], fresh['application_effect_committed_monotonic_ns'],
        fresh['effect_readback_completed_monotonic_ns'])
    check('fresh input/event/commit/readback ordering', start <= event <= commit
          <= fresh['effect_readback_started_monotonic_ns'] <= end)
    fresh_ms = (end-start)/1e6
    check('fresh interval recomputes from timestamps', abs(fresh_ms
          -fresh['effect_timing_ms']['input_invocation_to_effect_readback_completed']) < 1e-9)
    check('fresh task before old horizon', end < r['late_request_horizon_readback']['observed_ns'])
    for name, fence in [('cancel', cancel), ('terminal', r['terminal']),
                        ('after_fresh', fresh['old_cancellation_after_fresh_task'])]:
        check(name + ' UNKNOWN/no-replay/null-task preserved', fence['cleanup_status'] == 'UNKNOWN'
              and fence['release_confirmed'] is False and fence['replay_allowed'] is False
              and fence['task_success'] is None and fence['late_server_request_possible'] is True)
    check('neutral final cleanup', all_up(r['final_cleanup']['keys_down'])
          and not r.get('cleanup_errors'))
    cleanup = load('cleanup-recheck.json')
    check('owned server/test exited, no old-session members', launcher['cleanup'] == {'xvfb_exit_code': 0}
          and cleanup['xvfb_present'] is False and cleanup['test_present'] is False
          and cleanup['lock_present'] is False and cleanup['socket_present'] is False
          and cleanup['old_test_session_members'] == [])
    old_target = r['observation']['pointer_binding']['surface']
    old_presses = [e for e in events if e['type'] == 2 and e['window'] == old_target]
    return {'status': 'SCHEDULE_ENDPOINTS_PASS_ORACLE_EXACT_ONCE_FAIL', 'checks': checks,
        'recomputed_ms': {'cancel_invocation_to_return': cancel_ms,
            'resume_to_independent_all_up': (release['observed_ns']-resumed)/1e6,
            'fresh_input_to_independent_effect_readback': fresh_ms},
        'exact_once_counterexample': {
            'claimed_task_definition': r['independent_task_oracle']['task_definition'],
            'runtime_test_oracle_status': r['independent_task_oracle']['status'],
            'old_target_keypress_count': len(old_presses), 'old_target_keypress_events': old_presses,
            'old_property_remained': r['synthetic_application_effect']['property_value'],
            'exactly_one_old_keypress': len(old_presses) == 1,
            'interpretation': 'Idempotent property assignment masks repeated KeyPress/effect handlers. '
                'Trace alone does not prove the cause of repeats or a non-idempotent external task outcome.'}}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
