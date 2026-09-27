"""Independent raw-only auditor. Does not import study.py or load native.so."""
from __future__ import annotations
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import statistics
import zlib

KINDS = ['prompt', 'delayed_same', 'delayed_changed', 'missing', 'boolean',
         'reversed', 'future', 'stale_identity']
AGE = 100_000_000
HOLD = 150_000_000


def digest(b):
    return hashlib.sha256(b).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def pairs(items):
    d = {}
    for k, v in items:
        if k in d:
            raise ValueError('duplicate JSON key')
        d[k] = v
    return d


def loads(s):
    return json.loads(s, object_pairs_hook=pairs)


def unpack(frame):
    b = zlib.decompress(base64.b64decode(frame['pixels_z64'], validate=True))
    assert len(b) == 4096, 'PIXEL_LENGTH'
    assert digest(b) == frame['pixels_sha256'], 'PIXEL_DIGEST'
    return b


def integer(v, minimum=0):
    assert type(v) is int and v >= minimum, 'INTEGER_TYPE'
    return v


def monotone(values):
    for v in values:
        integer(v, 1)
    assert values == sorted(values), 'CLOCK_ORDER'


def no_input(sample):
    assert len(sample['keys']) == 32, 'KEYMAP_LENGTH'
    assert all(type(x) is int and x == 0 for x in sample['keys']), 'KEY_HELD'
    assert integer(sample['mask']) & 0x1f00 == 0, 'BUTTON_HELD'
    integer(sample['sample_ns'], 1)


def rgb(frame, expected):
    data = unpack(frame)
    assert all(data[i:i + 3] == expected for i in range(0, 4096, 4)), 'RGB_PATTERN'
    if 'bytes' in frame:
        assert integer(frame['bytes']) == 4096, 'BYTE_COUNT'
    return data


def audit(records, frozen=None, construction=False):
    errors, rows, ages, native_times, transit_times = [], [], {}, [], []
    gates = []
    try:
        h = records[0]
        count = 1 if construction else 3
        assert h['event'] == 'header', 'HEADER'
        assert h['mode'] == ('construction' if construction else 'formal'), 'MODE'
        assert integer(h['repetitions']) == count, 'REPETITIONS'
        assert integer(h['age_ns']) == AGE and integer(h['hold_ns']) == HOLD, 'BUDGET'
        for key in ['model_calls', 'input_events']:
            assert integer(h[key]) == 0, 'NO_CALL_HEADER'
        if not construction:
            assert frozen is not None and h['freeze_sha256'] == digest(frozen), 'FREEZE_BINDING'
        assert len(records) == 4 + 8 * count, 'RECORD_COUNT'
        assert records[1]['event'] == 'display', 'DISPLAY'
        assert '-nolisten' in records[1]['argv'] and 'tcp' in records[1]['argv'], 'DISPLAY_NETWORK'
        no_input(records[1]['initial_neutral'])
        assert records[-2]['event'] == 'cleanup', 'CLEANUP_EVENT'
        rgb(records[-2]['frame'], b'\x10\x10\x10')
        no_input(records[-2]['neutral'])
        assert records[-1]['event'] == 'exit', 'EXIT_EVENT'
        assert records[-1]['status'] == 'COMPLETED_UNSCORED', 'RUNNER_STOP'
        assert type(records[-1]['xvfb_exit']) is int and records[-1]['xvfb_exit'] in (0, -15), 'XVFB_EXIT'
        rows = records[2:-2]
        for i, r in enumerate(rows):
            try:
                kind = KINDS[i % 8]
                assert integer(r['index']) == i and r['event'] == 'case', 'ROW_ID'
                assert r['kind'] == kind, 'ROW_KIND'
                assert r['session'] == h['session'], 'SESSION'
                assert r['request_id'] == f"{h['session']}/{i:02d}", 'REQUEST_ID'
                for key in ['worker_exit', 'model_calls', 'input_events']:
                    assert integer(r[key]) == 0, 'EXIT_OR_CALL'
                assert integer(r['worker_ready']['pid'], 1) != integer(h['pid'], 1), 'PROCESS_ISOLATION'
                assert r['worker_ready']['time_namespace'] == h['time_namespace'], 'TIME_NAMESPACE_DECLARATION'
                s, p, t = r['source'], r['packet'], r['source']['native']
                assert len(t) == 6, 'NATIVE_TRACE'
                monotone([s['python_before'], *t[:4], s['python_after']])
                assert integer(t[4]) <= integer(t[5]), 'CPU_ORDER'
                before = rgb(r['before'], b'\x32\x32\xdc')
                source = rgb(s, b'\x32\x32\xdc')
                assert source == before == unpack(p), 'CAPTURE_PIXEL_BINDING'
                assert r['before']['depth'] == r['current']['depth'] == 24, 'DEPTH'
                current = rgb(r['current'], b'\x10\x10\x10' if kind == 'delayed_changed' else b'\x32\x32\xdc')
                assert (current != source) == (kind == 'delayed_changed'), 'CURRENT_PIXEL_DISCRIMINATOR'
                no_input(r['neutral'])
                protocol = r['protocol']
                assert len(protocol) == 5, 'PROTOCOL_LENGTH'
                assert [q['direction'] for q in protocol] == ['recv', 'send', 'recv', 'send', 'recv'], 'PROTOCOL_ORDER'
                messages = [loads(q['line']) for q in protocol]
                expected_request = {'op': 'capture', 'kind': kind, 'request_id': r['request_id'], 'session': r['session']}
                assert canonical(messages[0]) == canonical(r['worker_ready']), 'READY_BINDING'
                assert canonical(messages[1]) == canonical(expected_request), 'REQUEST_BINDING'
                assert canonical(messages[2]) == canonical({'event': 'captured', 'capture': s}), 'SOURCE_BINDING'
                assert messages[3] == {'op': 'deliver'}, 'RELEASE_BINDING'
                assert canonical(messages[4]) == canonical({'event': 'delivered', 'packet': p, 'publish_ns': r['publish_ns']}), 'DELIVERY_BINDING'
                assert protocol[1]['ns'] == r['request_send_ns'], 'REQUEST_TIME'
                assert protocol[3]['ns'] == r['release_send_ns'], 'RELEASE_TIME'
                monotone([r['before']['start'], r['before']['end'], *[q['ns'] for q in protocol[:2]],
                          s['python_before'], *t[:4], s['python_after'], protocol[2]['ns'],
                          r['display_ready_ns'], r['release_send_ns'], r['publish_ns'], protocol[4]['ns'],
                          r['consume_ns'], r['current']['start'], r['current']['end'], r['neutral']['sample_ns']])
                expected_packet = {'request_id': r['request_id'], 'session': r['session'], 'capture': t[1:3],
                                   'pixels_z64': s['pixels_z64'], 'pixels_sha256': s['pixels_sha256']}
                if kind == 'missing':
                    del expected_packet['capture']
                elif kind == 'boolean':
                    expected_packet['capture'] = [True, True]
                elif kind == 'reversed':
                    expected_packet['capture'] = [t[2] + 1, t[1]]
                elif kind == 'future':
                    expected_packet['capture'] = [t[2] + 60_000_000_000] * 2
                elif kind == 'stale_identity':
                    expected_packet['request_id'] = 'predecessor-request'
                assert canonical(expected_packet) == canonical(p), 'PACKET_RECONSTRUCTION'
                age = r['consume_ns'] - t[1]
                ages.setdefault(kind, []).append(age)
                native_times.append(t[2] - t[1])
                transit_times.append(r['consume_ns'] - s['python_after'])
                if kind.startswith('delayed'):
                    assert r['release_send_ns'] - t[2] >= HOLD, 'DELAY_NOT_EXPOSED'
                if kind == 'stale_identity':
                    capture = {'admit': False, 'reason': 'IDENTITY'}
                elif kind in ('missing', 'boolean'):
                    capture = {'admit': False, 'reason': 'CAPTURE_TYPE'}
                elif kind in ('reversed', 'future'):
                    capture = {'admit': False, 'reason': 'CAPTURE_ORDER'}
                elif age > AGE:
                    capture = {'admit': False, 'reason': 'STALE'}
                else:
                    capture = {'admit': True, 'reason': 'CAPTURE_AGE_VALID'}
                arrival = ({'admit': False, 'reason': 'IDENTITY'} if kind == 'stale_identity'
                           else {'admit': True, 'reason': 'ARRIVAL_RESTAMPED'})
                assert canonical(capture) == canonical(r['capture_age']), 'CANDIDATE_DECISION'
                assert canonical(arrival) == canonical(r['arrival_age']), 'COMPARATOR_DECISION'
                gates.append(capture['admit'] == (kind == 'prompt'))
            except Exception as e:
                errors.append(f'row {i}: {type(e).__name__}: {e}')
    except Exception as e:
        errors.append(f'structure: {type(e).__name__}: {e}')
    status = ('FAIL_INDEPENDENT_AUDIT' if errors else
              'PASS_CAPTURE_AGE_BOUNDARY_SCOPED' if all(gates) and gates else
              'HOLD_POSITIVE_OR_BOUNDARY_UNRESOLVED')
    def bounds(values):
        return {'min_ns': min(values), 'median_ns': statistics.median(values), 'max_ns': max(values)} if values else None
    return {'status': status, 'errors': errors, 'rows': len(rows), 'mode': 'construction' if construction else 'formal',
            'capture_age_by_kind': {k: bounds(v) for k, v in ages.items()},
            'native_acquisition': bounds(native_times), 'post_capture_to_consumer': bounds(transit_times),
            'candidate_admitted': sum(r.get('capture_age', {}).get('admit') is True for r in rows),
            'arrival_admitted': sum(r.get('arrival_age', {}).get('admit') is True for r in rows),
            'delayed_changed_false_admissions': sum(r.get('kind') == 'delayed_changed' and
                r.get('arrival_age', {}).get('admit') is True for r in rows)}


def mutations(records, frozen, construction):
    def drop(r): del r[2]
    def duplicate(r): r.insert(2, copy.deepcopy(r[2]))
    def decision(r): r[3]['capture_age']['admit'] = True
    def identity(r): r[2]['packet']['request_id'] = 'other'
    def source(r): r[2]['source']['native'][1] += 1
    def pixel(r): r[2]['current']['pixels_sha256'] = '0' * 64
    def exit_missing(r): del r[2]['worker_exit']
    def bool_index(r): r[2]['index'] = False
    def hold(r): r[3]['release_send_ns'] = r[3]['source']['native'][2]
    def release_missing(r): del r[2]['protocol'][3]
    def held(r): r[2]['neutral']['keys'][0] = 1
    def byte_count(r): r[2]['source']['bytes'] = True
    cases = [drop, duplicate, decision, identity, source, pixel, exit_missing,
             bool_index, hold, release_missing, held, byte_count]
    results = []
    for change in cases:
        modified = copy.deepcopy(records)
        change(modified)
        result = audit(modified, frozen, construction)
        results.append({'mutation': change.__name__, 'rejected': bool(result['errors']), 'errors': result['errors']})
    return results


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('raw', type=Path)
    p.add_argument('--freeze', type=Path)
    p.add_argument('--construction', action='store_true')
    p.add_argument('--mutations', action='store_true')
    args = p.parse_args()
    b = args.raw.read_bytes()
    if args.raw.name.endswith('.b64'):
        b = zlib.decompress(base64.b64decode(b, validate=False))
    frozen = args.freeze.read_bytes() if args.freeze else None
    records = [loads(line) for line in b.splitlines()]
    result = audit(records, frozen, args.construction)
    result['raw_sha256'] = digest(b)
    result['raw_bytes'] = len(b)
    if args.mutations:
        result['corruption_controls'] = mutations(records, frozen, args.construction)
        if not all(c['rejected'] for c in result['corruption_controls']):
            result['status'] = 'FAIL_CORRUPTION_CONTROL'
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result['status'] == 'PASS_CAPTURE_AGE_BOUNDARY_SCOPED' else 2)
