"""Raw-only independent UTF-16 byte oracle. Never imports runner/policy/runtime."""
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path


def require(condition, name):
    if not condition:
        raise ValueError(name)


def jint(value, minimum=0):
    return type(value) is int and value >= minimum


def same(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def native_replace(text, span):
    encoded = text.encode('utf-16-le')
    lo, hi = sorted(span)
    return (encoded[:2 * lo] + b'X\x00' + encoded[2 * hi:]).decode('utf-16-le')


def check(raw, blobs, cases):
    require(raw['schema'] == 'edit49-native-v1', 'schema')
    require(raw['backend_module'] == '/src/vendor/runtime/backends/x11_v1/backend.py', 'module origin')
    require(len(raw['rows']) == 4 * len(cases), 'complete rows')
    rows = []
    for index, row in enumerate(raw['rows']):
        case = cases[index // 4]
        widget = ['plain', 'rich'][(index // 2) % 2]
        arm = ['untyped', 'typed'][index % 2]
        ident = case['id'] + '-' + widget + '-' + arm
        require(row['cell_id'] == ident and row['display'] == ':' + str(121 + index), 'cell/display identity')
        require(same(row['cell'], dict(case, widget=widget, arm=arm, cell_id=ident)), 'case identity')
        ready = row['ready']
        require(ready['kind'] == 'ready' and ready['role'] == 'edit_fixture' and jint(ready['pid'], 1) and jint(ready['xid'], 1), 'ready identity')
        require(ready['text'] == case['current'] and ready['qt_document_count'] == len(case['current'].encode('utf-16-le')) // 2 + 1, 'observed source/unit')
        require(ready['qt'] == '5.15.13' and ready['pyqt'] == '5.15.10', 'Qt version')
        require(jint(row['app_exit']) and row['app_exit'] == 0 and jint(row['xvfb_exit']) and row['xvfb_exit'] == 0 and not row.get('forced_app_cleanup'), 'native exits')
        require(row['keymap_hex'] == '00' * 32, 'server keys empty')
        require(row['final_release']['verified'] is True and row['final_release']['keys_down'] == row['final_release']['buttons_down'] == [], 'release readback')
        require(set(row['artifacts']) == {'xvfb.stderr', 'app.stderr', 'saved.txt', 'state.json', 'events.jsonl', 'widget.png'}, 'artifact set')
        for name, digest in row['artifacts'].items():
            require(hashlib.sha256(blobs[ident + '/' + name]).hexdigest() == digest, 'artifact hash ' + name)
        png = blobs[ident + '/widget.png']
        require(png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', png[16:24]) == (520, 160), 'PNG dimensions')
        state = json.loads(blobs[ident + '/state.json'])
        require(same(state, row['saved_reply']), 'saved reply/state')
        require(blobs[ident + '/saved.txt'] == state['text'].encode('utf-8'), 'persisted UTF8')
        events = [json.loads(line) for line in blobs[ident + '/events.jsonl'].splitlines()]
        require(all(jint(e['ns'], 1) for e in events) and all(a['ns'] <= b['ns'] for a, b in zip(events, events[1:])), 'event order')
        require(events[-1]['kind'] == 'exit', 'fixture terminal')
        saved_events = [e for e in events if e['kind'] == 'saved']
        require(len(saved_events) == 1 and same(saved_events[0]['state'], state), 'journal saved join')
        refusal = arm == 'typed' and (case['context'] != case['current'] or case['unit'] == 'unknown')
        presses = [e for e in events if e['kind'] == 'key_press']
        releases = [e for e in events if e['kind'] == 'key_release']
        changes = [e for e in events if e['kind'] == 'text_changed']
        commands = [e['command']['op'] for e in events if e['kind'] == 'command']
        if refusal:
            expected = case['current']
            require(row['outcome'] == 'REFUSED_BEFORE_INPUT' and row['execution'] is None and 'program' not in row, 'refusal no program')
            require(row['refusal'] == ('STALE_SOURCE' if case['current'] != case['context'] else 'UNKNOWN_UNIT'), 'refusal reason')
            require(presses == releases == changes == [] and commands == ['save', 'quit'], 'refusal no native input')
            require(state['changes'] == [], 'refusal no change')
        else:
            require(row['outcome'] == 'INPUT_PROGRAM_RETURNED', 'input returned')
            if arm == 'untyped' or case['unit'] == 'utf16':
                span = case['span']
            else:
                span = [sum(2 if ord(c) > 0xffff else 1 for c in case['context'][:v]) for v in case['span']]
            require(same(row['lowered_span'], span), 'lowered range')
            selected = row['selection']
            require(selected['anchor'] == span[0] and type(selected['anchor']) is int and selected['position'] == span[1] and type(selected['position']) is int, 'actual range/direction')
            lo, hi = sorted(span)
            require(selected['selected'] == case['current'].encode('utf-16-le')[2 * lo:2 * hi].decode('utf-16-le'), 'actual selected text')
            expected = native_replace(case['current'], span)
            execution = row['execution']
            require(jint(execution['program_emissions']) and execution['program_emissions'] == 4 and jint(execution['emissions']) and execution['emissions'] == 4, 'emission counts')
            require(same(execution['completed_ops'], [0, 1, 2]) and row['admission']['accepted'] is True and row['admission']['code'] is None, 'contract/execution')
            require(row['program']['ops'] == [{'op':'focus','target':'fixture'}, {'op':'text','text':'X'}, {'op':'release_all'}], 'program intent')
            require(jint(execution['started_ns'], 1) and jint(execution['ended_ns'], 1) and execution['started_ns'] < execution['ended_ns'], 'execution order')
            require(len(execution['releases']) == 1 and execution['releases'][0]['verified'] is True and execution['releases'][0]['keys_down'] == execution['releases'][0]['buttons_down'] == [], 'program release')
            require(type(row['focus_xid']) is int and row['focus_xid'] == ready['xid'], 'focus target')
            require([e['key'] for e in presses] == [16777248, 88] and [e['key'] for e in releases] == [88, 16777248], 'native chord events')
            require(all(e['auto'] is False for e in presses + releases) and len(changes) == 1 and changes[0]['text'] == expected, 'native change')
            require(commands == ['select', 'save', 'quit'] and state['changes'] == [expected], 'one edit/no replay')
        require(state['text'] == expected, 'application effect oracle')
        if case['unit'] == 'utf16':
            intended = native_replace(case['context'], case['span'])
        else:
            lo, hi = sorted(case['span'])
            intended = case['context'][:lo] + 'X' + case['context'][hi:]
        if arm == 'typed' and not refusal:
            require(state['text'] == intended, 'typed intended effect')
        rows.append(dict(cell_id=ident, arm=arm, refused=refusal, text=state['text'],
                         exact_intended=state['text'] == intended, original=case['current']))
    typed = [r for r in rows if r['arm'] == 'typed']
    baseline = [r for r in rows if r['arm'] == 'untyped']
    return dict(rows=rows, typed_exact_edits=sum(r['exact_intended'] and not r['refused'] for r in typed),
                typed_no_input_refusals=sum(r['refused'] for r in typed), baseline_wrong_saved=sum(not r['exact_intended'] for r in baseline))


def mutations(raw, blobs):
    def simple(name, index, key, value):
        r = copy.deepcopy(raw); r['rows'][index][key] = value
        return name, r, dict(blobs)
    yield simple('wrong_display', 0, 'display', ':999')
    r = copy.deepcopy(raw); r['rows'][0]['ready']['pid'] = float(r['rows'][0]['ready']['pid'])
    yield 'float_pid', r, dict(blobs)
    r = copy.deepcopy(raw); r['rows'][0]['ready']['role'] = 'consumer'
    yield 'wrong_role', r, dict(blobs)
    r = copy.deepcopy(raw); r['rows'][0]['execution']['program_emissions'] = 4.0
    yield 'float_emissions', r, dict(blobs)
    yield simple('keys_not_empty', 0, 'keymap_hex', '01' + '00' * 31)
    r = copy.deepcopy(raw); r['rows'][0]['app_exit'] = False
    yield 'boolean_exit', r, dict(blobs)
    r = copy.deepcopy(raw); r['rows'][0]['selection']['anchor'] += 1
    yield 'wrong_anchor', r, dict(blobs)
    yield simple('wrong_focus', 0, 'focus_xid', 1)
    r = copy.deepcopy(raw); r['rows'][0]['admission']['accepted'] = False
    yield 'contract_refused', r, dict(blobs)
    r = copy.deepcopy(raw); r['rows'].pop()
    yield 'missing_row', r, dict(blobs)
    r = copy.deepcopy(raw); r['rows'][1]['lowered_span'] = [3.0, 5]
    yield 'float_range', r, dict(blobs)
    for index in [0, 1]:
        r, b = copy.deepcopy(raw), dict(blobs)
        row = r['rows'][index]; ident = row['cell_id']; text = 'WRONG'
        state = json.loads(b[ident + '/state.json']); state['text'] = text; state['changes'] = [text]
        row['saved_reply'] = copy.deepcopy(state)
        events = [json.loads(line) for line in b[ident + '/events.jsonl'].splitlines()]
        for e in events:
            if e['kind'] == 'saved': e['state'] = copy.deepcopy(state)
            if e['kind'] == 'text_changed': e['text'] = text
        updated = {'saved.txt': text.encode(), 'state.json': (json.dumps(state) + '\n').encode(),
                   'events.jsonl': ''.join(json.dumps(e) + '\n' for e in events).encode()}
        for name, data in updated.items():
            b[ident + '/' + name] = data; row['artifacts'][name] = hashlib.sha256(data).hexdigest()
        yield 'rejoined_wrong_effect_' + str(index), r, b


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cases', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raw_bytes = (a.evidence / 'raw.json').read_bytes()
    raw = json.loads(raw_bytes); cases_bytes = a.cases.read_bytes(); cases = json.loads(cases_bytes)
    require(raw['cases_sha256'] == hashlib.sha256(cases_bytes).hexdigest(), 'case bytes')
    blobs = {str(f.relative_to(a.evidence)): f.read_bytes() for f in a.evidence.rglob('*') if f.is_file() and f.name != 'raw.json'}
    result = check(raw, blobs, cases)
    require(result['typed_exact_edits'] == 12 and result['typed_no_input_refusals'] == 4 and result['baseline_wrong_saved'] == 8, 'frozen decision gate')
    controls = []
    for name, r, b in mutations(raw, blobs):
        try: check(r, b, cases)
        except ValueError as e: controls.append(dict(name=name, rejected=True, reason=str(e)))
        else: controls.append(dict(name=name, rejected=False))
    require(len(controls) == 13 and all(c['rejected'] for c in controls), 'semantic negative controls')
    result.update(status='PASS_EDIT_OFFSET_BOUNDARY_SCOPED', controls=controls,
                  raw_sha256=hashlib.sha256(raw_bytes).hexdigest(), cases_sha256=hashlib.sha256(cases_bytes).hexdigest())
    with a.output.open('x') as f: f.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'typed_exact_edits', 'typed_no_input_refusals', 'baseline_wrong_saved']}))


if __name__ == '__main__':
    main()
