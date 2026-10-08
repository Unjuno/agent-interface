"""Read-only saved native packet/oracle audit; does not import candidate/policy/Xlib."""
import base64, copy, hashlib, io, json, sys
from pathlib import Path
from PIL import Image
MODES = ('TITLE', 'PARENT', 'ANCHOR', 'HIDDEN', 'DUPLICATE', 'STALE_HINT', 'CONTRADICTORY')
ARMS = ('FULL_REACQUIRE', 'SIMILARITY_FIRST', 'MEMORY_CUE', 'FRESH_CUE')
FIELDS = ('title', 'parent', 'anchor')

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def selection(records, fields):
    if any(type(r[f]) is not str for r in records for f in fields): return None
    hits = {r['id'] for r in records if any(r[f] == 'Target' for f in fields)}
    return list(hits)[0] if len(hits) == 1 else None

def validate_row(row, oracle):
    assert 'error' not in row and row['input_emissions'] == 0 and type(row['input_emissions']) is int
    assert row['dispatch_authority'] is False
    mode = row['mode']; assert mode in MODES
    assert oracle['mode'] == mode and oracle['repeat'] == row['repeat'] and oracle['epoch'] == row['epoch']
    ids = oracle['source_role_ids']; assert len(ids) == 2 and len(set(ids)) == 2 and all(type(i) is int and i > 1 for i in ids)
    assert oracle['intended_id'] == ids[1 if mode == 'CONTRADICTORY' else 0]
    assert oracle['admissible_resolution'] is (mode in ('TITLE', 'PARENT', 'ANCHOR', 'STALE_HINT'))
    expected = {'title': ['Save', 'Save'], 'parent': ['Doc', 'Doc'], 'anchor': ['Ledger', 'Ledger']}
    if mode == 'TITLE': expected['title'] = ['Target', 'Other']
    elif mode in ('PARENT', 'STALE_HINT'): expected['parent'] = ['Target', 'Other']
    elif mode == 'ANCHOR': expected['anchor'] = ['Target', 'Other']
    elif mode == 'HIDDEN': expected = {f: [None, None] for f in FIELDS}
    elif mode == 'DUPLICATE': expected['title'] = ['Target', 'Target']
    elif mode == 'CONTRADICTORY': expected['title'], expected['parent'] = ['Target', 'Other'], ['Other', 'Target']
    assert oracle['source_cue_values'] == expected
    initial = copy.deepcopy(expected)
    if mode in ('STALE_HINT', 'CONTRADICTORY'):
        initial['title'], initial['parent'] = ['Target', 'Other'], ['Doc', 'Doc']
        assert row['sequence_started_ns'] <= row['fixture_mutation_started_ns'] <= row['fixture_mutation_finished_ns'] <= row['sequence_finished_ns']
    acquired = row['acquisition']; assert acquired['packet']['epoch'] == row['epoch']
    assert acquired['canonical_bytes'] == len(canonical(acquired['packet']))
    assert len(acquired['calls']) == 12
    initial_records = acquired['packet']['records']; assert {r['id'] for r in initial_records} == set(ids)
    for r in initial_records:
        assert set(r) == {'id', *FIELDS} and type(r['id']) is int
        assert all(r[f] == initial[f][ids.index(r['id'])] for f in FIELDS)
    sufficient = [f for f in FIELDS if selection(initial_records, [f]) is not None]
    hint = sufficient[0] if sufficient else 'title'
    assert row['hint'] == {'field': hint, 'learned_requirement_only': True, 'authority': False, 'validity_proven': False, 'initial_unique_fields': sufficient, 'source_epoch': row['epoch']}
    assert row['hint']['learned_requirement_only'] is True and row['hint']['authority'] is False and row['hint']['validity_proven'] is False
    assert set(row['arms']) == set(ARMS)
    orders = []
    pixel_hashes = []
    for arm in ARMS:
        record = row['arms'][arm]; packet = record['packet']
        assert packet['epoch'] == row['epoch'] and record['canonical_bytes'] == len(canonical(packet))
        assert type(record['elapsed_ns']) is int and record['elapsed_ns'] >= 0
        data = packet['records']; assert len(data) == 2
        assert {r['id'] for r in data} == set(ids) and all(type(r['id']) is int for r in data)
        orders.append([r['id'] for r in data])
        fields = list(FIELDS) if arm == 'FULL_REACQUIRE' else ([] if arm == 'SIMILARITY_FIRST' else [hint])
        pixels = arm in ('FULL_REACQUIRE', 'SIMILARITY_FIRST')
        for r in data:
            assert set(r) == {'id', *fields, *(['image'] if pixels else [])}
            assert all(r[f] == expected[f][ids.index(r['id'])] for f in fields)
            if pixels:
                im = Image.open(io.BytesIO(base64.b64decode(r['image']['png_base64'], validate=True))); im.load()
                assert im.mode == 'RGB' and im.size == (32, 24) and r['image']['native_bytes'] == 3072
                digest = hashlib.sha256(im.tobytes()).hexdigest()
                assert digest == r['image']['pixel_sha256']; pixel_hashes.append(digest)
        wanted = data[0]['id'] if arm == 'SIMILARITY_FIRST' else selection(data, fields)
        assert type(record['selected']) is int if wanted is not None else record['selected'] is None
        assert record['selected'] == wanted
        count = 14 if arm == 'FULL_REACQUIRE' else (2 if arm == 'SIMILARITY_FIRST' else {'title': 2, 'parent': 4, 'anchor': 6}[hint])
        assert len(record['calls']) == count
        for call in record['calls']:
            assert type(call['window']) is int and call['window'] > 1
            assert row['sequence_started_ns'] <= call['start_ns'] <= call['end_ns'] <= row['sequence_finished_ns']
    assert all(order == orders[0] for order in orders) and len(set(pixel_hashes)) == 1
    memory, fresh = row['arms']['MEMORY_CUE'], row['arms']['FRESH_CUE']
    assert canonical(memory['packet']) == canonical(fresh['packet']) and memory['selected'] == fresh['selected']
    assert len(memory['calls']) == len(fresh['calls'])
    assert row['cleanup'] == {'keymap_empty': True, 'observed_buttons_1_to_3_neutral': True, 'connection_closed': True, 'server_exit': 0}
    # bool==1 is not accepted for state witnesses.
    assert all(row['cleanup'][k] is True for k in ('keymap_empty', 'observed_buttons_1_to_3_neutral', 'connection_closed'))
    assert type(row['cleanup']['server_exit']) is int
    return True

def check(rows, truth):
    assert len(rows) == len(truth) == 21
    assert {(r['mode'], r['repeat']) for r in rows} == {(m, i) for m in MODES for i in range(3)}
    oracle = {(r['mode'], r['repeat']): r for r in truth}; assert len(oracle) == 21
    assert len({r['epoch'] for r in rows}) == len({r['server_pid'] for r in rows}) == 21
    metrics = {arm: {'correct': 0, 'wrong': 0, 'unknown': 0, 'unsafe_bind': 0, 'false_unknown': 0, 'canonical_observation_bytes': 0, 'wrapped_native_calls': 0, 'measured_elapsed_ns': []} for arm in ARMS}
    for row in rows:
        o = oracle[(row['mode'], row['repeat'])]; validate_row(row, o)
        for arm in ARMS:
            a = row['arms'][arm]; m = metrics[arm]; selected = a['selected']
            m['unknown' if selected is None else ('correct' if selected == o['intended_id'] else 'wrong')] += 1
            m['unsafe_bind'] += int(selected is not None and (not o['admissible_resolution'] or selected != o['intended_id']))
            m['false_unknown'] += int(selected is None and o['admissible_resolution'])
            m['canonical_observation_bytes'] += a['canonical_bytes']; m['wrapped_native_calls'] += len(a['calls']); m['measured_elapsed_ns'].append(a['elapsed_ns'])
    memory = metrics['MEMORY_CUE']
    status = 'FAIL_SINGLE_CUE_IDENTITY_SAFETY' if memory['unsafe_bind'] else ('HOLD_STALE_DISCRIMINATOR_SUPPORT' if memory['false_unknown'] else 'HOLD_NO_MEMORY_SPECIFIC_GAIN')
    assert metrics['FULL_REACQUIRE']['unsafe_bind'] == metrics['FULL_REACQUIRE']['false_unknown'] == 0
    return {'first_status': status, 'metrics': metrics, 'same_memory_fresh_packets': 21, 'memory_specific_work_gain': False}

def controls(rows, truth):
    def wrong_selection(x):
        arm = x[0]['arms']['MEMORY_CUE']
        arm['selected'] = next(r['id'] for r in arm['packet']['records'] if r['id'] != arm['selected'])
    changes = [lambda x: x.pop(), lambda x: x[0].update(dispatch_authority=True), lambda x: x[0].update(input_emissions=True), wrong_selection, lambda x: x[0]['arms']['FRESH_CUE']['packet'].update(epoch='stale'), lambda x: x[0]['arms']['MEMORY_CUE'].update(canonical_bytes=0), lambda x: x[0]['arms']['FULL_REACQUIRE']['packet']['records'][0].update(id=True), lambda x: x[0]['cleanup'].update(server_exit=True)]
    results = []
    for i, change in enumerate(changes):
        altered = copy.deepcopy(rows); change(altered)
        assert canonical(altered) != canonical(rows), 'ineffective control'
        rejected = False
        try: check(altered, truth)
        except (AssertionError, KeyError, TypeError, ValueError): rejected = True
        results.append({'control': i, 'rejected': rejected})
    assert all(r['rejected'] for r in results)
    return results

def main():
    raw, oracle, target = map(Path, sys.argv[1:4])
    result = {'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(), 'oracle_sha256': hashlib.sha256(oracle.read_bytes()).hexdigest()}
    try:
        rows = [json.loads(s) for s in raw.read_text().splitlines()]; truth = [json.loads(s) for s in oracle.read_text().splitlines()]
        result.update(check(rows, truth)); result['controls'] = controls(rows, truth); result['audit_status'] = 'COMPLETE_SAVED_NATIVE_RECONSTRUCTION_SCOPED'
    except Exception as exc:
        result.update(first_status='STOP_INVALID_NATIVE_EVIDENCE', error=repr(exc), audit_status='STOP')
    with target.open('x') as f: json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result))
    return 1 if result['audit_status'] == 'STOP' else 0
if __name__ == '__main__': sys.exit(main())
