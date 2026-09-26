"""Independent raw-only evidence checker. Never imports the runner or X11 modules."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def zero(value):
    return type(value) is int and value == 0


def neutral(state, locked):
    require(type(state['locked']) is int and state['locked'] == locked * 2, 'locked state')
    require(state['keymap'] == '00' * 32, 'physical keys')
    require(zero(state['base']) and zero(state['latched']) and zero(state['group']), 'other modifiers/group')
    require(type(state['mask']) is int and state['mask'] == locked * 2, 'pointer modifier state')


def check_case(r):
    before, after = r['before'], r['after']
    require(type(before) is int and before in (0, 1) and type(after) is int and after in (0, 1), 'state type')
    policy = r['policy']
    require(policy in ('EXACT_BACKEND', 'PREFLIGHT_LOCK_GUARD', 'DISPATCH_LOCK_GUARD'), 'policy')
    expected = policy == 'EXACT_BACKEND' or (before == 0 if policy == 'PREFLIGHT_LOCK_GUARD' else after == 0)
    require(type(r['allowed']) is bool and r['allowed'] == expected, 'decision')
    require(r['public_admission'] is False and 'error' not in r, 'scope/error')
    neutral(r['configured_pre'], before)
    neutral(r['pre'], before)
    neutral(r['configured_dispatch'], after)
    neutral(r['post'], after)
    require(r['preflight_mask'] == before * 2 and r['dispatch_mask'] == after * 2, 'mask snapshots')
    require(r['preflight_clear'] is (before == 0), 'precheck')
    require(r['preflight_plan'] == [[r['payload'][0]], ['SHIFT', r['payload'][1].lower()], [r['payload'][2]]], 'plan')
    require(zero(r['unsupported']['emissions']) and 'U+20AC' in r['unsupported']['error'], 'unsupported')
    require(zero(r['app_exit']) and r['app_stdout_tail'] == '' and r['app_stderr'] == '', 'app process')
    require(type(r['app_pid']) is int and r['app_pid'] > 0, 'app identity')
    require(r['start_ns'] <= r['decision_ns'] <= r['post']['ns'] <= r['effect']['ns'] <= r['end_ns'], 'decision/effect clock order')
    require(r['configured_dispatch']['ns'] <= r['decision_ns'], 'lock precedes decision')
    native = r['native']
    require(len(native) == 4, 'native denominator')
    states = ['configured_pre', 'pre', 'configured_dispatch', 'post']
    for rec, name in zip(native, states):
        require(zero(rec['exit']) and rec['stderr'] == '', 'native process')
        require(json.loads(rec['stdout']) == r[name], 'native raw binding')
        require(rec['start_ns'] <= r[name]['ns'] <= rec['end_ns'], 'native clock enclosure')
    wire = r['app_wire']
    require(len(wire) == 4, 'app wire denominator')
    require(wire[0]['request'] is None and [json.loads(w['request']) for w in wire[1:]] == [{'op':'snapshot'}, {'op':'snapshot'}, {'op':'finish'}], 'read-only app requests')
    for rec, name, tag in zip(wire, ['ready', 'before_effect', 'effect', 'terminal'], ['ready', 'snapshot', 'snapshot', 'finish']):
        obj = json.loads(rec['response'])
        require(obj == r[name] and obj['tag'] == tag, 'app raw binding')
        require(obj['pid'] == r['app_pid'] and obj['entry'] == r['ready']['entry'], 'app identity binding')
        require(obj['ns'] <= rec['received_ns'], 'app clock enclosure')
    require(r['before_effect']['value'] == '' and r['before_effect']['events'] == [] and r['before_effect']['changes'] == [], 'no early text')
    require(r['pre']['focus'] == r['ready']['entry'] == r['post']['focus'], 'focus')
    effect = r['effect']
    require(effect['value'] == r['terminal']['value'] and effect['events'] == r['terminal']['events'], 'terminal effect')
    require(r['finally_release']['verified'] is True and r['finally_release']['keys_down'] == [] and r['finally_release']['buttons_down'] == [], 'final release')
    if not expected:
        require(effect['value'] == '' and effect['events'] == [] and effect['changes'] == [], 'refusal emitted')
        require(zero(r['backend_emissions']) and r['execution'] is None, 'refusal emissions')
        require(r['release']['verified'] is True and r['disposition'] == 'REFUSE_LOCKED_MODIFIER', 'refusal release')
        return 'REFUSED'
    require(type(r['backend_emissions']) is int and r['backend_emissions'] == 8, 'emission count')
    ex = r['execution']
    require(ex['completed_ops'] == [0, 1, 2] and ex['program_emissions'] == 8 and ex['emissions'] == 8, 'execution prefix')
    require(len(ex['releases']) == 1 and ex['releases'][0]['verified'] is True, 'release')
    require(ex['releases'][0]['keys_down'] == [] and ex['releases'][0]['buttons_down'] == [], 'owned neutrality')
    events = effect['events']
    require(len(events) == 8 and [x['kind'] for x in events] == ['2', '3', '2', '2', '3', '3', '2', '3'], 'event sequence')
    held = set()
    for ev in events:
        require(type(ev['state']) is int and (ev['state'] & 2) == after * 2, 'event lock state')
        if ev['kind'] == '2':
            require(ev['keycode'] not in held, 'duplicate press')
            held.add(ev['keycode'])
        else:
            require(ev['keycode'] in held, 'unpaired release')
            held.remove(ev['keycode'])
    require(not held, 'unreleased event')
    if r['payload'] == 'aB2':
        a, b, digit, shift = r['post']['codes']
        require([ev['keycode'] for ev in events] == [a, a, shift, b, b, shift, digit, digit], 'keycode plan')
    typed = ''.join(ev['char'] for ev in events if ev['kind'] == '2')
    require(typed == effect['value'], 'event/application effect')
    require(effect['changes'][-1]['value'] == effect['value'] and len(effect['changes']) == 3, 'value journal')
    require(all(a['ns'] <= b['ns'] for a, b in zip(events, events[1:])), 'event ordering')
    if after == 0:
        require(typed == r['payload'], 'unlocked text')
        return 'EXACT'
    require(typed != r['payload'] and typed.lower() == r['payload'].lower() and len(typed) == 3, 'locked counterexample')
    return 'WRONG_CASE'


def check_batch(raw):
    require(raw['completed'] is True and 'error' not in raw, 'batch incomplete')
    cleanup = raw['server_cleanup']
    require(zero(cleanup['exit']) and cleanup['socket_absent'] is True, 'server cleanup')
    require(cleanup['pid'] == raw['server_pid'], 'server identity')
    require(raw['source_backend'] == '3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8', 'backend source')
    require('-nolisten' in raw['server_argv'] and 'tcp' in raw['server_argv'] and '-auth' in raw['server_argv'], 'private display')
    require('layout:' in raw['setup'][1]['stdout'] and 'us' in raw['setup'][1]['stdout'], 'US layout')
    for rec in raw['setup'] + raw['lock_controls']:
        require(zero(rec['exit']), 'setup exit')
    neutral(json.loads(raw['lock_controls'][0]['stdout']), 1)
    neutral(json.loads(raw['lock_controls'][1]['stdout']), 0)
    return [check_case(r) for r in raw['rows']]


def mutation_controls(row):
    cases = []
    for name in ('effect', 'event', 'decision', 'physical', 'process_type', 'native_type', 'focus', 'release', 'lock', 'raw'):
        m = copy.deepcopy(row)
        if name == 'effect': m['effect']['value'] = 'wrong'
        if name == 'event': m['effect']['events'][0]['char'] = 'z'
        if name == 'decision': m['allowed'] = not m['allowed']
        if name == 'physical': m['pre']['keymap'] = 'ff' * 32
        if name == 'process_type': m['app_exit'] = False
        if name == 'native_type': m['native'][0]['exit'] = False
        if name == 'focus': m['post']['focus'] += 1
        if name == 'release': m['finally_release']['verified'] = False
        if name == 'lock': m['post']['locked'] = 2
        if name == 'raw': m['app_wire'][2]['response'] = '{}\n'
        try:
            check_case(m)
        except (ValueError, KeyError, TypeError, IndexError):
            cases.append({'name': name, 'rejected': True})
        else:
            raise ValueError('accepted mutation ' + name)
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path', type=Path)
    ap.add_argument('--construction', action='store_true')
    args = ap.parse_args()
    if args.construction:
        raw = json.loads((args.path / 'raw.json').read_text())
        outcomes = check_batch(raw)
        result = {'decision': 'PASS_CONSTRUCTION', 'outcomes': outcomes,
                  'controls': mutation_controls(raw['rows'][0])}
    else:
        root = args.path.parent
        freeze = json.loads((root / 'FREEZE.json').read_text())
        for name, expected in freeze['sources'].items():
            require(hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, 'frozen source '+name)
        summary = {p: {'EXACT': 0, 'WRONG_CASE': 0, 'REFUSED': 0} for p in ('EXACT_BACKEND','PREFLIGHT_LOCK_GUARD','DISPATCH_LOCK_GUARD')}
        all_rows = []
        for i, schedule in enumerate(((0,0),(1,1),(0,1),(1,0))):
            receipt = json.loads((args.path / f'batch-{i}.exit.json').read_text())
            require(zero(receipt['returncode']) and receipt['timed_out'] is False, 'supervisor exit')
            rawbytes = (args.path / f'batch-{i}' / 'raw.json').read_bytes()
            require(receipt['raw_sha256'] == hashlib.sha256(rawbytes).hexdigest(), 'supervisor raw hash')
            raw = json.loads(rawbytes)
            require(type(raw['batch']) is int and raw['batch'] == i and raw['construction'] is False and len(raw['rows']) == 6, 'batch schedule')
            require(raw['pid'] == receipt['pid'] and receipt['started_ns'] <= raw['started_ns'] <= raw['finished_ns'] <= receipt['ended_ns'], 'runner exit identity/enclosure')
            outcomes = check_batch(raw)
            keys = set()
            for r, verdict in zip(raw['rows'], outcomes):
                require((r['before'],r['after']) == schedule and r['payload'] == 'aB2', 'row schedule')
                key = (r['policy'],r['repetition'])
                require(key not in keys and type(r['repetition']) is int and r['repetition'] in (0,1), 'row uniqueness')
                keys.add(key)
                summary[r['policy']][verdict] += 1
            all_rows.extend(raw['rows'])
        require(summary == {'EXACT_BACKEND': {'EXACT':4,'WRONG_CASE':4,'REFUSED':0},
                            'PREFLIGHT_LOCK_GUARD': {'EXACT':2,'WRONG_CASE':2,'REFUSED':4},
                            'DISPATCH_LOCK_GUARD': {'EXACT':4,'WRONG_CASE':0,'REFUSED':4}}, 'scientific gates')
        result = {'decision':'PASS_TEXT_LOCK_BOUNDARY_SCOPED', 'rows':24, 'summary':summary,
                  'controls':mutation_controls(all_rows[0]), 'errors':[]}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, IndexError, OSError) as error:
        print(json.dumps({'decision':'HOLD_OR_FAIL_AUDIT', 'error':repr(error)}))
        raise SystemExit(2)
