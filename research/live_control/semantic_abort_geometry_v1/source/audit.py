"""Raw-only independent audit. Imports no actor, controller or policy code."""
import argparse
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path


def expected_specs():
    result = []
    for rep, order in enumerate((('RELEASE_ONLY', 'CACHED_OUTSIDE', 'FRESH_OUTSIDE'),
                                 ('CACHED_OUTSIDE', 'FRESH_OUTSIDE', 'RELEASE_ONLY'),
                                 ('FRESH_OUTSIDE', 'RELEASE_ONLY', 'CACHED_OUTSIDE'))):
        for scenario in ('STABLE', 'MOVE_BEFORE_REFRESH', 'MOVE_AFTER_REFRESH'):
            for policy in order:
                result.append(dict(case=len(result), rep=rep, scenario=scenario, policy=policy))
        result.append(dict(case=len(result), rep=rep, scenario='STABLE', policy='NO_INPUT'))
    return result


def read_files(path):
    if path.is_dir():
        return {p.relative_to(path).as_posix(): p.read_text() for p in path.rglob('*') if p.is_file()}
    encoded = path.read_bytes()
    if path.suffix == '.b64':
        encoded = base64.b64decode(encoded, validate=False)
    return json.loads(gzip.decompress(encoded))['files']


def audit(files, bindings, construction=False):
    errors, hypothesis, metrics = [], [], []
    def check(condition, message):
        if not condition:
            errors.append(message)
    specs = expected_specs()[:10] if construction else expected_specs()
    wanted = {'case-%02d/row.json' % s['case'] for s in specs}
    check({p for p in files if p.endswith('/row.json')} == wanted, 'case denominator')
    pids = set()
    for spec in specs:
        tag = 'case-%02d' % spec['case']
        def need(condition, message):
            check(condition, tag + ': ' + message)
        try:
            row = json.loads(files[tag + '/row.json'])
            journal = [json.loads(x) for x in files[tag + '/app.jsonl'].splitlines()]
            need(row['spec'] == spec and all(type(row['spec'][k]) is int for k in ('case', 'rep')),
                 'exact typed specification')
            need(row['errors'] == [], 'runner reported errors')
            need(row['bindings'] == bindings, 'unmodified class bindings')
            need(set(row['exits']) == {'fixture', 'observer', 'xvfb'}, 'exit coverage')
            need(all(type(v) is int and v == 0 for v in row['exits'].values()), 'process exits')
            case_pids = [row['actors']['fixture'], row['actors']['observer'], row['xvfb_pid']]
            need(all(type(v) is int and v > 0 for v in case_pids) and len(set(case_pids)) == 3,
                 'separate process identities')
            need(not pids.intersection(case_pids), 'fresh process per case')
            pids.update(case_pids)
            for suffix in ('app.stderr', 'observer.stderr', 'xvfb.stderr', 'xvfb.stdout'):
                need(files[tag + '/' + suffix] == '', 'empty stderr/stdout: ' + suffix)
            need(type(row['final_mask']) is int and row['final_mask'] & 0x1f00 == 0, 'final buttons neutral')
            need(len(row['final_keymap']) == 32 and all(type(x) is int and x == 0 for x in row['final_keymap']),
                 'final keys neutral')
            ready_events = [e for e in journal if e['kind'] == 'ready']
            need(len(ready_events) == 1 and journal[-1]['kind'] == 'exit', 'app lifetime')
            ready_event = ready_events[0]
            need(ready_event['bindings'] == bindings, 'receiver class bindings')
            prefix = journal[:journal.index(ready_event)]
            need(all(e['kind'] == 'native' and e['type'] in ('7', '8') for e in prefix), 'only observational crossing before ready')
            need(all(e['pid'] == case_pids[0] for e in journal), 'journal process identity')
            need(all(type(e['ns']) is int for e in journal) and
                 all(a['ns'] <= b['ns'] for a, b in zip(journal, journal[1:])), 'journal order')
            native = [e for e in journal if e['kind'] == 'native']
            presses = [e for e in native if e['type'] == '4']
            releases = [e for e in native if e['type'] == '5']
            callbacks = [e for e in journal if e['kind'] == 'command']
            effect = len(callbacks)
            used = spec['policy'] != 'NO_INPUT'
            need(len(presses) == int(used) and len(releases) == int(used), 'native event denominator')
            need(all(e['send_event'] is False for e in native), 'native XTEST, not SendEvent')
            need(all(type(e['count']) is int and e['count'] == i + 1 for i, e in enumerate(callbacks)),
                 'callback counter')
            if used:
                need(presses[0]['ns'] < releases[0]['ns'], 'press precedes release')
                need(all(presses[0]['ns'] < e['ns'] < releases[0]['ns'] for e in callbacks), 'callback ordering')
            inputs = [s['input'] for s in row['steps'] if 'input' in s]
            input_kinds = [x['kind'] for x in inputs]
            expected_inputs = ([] if not used else ['motion', 'press'] +
                               ([] if spec['policy'] == 'RELEASE_ONLY' else ['motion']) + ['release'])
            need(input_kinds == expected_inputs, 'exact submitted input')
            stages = [s for s in row['steps'] if 'label' in s]
            labels = [s['label'] for s in stages]
            expected_labels = ['initial', 'terminal']
            if used:
                expected_labels = ['initial', 'pressed']
                if spec['scenario'] == 'MOVE_BEFORE_REFRESH':
                    expected_labels += ['layout_change']
                expected_labels += ['refresh']
                if spec['scenario'] == 'MOVE_AFTER_REFRESH':
                    expected_labels += ['layout_change']
                expected_labels += ['before_release', 'terminal']
            need(labels == expected_labels, 'barrier schedule')
            states = {s['label']: s for s in stages}
            changed = False
            for stage in stages:
                label, app, ob = stage['label'], stage['app'], stage['observer']
                if label == 'layout_change':
                    changed = True
                geom = [360 if changed else 90, 110, 120, 60]
                need(ob['geometry'] == geom and app['geometry'] == geom, 'native geometry at ' + label)
                need(app['revision'] == int(changed) and type(app['revision']) is int, 'geometry revision')
                need(app['pid'] == case_pids[0] and ob['pid'] == case_pids[1], 'observation separation')
                need(app['button'] == ob['button'] and app['marker'] == ob['marker'], 'drawable binding')
                need(type(ob['mask']) is int and ob['mask'] & 0x1f00 ==
                     (0 if label in ('initial', 'terminal') else 0x100), 'button state at ' + label)
                need(len(ob['keymap']) == 32 and all(type(v) is int and v == 0 for v in ob['keymap']), 'key state')
                counters = app['counts']
                need(all(type(v) is int for v in counters.values()), 'typed counters')
                want_counts = {'press': int(used and label != 'initial'),
                               'release': int(used and label == 'terminal'),
                               'command': effect if label == 'terminal' else 0}
                need(counters == want_counts, 'app counts at ' + label)
                pixels = bytes.fromhex(ob['pixels_hex'])
                need(len(pixels) == 64 and ob['depth'] == 24 and ob['masks'] == [16711680, 65280, 255]
                     and ob['byte_order'] == 0, 'frozen X11 pixel representation')
                # Decode each of 16 pixels without relying on a runner color summary.
                rgb = [(int.from_bytes(pixels[i:i+4], 'little') >> 16 & 255,
                        int.from_bytes(pixels[i:i+4], 'little') >> 8 & 255,
                        int.from_bytes(pixels[i:i+4], 'little') & 255) for i in range(0, len(pixels), 4)]
                expected_rgb = (0, 255, 0) if label == 'terminal' and effect else (0, 0, 0)
                need(rgb == [expected_rgb] * 16, 'marker pixels corroborate callback at ' + label)
            if used:
                p = spec['policy']
                refreshed = states['refresh']['observer']['geometry']
                expected_point = None if p == 'RELEASE_ONLY' else [420, 140]
                if p == 'FRESH_OUTSIDE' and refreshed[0] == 360:
                    expected_point = [30, 40]
                need(row['decision']['point'] == expected_point, 'policy target from actual geometry')
                need(row['decision']['geometry_used'] == (refreshed if p == 'FRESH_OUTSIDE' else [90, 110, 120, 60]),
                     'geometry consumed by policy')
                need(inputs[0]['point'] == [150, 140], 'press location')
                if expected_point is not None:
                    need(inputs[2]['point'] == expected_point, 'cancel motion')
                pointer = expected_point or [150, 140]
                need(states['before_release']['observer']['pointer'] == pointer and
                     states['terminal']['observer']['pointer'] == pointer, 'actual release pointer')
                need([releases[0]['x'], releases[0]['y']] == pointer, 'native release coordinates')
            # Independently reconcile raw JSON-line IPC, not just the runner's summarized stages.
            decoded = [(e, json.loads(e['raw'])) for e in row['ipc']]
            all_responses = []
            for actor in case_pids[:2]:
                packets = [(e, r) for e, r in decoded if e['actor'] == actor]
                need(packets[0][0]['direction'] == 'response' and 'ready' in packets[0][1], 'actor ready')
                pending, last = None, 0
                for e, data in packets[1:]:
                    if e['direction'] == 'request':
                        need(pending is None and type(data['id']) is int and data['id'] == last + 1, 'IPC request order')
                        pending = data
                    else:
                        need(pending is not None and data['id'] == pending['id'], 'IPC response binding')
                        last = data['id']
                        pending = None
                        all_responses.append(data)
                need(pending is None, 'no dangling IPC')
            ready = next(r for e, r in decoded if e['actor'] == case_pids[0] and 'ready' in r)
            for st in stages:
                need(st['observer'] in all_responses, 'raw observer response retained')
                need(st['app'] == ready['ready'] or any(r.get('state') == st['app'] for r in all_responses),
                     'raw application response retained')
            app_requests = [r for e, r in decoded if e['actor'] == case_pids[0] and e['direction'] == 'request']
            need(app_requests == [e['request'] for e in journal if e['kind'] == 'request'], 'app received every request')
            for e in journal:
                if e['kind'] == 'barrier':
                    need(any(r.get('id') == e['id'] and r.get('state') == e['state'] for r in all_responses), 'app barrier receipt')
            expected_effect = int(spec['policy'] == 'RELEASE_ONLY' and spec['scenario'] == 'STABLE' or
                                  spec['policy'] == 'CACHED_OUTSIDE' and spec['scenario'] != 'STABLE' or
                                  spec['policy'] == 'FRESH_OUTSIDE' and spec['scenario'] == 'MOVE_AFTER_REFRESH')
            if effect != expected_effect:
                hypothesis.append(tag + ': expected %d callback, observed %d' % (expected_effect, effect))
            metrics.append({**spec, 'callbacks': effect, 'presses': len(presses), 'releases': len(releases)})
        except (KeyError, TypeError, ValueError, IndexError, StopIteration) as exc:
            errors.append(tag + ': malformed evidence: ' + repr(exc))
    return {'integrity': 'PASS' if not errors else 'FAIL', 'integrity_errors': errors,
            'hypothesis_errors': hypothesis, 'cases': metrics,
            'disposition': ('HOLD_EVIDENCE_INCOMPLETE' if errors else 'FAIL_BOUNDARY_HYPOTHESIS'
                            if hypothesis else 'PASS_ABORT_GEOMETRY_BOUNDARY_SCOPED')}


def corruption_checks(files, bindings, construction=False):
    checks = {}
    def trial(name, mutate):
        altered = copy.deepcopy(files)
        mutate(altered)
        checks[name] = bool(audit(altered, bindings, construction)['integrity_errors'])
    def row_change(files, case, change):
        key = 'case-%02d/row.json' % case
        row = json.loads(files[key])
        change(row)
        files[key] = json.dumps(row)
    trial('missing_case', lambda f: f.pop('case-00/row.json'))
    trial('duplicate_case', lambda f: f.update({'case-99/row.json': f['case-00/row.json']}))
    trial('boolean_counter', lambda f: row_change(f, 0, lambda r: r['steps'][-1]['app']['counts'].update(command=True)))
    trial('lost_exit', lambda f: row_change(f, 0, lambda r: r['exits'].pop('fixture')))
    trial('geometry_change', lambda f: row_change(f, 0, lambda r: r['steps'][-1]['observer']['geometry'].__setitem__(0, 91)))
    trial('false_pixel', lambda f: row_change(f, 0, lambda r: r['steps'][-1]['observer'].update(pixels_hex='00' * 64)))
    trial('missing_callback', lambda f: f.update({'case-00/app.jsonl': '\n'.join(
        x for x in f['case-00/app.jsonl'].splitlines() if json.loads(x)['kind'] != 'command') + '\n'}))
    trial('swapped_schedule', lambda f: row_change(f, 8, lambda r: r['steps'].reverse()))
    trial('held_button', lambda f: row_change(f, 0, lambda r: r.update(final_mask=256)))
    trial('wrong_actor', lambda f: row_change(f, 0, lambda r: r['actors'].update(observer=r['actors']['fixture'])))
    return checks


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--construction', action='store_true')
    args = p.parse_args()
    files = read_files(args.input)
    env = json.loads((args.source / 'ENVIRONMENT.json').read_text())
    result = audit(files, env['bindings'], args.construction)
    result['corruption_controls'] = corruption_checks(files, env['bindings'], args.construction)
    result['source_errors'] = []
    if not args.construction:
        freeze = json.loads((args.source / 'FREEZE.json').read_text())
        for name, expected in freeze['source_sha256'].items():
            if hashlib.sha256((args.source / name).read_bytes()).hexdigest() != expected:
                result['source_errors'].append(name)
        result['freeze_sha256'] = hashlib.sha256((args.source / 'FREEZE.json').read_bytes()).hexdigest()
    if not all(result['corruption_controls'].values()) or result['source_errors']:
        result['disposition'] = 'HOLD_AUDIT_OR_SOURCE_INTEGRITY'
    result['evidence_sha256'] = {p: hashlib.sha256(s.encode()).hexdigest() for p, s in sorted(files.items())}
    with args.out.open('x') as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('evidence_sha256', 'cases')}, sort_keys=True))
    return 0 if result['disposition'] == 'PASS_ABORT_GEOMETRY_BOUNDARY_SCOPED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
