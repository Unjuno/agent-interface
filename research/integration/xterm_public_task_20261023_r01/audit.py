"""Independent saved-file oracle; no runtime scorer imports or live actions."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit():
    r = json.loads((HERE/'result.json').read_text())
    rows = [json.loads(line) for line in (HERE/'journal.jsonl').read_text().splitlines()]
    done = json.loads((HERE/'journal.done.json').read_text())
    cleanup = json.loads((HERE/'cleanup-recheck.json').read_text())
    checks = []
    def check(name, ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:
            raise ValueError(name)
    check('actual run success', json.loads((HERE/'host-launch.json').read_text())['exit_code'] == 0
          and r['status'] == 'PASS_XTERM_TASK_SCOPED')
    check('one non-idempotent saved record', len(rows) == 1 and rows[0]['argv'] == ['a1'])
    check('command ran inside terminal PTY', rows[0]['stdin_tty'] is True and rows[0]['stdout_tty'] is True
          and rows[0]['term'] == 'xterm' and rows[0]['display'] == ':188')
    check('command ancestry belongs to owned xterm',
          r['xterm_pid'] in (rows[0]['ppid'], rows[0]['parent_ppid']))
    check('fsync completion agrees with record', done['pid'] == rows[0]['pid']
          and done['argv'] == ['a1'] and rows[0]['started_ns'] <= done['effect_committed_ns'])
    check('input precedes command, oracle follows fsync', r['input_started_ns'] <= rows[0]['started_ns']
          and done['effect_committed_ns'] <= r['oracle_read_completed_ns'])
    check('complete public input and close', r['input_result']['status'] == 'completed'
          and r['close']['status'] == 'closed')
    check('independent final neutral keymap', set(bytes.fromhex(r['final_keymap_hex'])) == {0})
    check('initial neutral keymap', set(bytes.fromhex(r['initial_keymap_hex'])) == {0})
    check('real app fixture target and generation evidence', r['window']['wm_class'][1] == 'XTerm'
          and len(r['source_binding']['process_generation']) == 64)
    check('no replayed input request', sum(json.loads(p.read_text())['operation'] == 'guarded_input'
          for p in (HERE/'mcp').glob('*/request.json')) == 1)
    check('owned app/server cleanup', r['xvfb_cleanup_exit_code'] == 0
          and isinstance(r['xterm_cleanup_exit_code'], int) and 'xterm_cleanup_error' not in r)
    check('independent owned absence', cleanup['remaining_owned_pids'] == []
          and not cleanup['lock_present'] and not cleanup['socket_present'])
    check('zero model calls', r['model_calls'] == 0)
    return {'status':'PASS_SAVED_XTERM_EFFECT_SCOPED','checks':checks,
        'input_to_fsync_ms':(done['effect_committed_ns']-r['input_started_ns'])/1e6,
        'input_to_oracle_read_ms':(r['oracle_read_completed_ns']-r['input_started_ns'])/1e6,
        'scope':'Known typed shell command through real xterm; custom append helper, one task, no fault or model.'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
