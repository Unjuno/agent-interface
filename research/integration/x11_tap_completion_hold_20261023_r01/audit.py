"""Read-only, standard-library comparison audit; no runtime import or live action."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit():
    conditions = json.loads((HERE/'conditions.json').read_text())
    checks, measurements = [], []
    def check(name, ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:
            raise ValueError(name)
    controls = []
    cleanup = json.loads((HERE/'cleanup-recheck.json').read_text())
    check('independent owned cleanup', cleanup['remaining_owned_pids'] == []
          and not cleanup['lock_present'] and not cleanup['socket_present'])
    check('actual host exit', json.loads((HERE/'host-launch.json').read_text())['exit_code'] == 0)
    for index, arm in enumerate(conditions['order']):
        r = json.loads((HERE/(str(index)+'-'+arm)/'result.json').read_text())
        prefix = str(index)+'-'+arm+': '
        check(prefix+'actual arm and cleanup', r['status'] == 'OBSERVED' and r['arm'] == arm
              and r['xvfb_exit_code'] == 0 and r['application_thread_stopped'] is True
              and 'input_cleanup_error' not in r and 'close_cleanup_error' not in r)
        controls.append(r['keyboard_controls'])
        h, start, end, final = r['hold'], r['held_start'], r['held_end'], r['final']
        check(prefix+'one declared completion hold', 'gate_timeout' not in h
              and h['real_sync_returned_ns'] <= start['started_ns'] <= start['completed_ns']
              <= end['started_ns'] <= end['completed_ns'] <= r['gate_released_ns']
              <= h['completion_returned_ns'] <= r['input_returned_ns'])
        check(prefix+'at least one second sampled interval', end['started_ns']-start['completed_ns'] >= 1_000_000_000)
        request_types = [x['type'] for x in h['requests_at_entry'] if x['detail'] == r['keycode']]
        check(prefix+'literal request prefix', request_types == ([2] if arm == 'baseline' else [2,3]))
        check(prefix+'conservative obligation while completion withheld',
              h['obligations_at_entry'] == {'a':r['keycode']})
        check(prefix+'initial neutral/zero', r['initial']['count'] == [0]
              and not r['initial']['key_down'] and set(bytes.fromhex(r['initial']['keymap_hex'])) == {0})
        check(prefix+'key-state discriminator', start['key_down'] is (arm == 'baseline')
              and end['key_down'] is (arm == 'baseline'))
        check(prefix+'candidate one effect / baseline observed count',
              start['count'][0] >= 1 and end['count'][0] >= start['count'][0]
              and (arm == 'baseline' or start['count'] == end['count'] == [1]))
        presses = [e for e in r['application_events'] if e['type'] == 2]
        check(prefix+'independent final count matches handler trace', final['count'] == [len(presses)]
              and all(e['detail'] == r['keycode'] for e in presses))
        check(prefix+'final neutral with no held keys', not final['key_down']
              and set(bytes.fromhex(final['keymap_hex'])) == {0})
        check(prefix+'public input and close completed', r['input_result']['status'] == 'completed'
              and r['close']['status'] == 'closed')
        measurements.append({'index':index,'arm':arm,'held_start_count':start['count'][0],
            'held_end_count':end['count'][0],'final_count':final['count'][0],
            'hold_ms':(h['completion_returned_ns']-h['real_sync_returned_ns'])/1e6,
            'call_ms':(r['input_returned_ns']-r['input_invoked_ns'])/1e6,
            'baseline_repeat_observed':arm == 'baseline' and end['count'][0] > 1})
    check('same keyboard repeat controls', all(c == controls[0] for c in controls))
    return {'status':'PASS_COMPLETION_HOLD_DISCRIMINATOR_SCOPED',
        'checks':checks,'measurements':measurements,
        'scope':'Two matched samples per method, ABBA, injected completion hold after actual sync; '
            'not network reply loss, blocked send, production reliability or general task economics.'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
