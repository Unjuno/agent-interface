"""Saved raw only; no Xlib or candidate policy import, no native rerun."""
import copy, hashlib, json, sys
from pathlib import Path

MODES = {'healthy_fast', 'healthy_server_blocked', 'killed_server_blocked', 'invalid_response'}
def check(rows):
    assert len(rows) == 12
    assert {(r['mode'], r['repeat']) for r in rows} == {(m, i) for m in MODES for i in range(3)}
    clock_hold = False
    for r in rows:
        assert 'error' not in r
        assert r['authority'] is False and type(r['input_emissions']) is int and r['input_emissions'] == 0
        ready = r['ready']
        assert ready['kind'] == 'READY' and type(ready['pid']) is int and ready['pid'] == r['parent_observed_pid']
        assert type(ready['start_ticks']) is int and ready['start_ticks'] == r['parent_start_ticks']
        assert isinstance(ready['nonce'], str) and len(ready['nonce']) == 36
        starts = [m for m in r['messages'] if m['kind'] == 'QUERY_STARTED']
        replies = [m for m in r['messages'] if m['kind'] == 'RESULT']
        assert len(starts) == 1 and all(type(starts[0][k]) is type(ready[k]) and starts[0][k] == ready[k] for k in ('pid', 'start_ticks', 'nonce'))
        assert r['go_ns'] <= starts[0]['query_started_ns'] <= r['query_start_received_ns']
        assert r['query_start_received_ns'] < r['go_ns'] + 30000000, 'query did not enroll before fixed budget'
        assert r['budget_observed_ns'] >= r['go_ns'] + 30000000
        assert r['fixture_focus'] == r['expected_focus'] == r['oracle_focus_after']
        killed = r['mode'] == 'killed_server_blocked'
        blocked = r['mode'].endswith('server_blocked')
        expected_exit = -9 if killed else 0
        assert type(r['worker_exit']) is int and r['worker_exit'] == expected_exit
        assert r['cleanup']['worker_exit'] == expected_exit and r['cleanup']['server_exit'] == 0
        assert r['cleanup']['keymap_empty'] is True and r['cleanup']['observed_buttons_1_to_3_neutral'] is True and r['cleanup']['controller_closed'] is True
        if blocked:
            assert r['grab_confirmed_ns'] <= r['go_ns'] < r['budget_observed_ns'] <= r['ungrab_ns']
            assert r['ungrab_ns'] >= r['go_ns'] + 100000000
            assert r['result_available_at_budget'] is False
        if killed:
            assert len(replies) == 0 and r['response_valid'] is None
            assert r['terminal_at_budget'] == -9
            assert r['go_ns'] + 10000000 <= r['kill_ns'] < r['go_ns'] + 30000000
            assert r['at_budget'] == r['final'] == 'FAILED'
        else:
            assert len(replies) == 1
            reply = replies[0]
            assert all(type(reply[k]) is type(ready[k]) and reply[k] == ready[k] for k in ('pid', 'start_ticks', 'nonce'))
            assert type(reply['native_focus']) is int and reply['native_focus'] == r['expected_focus']
            assert starts[0]['query_started_ns'] <= reply['query_finished_ns'] <= r['response_received_ns'] <= r['waitpid_observed_ns']
            invalid = r['mode'] == 'invalid_response'
            assert type(reply['focus']) is int and reply['focus'] == r['expected_focus'] + int(invalid)
            assert r['response_valid'] is (not invalid)
            assert r['final'] == ('EVIDENCE_INVALID' if invalid else 'RESPONSIVE_SCOPED')
            if blocked:
                assert r['terminal_at_budget'] is None and r['at_budget'] == 'SUSPECTED_UNAVAILABLE'
                assert reply['query_finished_ns'] >= r['ungrab_ns']
                assert r['baseline_at_budget'] == 'FAILED'
            elif not r['result_available_at_budget']:
                clock_hold = True
                assert r['at_budget'] == 'SUSPECTED_UNAVAILABLE'
            else:
                assert r['at_budget'] == ('EVIDENCE_INVALID' if invalid else 'RESPONSIVE_SCOPED')
                if reply['query_finished_ns'] > r['go_ns'] + 30000000:
                    clock_hold = True
    return 'HOLD_CLOCK_BOUNDARY' if clock_hold else 'SUPPORTED_NATIVE_LIVENESS_BOUNDARY_SCOPED'

def negatives(rows):
    mutations = [lambda x: x[0].update(authority=True), lambda x: x[0].update(input_emissions=True), lambda x: x[0]['ready'].update(pid=True), lambda x: x[0]['messages'][0].update(nonce='stale'), lambda x: x[0]['cleanup'].update(keymap_empty=False), lambda x: x[0].update(final='FAILED'), lambda x: x[1].update(terminal_at_budget=-9), lambda x: x[2].update(worker_exit=0)]
    results = []
    for i, mutate in enumerate(mutations):
        other = copy.deepcopy(rows); mutate(other)
        assert json.dumps(other, sort_keys=True) != json.dumps(rows, sort_keys=True), 'ineffective control'
        rejected = False
        try: check(other)
        except (AssertionError, KeyError, TypeError): rejected = True
        results.append({'control': i, 'rejected': rejected})
    assert all(x['rejected'] for x in results)
    return results

def main():
    source, target = map(Path, sys.argv[1:3])
    result = {'raw_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    try:
        rows = [json.loads(line) for line in source.read_text().splitlines()]
        result.update(status=check(rows), rows=len(rows), controls=negatives(rows), delayed_healthy=3, timeout_baseline_false_crash=3, typed_false_crash=0)
    except Exception as exc:
        result.update(status='STOP_INVALID_NATIVE_EVIDENCE', error=repr(exc))
    with target.open('x') as f: json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result))
    return 1 if result['status'].startswith('STOP') else 0

if __name__ == '__main__': sys.exit(main())
