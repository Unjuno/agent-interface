"""Independent raw-file audit: does not import the controller or application."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(root, construction=False, check_hashes=True):
    errors, failures, counts = [], [], {}

    def require(ok, label):
        if not ok:
            errors.append(label)

    def gate(ok, label):
        if not ok:
            failures.append(label)

    recipes = ['COMPLETE', 'RELEASE_ONLY_CANCEL', 'MOVE_AWAY_CANCEL',
               'CAPABILITY_GATED_CANCEL', 'STALE_CAPABILITY_CANCEL']
    schedule = ([(0, k, s) for k in ['button', 'scale'] for s in [recipes[0], recipes[2]]]
                if construction else [(r, k, s) for r in range(3)
                                      for k in ['button', 'scale'] for s in recipes])
    mode = 'construction' if construction else 'formal'
    expected = [f'{mode}-{i:02d}-{k}-{s.lower()}' for i, (_, k, s) in enumerate(schedule)]
    try:
        manifest = json.loads((root / 'MANIFEST.json').read_text())
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
        require(actual == set(manifest) | {'MANIFEST.json'}, 'file denominator')
        if check_hashes:
            for name, sha in manifest.items():
                require(hashlib.sha256((root / name).read_bytes()).hexdigest() == sha,
                        'hash:' + name)
        run = json.loads((root / 'run.json').read_text())
        require(run['rows'] == expected and run['mode'] == mode, 'schedule')
        require(run['errors'] == [] and run['xvfb_reaped'] is True
                and type(run['xvfb_returncode']) is int and run['xvfb_returncode'] == 0,
                'Xvfb outcome')
        for cid, (rep, kind, recipe) in zip(expected, schedule):
            d = root / cid
            row = json.loads((d / 'row.json').read_text())
            events = [json.loads(x) for x in (d / 'app_events.jsonl').read_text().splitlines()]
            effects = [json.loads(x) for x in (d / 'effects.jsonl').read_text().splitlines()]
            require(row['case_id'] == cid and row['kind'] == kind
                    and row['recipe'] == recipe and type(row['rep']) is int and row['rep'] == rep,
                    cid + ':row identity')
            require(row['errors'] == [] and type(row['app_returncode']) is int
                    and row['app_returncode'] == 0 and (d / 'app_stderr.txt').read_bytes() == b'',
                    cid + ':process')
            ready = row['ready']
            pid = ready['pid']
            require(type(pid) is int and pid > 0 and ready['session'] == cid
                    and ready['kind'] == kind, cid + ':application identity')
            receives, sends = [], []
            for item in row['ipc']:
                require(item['raw'].endswith('\n') and type(item['mono_ns']) is int,
                        cid + ':IPC framing')
                value = json.loads(item['raw'])
                if item['direction'] == 'receive':
                    require(value['session'] == cid and value['pid'] == pid,
                            cid + ':IPC lineage')
                    receives.append(value)
                elif item['direction'] == 'send':
                    sends.append(value)
                else:
                    require(False, cid + ':IPC direction')
            require(receives[0] == ready, cid + ':ready raw binding')
            require(len(receives) == len(sends) + 1, cid + ':IPC denominator')
            for i, (req, res) in enumerate(zip(sends, receives[1:])):
                require(type(req['id']) is int and req['id'] == i and res['request_id'] == i,
                        cid + ':IPC request identity')
                require(req['op'] in ['snapshot', 'close'], cid + ':read-only IPC')
            require(sends[-1]['op'] == 'close', cid + ':close')
            for label in ['initial', 'post_press', 'post_move', 'terminal', 'closing']:
                if label in row:
                    require(row[label] in receives, cid + ':' + label + ' raw binding')
            for label in ['initial_server', 'final_server', 'cleanup_server']:
                s = row[label]
                require(type(s['button_mask']) is int and s['button_mask'] == 0
                        and len(s['keys']) == 32
                        and all(type(v) is int and v == 0 for v in s['keys']),
                        cid + ':' + label + ' neutral')
            for group in [events, effects]:
                previous = -1
                for item in group:
                    require(item['session'] == cid and item['pid'] == pid
                            and type(item['mono_ns']) is int and item['mono_ns'] >= previous,
                            cid + ':journal lineage/order')
                    previous = item['mono_ns']
            presses = [x for x in events if x['event'] == 'press']
            releases = [x for x in events if x['event'] == 'release']
            for i, e in enumerate(effects, 1):
                require(e['event'] == 'effect' and type(e['index']) is int and e['index'] == i
                        and type(e['value']) in [int, float], cid + ':effect schema')
            for snap in [r for r in receives if r['event'] == 'snapshot']:
                observed = [e for e in effects if e['mono_ns'] <= snap['mono_ns']]
                pe = [e for e in presses if e['mono_ns'] <= snap['mono_ns']]
                re = [e for e in releases if e['mono_ns'] <= snap['mono_ns']]
                require(type(snap['effect_count']) is int and snap['effect_count'] == len(observed)
                        and type(snap['presses']) is int and snap['presses'] == len(pe)
                        and type(snap['releases']) is int and snap['releases'] == len(re),
                        cid + ':snapshot journal accounting')
                require(snap['value'] == (observed[-1]['value'] if observed else 0),
                        cid + ':application value')
            require(row['initial']['value'] == 0 and row['initial']['effect_count'] == 0,
                    cid + ':baseline')
            cap = ready['receipt']
            expected_class = 'TButton' if kind == 'button' else 'Scale'
            require(cap['session'] == cid and type(cap['epoch']) is int and cap['epoch'] == 1
                    and cap['widget_class'] == expected_class
                    and cap['recipe'] == 'MOVE_AWAY_CANCEL'
                    and cap['abort_without_effect'] is (kind == 'button'), cid + ':capability')
            require(ready['bindtags'][1] == expected_class and ready['class_bindings']
                    and type(cap['widget_xid']) is int and type(cap['root_xid']) is int,
                    cid + ':widget identity')
            receipt = dict(cap)
            if recipe == 'STALE_CAPABILITY_CANCEL':
                receipt['epoch'] = 0
            require(row['candidate_receipt'] == receipt
                    and type(row['candidate_receipt']['epoch']) is int, cid + ':receipt binding')
            gated = recipe in recipes[3:]
            should_admit = not gated or (recipe == 'CAPABILITY_GATED_CANCEL' and kind == 'button')
            require(row['admitted'] is should_admit, cid + ':admission')
            move = recipe in ['MOVE_AWAY_CANCEL', 'CAPABILITY_GATED_CANCEL'] and should_admit
            ops = ['motion', 'press'] + (['motion'] if move else []) + ['release'] if should_admit else []
            require([x['op'] for x in row['input']] == ops, cid + ':input order')
            require(len(presses) == int(should_admit) and len(releases) == int(should_admit),
                    cid + ':app input delivery')
            require(row['closing']['effect_count'] == len(effects), cid + ':late effect')
            if should_admit:
                ins = row['input']
                require(ins[0]['point'] == ready['point'] and ins[-1]['point'] is None,
                        cid + ':input target')
                require(row['pressed_server']['button_mask'] == 256
                        and all(v == 0 for v in row['pressed_server']['keys']), cid + ':held witness')
                require(ins[1]['mono_ns'] <= presses[0]['mono_ns']
                        <= row['post_press']['mono_ns'] < ins[-1]['mono_ns']
                        <= releases[0]['mono_ns'] <= row['terminal']['mono_ns'],
                        cid + ':press-release causal order')
                if move:
                    require(ins[2]['point'] == ready['away']
                            and any(e['event'] == 'leave' and presses[0]['mono_ns'] < e['mono_ns']
                                    < releases[0]['mono_ns'] for e in events), cid + ':leave witness')
                if kind == 'scale':
                    require(ready['identified_part'] == 'trough2', cid + ':scale target')
            has_effect = bool(effects)
            want_effect = should_admit and (kind == 'scale' or not move)
            gate(has_effect == want_effect, cid + ':effect gate')
            if kind == 'scale' and should_admit:
                gate(row['post_press']['effect_count'] > 0, cid + ':effect precedes release')
            if kind == 'button' and should_admit:
                gate(row['post_press']['effect_count'] == 0, cid + ':button press alone')
            key = kind + '/' + recipe
            c = counts.setdefault(key, {'cases': 0, 'effects': 0, 'pre_release_effects': 0,
                                        'task_presses': 0, 'neutral': 0})
            c['cases'] += 1
            c['effects'] += int(has_effect)
            c['pre_release_effects'] += int(row.get('post_press', {}).get('effect_count', 0) > 0)
            c['task_presses'] += len(presses)
            c['neutral'] += int(row['final_server']['button_mask'] == 0)
    except Exception as exc:
        errors.append(type(exc).__name__ + ': ' + str(exc))
    result = ('HOLD_EVIDENCE_INCOMPLETE' if errors else
              'FAIL_WIDGET_PHASE_BOUNDARY' if failures else 'PASS_WIDGET_PHASE_BOUNDARY_SCOPED')
    return {'result': result, 'errors': errors, 'gate_failures': failures,
            'expected_cases': len(schedule), 'audited_cases': sum(c['cases'] for c in counts.values()),
            'counts': counts, 'construction': construction}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('root', type=Path)
    p.add_argument('--construction', action='store_true')
    a = p.parse_args()
    result = audit(a.root, a.construction)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result['result'].startswith('PASS') else 1)
