"""Independent raw-only audit: no imports from worker, runner or upstream reader."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import sys

POLICIES = ['BLIND_REPLACE', 'OFFSET_MAX', 'REVISION_CAS']
SCHEDULES = ['OVERLAP_SMALL_FIRST', 'OVERLAP_LARGE_FIRST', 'EXACT_RESPONSE_REPLAY', 'SEQUENTIAL']


def serial(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def same(a, b):
    # JSON type distinctions, including bool vs int, must survive comparison.
    return serial(a) == serial(b)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decode_frame(hexed):
    data = bytes.fromhex(hexed)
    assert data.endswith(b'\n') and data.count(b'\n') == 1, 'framing'
    return json.loads(data)


def check_case(raw):
    cid, policy, schedule, rep = (raw[k] for k in ('case_id', 'policy', 'schedule', 'repetition'))
    assert policy in POLICIES and schedule in SCHEDULES and type(rep) is int and rep in (1, 2, 3)
    assert cid == f'{policy}__{schedule}__{rep}', 'case identity'
    sid = f'fixed-owner-{cid}'
    assert raw['stream_id'] == sid
    rows = [{'event': 'notification_fixture', 'ordinal': i, 'payload': f'payload-{cid}-{i}',
             'delivery_id': f'delivery:{i}'} for i in range(1, 7)]
    lines = [(serial(r) + '\n').encode() for r in rows]
    source = b''.join(lines)
    assert bytes.fromhex(raw['stream_hex']) == source, 'source payload'
    assert raw['source_before_sha256'] == raw['source_after_sha256'] == digest(source), 'source hash'

    def cursor(n):
        prefix = b''.join(lines[:n])
        return {'schema': 'agent-interface/experimental-read-cursor-v1', 'stream_id': sid,
                'offset': len(prefix), 'next_sequence': n + 1, 'prefix_sha256': digest(prefix)}

    current = {'revision': 0, 'cursor': cursor(0), 'batches': []}
    assert same(raw['initial'], current), 'initial'
    processes = raw['processes']
    assert len(processes) == 3 and {p['worker'] for p in processes} == {'A', 'B', 'C'}, 'process set'
    assert len({p['pid'] for p in processes}) == 3, 'distinct processes'
    pids = {}
    for p in processes:
        assert type(p['pid']) is int and p['pid'] > 0
        assert type(p['returncode']) is int and p['returncode'] == 0, 'process exit'
        assert p['forced_kill'] is False and p['stderr_hex'] == '', 'process cleanup'
        assert p['argv'][-3:] == [p['worker'], policy, sid], 'process argv'
        assert Path(p['argv'][2]).name == 'worker.py'
        pids[p['worker']] = p['pid']
    expected_ops = [('A', 'prepare')]
    if schedule == 'SEQUENTIAL':
        expected_ops += [('A', 'commit'), ('B', 'prepare'), ('B', 'commit')]
    elif schedule == 'EXACT_RESPONSE_REPLAY':
        expected_ops += [('A', 'commit'), ('A', 'commit')]
    else:
        expected_ops += [('B', 'prepare')]
        expected_ops += [(w, 'commit') for w in (('A', 'B') if schedule == SCHEDULES[0] else ('B', 'A'))]
    expected_ops += [('C', 'prepare'), ('C', 'commit')] + [(w, 'quit') for w in ('A', 'B', 'C')]
    assert len(raw['events']) == len(expected_ops), 'event denominator'
    prepared, clocks = {}, {}
    regressions = rejections = 0
    for event, (worker, op) in zip(raw['events'], expected_ops):
        req, result = decode_frame(event['request_hex']), decode_frame(event['response_hex'])
        assert event['worker'] == worker and req['op'] == op, 'schedule'
        assert result['pid'] == pids[worker] and type(result['pid']) is int, 'event PID'
        start, finish = result['started_ns'], result['finished_ns']
        assert type(start) is int and type(finish) is int and 0 <= start <= finish
        assert start >= clocks.get(worker, 0), 'worker timestamp order'
        clocks[worker] = finish
        assert same(event['before'], current), 'before snapshot'
        before_offset = current['cursor']['offset']
        if op == 'prepare':
            limit = {'A': 2, 'B': 4, 'C': 32}[worker]
            assert type(req['limit']) is int and req['limit'] == limit
            assert req['request_id'] == f'{cid}/{worker}'
            n = current['cursor']['next_sequence'] - 1
            end = min(6, n + limit)
            response = {'schema': 'agent-interface/experimental-inbox-read-v1', 'records': rows[n:end],
                        'tail_state': 'limit' if end < 6 else 'end', 'problem': None,
                        'next_cursor': cursor(end), 'authority': 'none',
                        'acknowledged': False, 'input_dispatched': False}
            expected = {'request_id': req['request_id'],
                        'start': {'revision': current['revision'], 'cursor': current['cursor']},
                        'response': response}
            assert same(result['prepared'], expected), 'prepared response'
            prepared[worker] = copy.deepcopy(expected)
        elif op == 'commit':
            p = prepared[worker]
            stale = not same(p['start'], {'revision': current['revision'], 'cursor': current['cursor']})
            accepted = policy != 'REVISION_CAS' or not stale
            assert result['request_id'] == p['request_id']
            assert result['disposition'] == ('COMMITTED' if accepted else 'STALE_RESULT'), 'commit admission'
            if accepted:
                target = p['response']['next_cursor']
                if policy == 'OFFSET_MAX' and current['cursor']['offset'] > target['offset']:
                    target = current['cursor']
                current['batches'].append({'index': len(current['batches']) + 1, 'worker': worker,
                                          'request_id': p['request_id'], 'response': p['response']})
                current['cursor'] = copy.deepcopy(target)
                current['revision'] += 1
            else:
                rejections += 1
        else:
            assert result['disposition'] == 'EXIT'
        assert same(event['after'], current), 'after snapshot'
        regressions += current['cursor']['offset'] < before_offset
    assert same(raw['final'], current), 'final snapshot'
    assert same(current['cursor'], cursor(6)), 'complete final cursor'
    retained = [r for b in current['batches'] for r in b['response']['records']]
    counts = [sum(same(r, original) for r in retained) for original in rows]
    assert all(count >= 1 for count in counts), 'omitted record'
    assert sum(counts) == len(retained), 'unexpected payload'
    duplicates = len(retained) - 6
    expected_duplicates = 0 if policy == 'REVISION_CAS' or schedule == 'SEQUENTIAL' else (
        4 if policy == 'BLIND_REPLACE' and schedule == 'OVERLAP_LARGE_FIRST' else 2)
    assert duplicates == expected_duplicates, 'duplicate gate'
    assert regressions == int(policy == 'BLIND_REPLACE' and schedule == 'OVERLAP_LARGE_FIRST'), 'regression gate'
    assert rejections == int(policy == 'REVISION_CAS' and schedule != 'SEQUENTIAL'), 'rejection gate'
    if policy == 'REVISION_CAS':
        assert same(retained, rows), 'candidate contiguous exact retention'
    return {'case_id': cid, 'policy': policy, 'schedule': schedule, 'duplicates': duplicates,
            'regressions': regressions, 'stale_rejections': rejections, 'omitted': 0,
            'retained_count': len(retained)}


def audit(folder, source_folder):
    root = Path(folder)
    freeze_bytes = (source_folder / 'FREEZE.json').read_bytes()
    freeze = json.loads(freeze_bytes)
    run = json.loads((root / 'RUN.json').read_bytes())
    assert run['freeze_sha256'] == digest(freeze_bytes), 'freeze identity'
    for name, h in freeze['sha256'].items():
        assert digest((source_folder / name).read_bytes()) == h, f'source:{name}'
    assert run['status'] == 'COMPLETED', 'run incomplete'
    reps = range(1, 4) if run['mode'] == 'formal' else range(1, 2)
    ids = [f'{p}__{s}__{r}' for p, s, r in itertools.product(POLICIES, SCHEDULES, reps)]
    assert [r['case_id'] for r in run['cases']] == ids, 'case set/order'
    metrics, raws = [], []
    for row in run['cases']:
        case_path = root / row['case_id']
        rawbytes = (case_path / 'raw.json').read_bytes()
        assert digest(rawbytes) == row['raw_sha256'], 'raw identity'
        raw = json.loads(rawbytes)
        assert raw['case_id'] == row['case_id']
        assert digest((case_path / 'host.sqlite').read_bytes()) == raw['database_sha256'], 'database bytes'
        assert (case_path / 'stream.jsonl').read_bytes().hex() == raw['stream_hex'], 'retained stream bytes'
        events = [json.loads(l) for l in (case_path / 'journal.jsonl').read_text().splitlines()]
        assert same(events, raw['events']), 'journal binding'
        for proc in raw['processes']:
            assert (case_path / f"{proc['worker']}.stderr").read_bytes().hex() == proc['stderr_hex']
        with sqlite3.connect(f'file:{case_path / "host.sqlite"}?mode=ro', uri=True) as db:
            rev, cur = db.execute('SELECT revision,cursor FROM state WHERE id=1').fetchone()
            batches = [{'index': i, 'worker': w, 'request_id': rid, 'response': json.loads(resp)}
                       for i, w, rid, resp in db.execute('SELECT id,worker,request_id,response FROM batches ORDER BY id')]
        assert same({'revision': rev, 'cursor': json.loads(cur), 'batches': batches}, raw['final']), 'database state'
        metrics.append(check_case(raw))
        raws.append(raw)
    # Semantic mutations operate on copies, beyond the outer raw-file digest gate.
    mutations = []
    baseline = raws[0]
    mutators = {
        'missing_event': lambda r: r['events'].pop(),
        'duplicate_event': lambda r: r['events'].append(copy.deepcopy(r['events'][0])),
        'boolean_revision': lambda r: r['initial'].__setitem__('revision', False),
        'wrong_cursor': lambda r: r['final']['cursor'].__setitem__('offset', 1),
        'missing_process_exit': lambda r: r['processes'][0].pop('returncode'),
        'wrong_source': lambda r: r.__setitem__('stream_hex', '00' + r['stream_hex'][2:]),
        'wrong_payload': lambda r: r['final']['batches'][0]['response']['records'][0].__setitem__('payload', 'altered'),
        'false_authority': lambda r: r['final']['batches'][0]['response'].__setitem__('input_dispatched', True),
    }
    for name, mutate in mutators.items():
        changed = copy.deepcopy(baseline)
        mutate(changed)
        rejected = False
        try:
            check_case(changed)
        except (AssertionError, KeyError, ValueError, TypeError):
            rejected = True
        assert rejected, f'accepted mutation:{name}'
        mutations.append({'mutation': name, 'rejected': rejected})
    return {'decision': 'PASS_CONCURRENT_READER_COMMIT_BOUNDARY_SCOPED',
            'mode': run['mode'], 'cases': len(metrics), 'errors': [],
            'metrics': metrics, 'corruption_controls': mutations,
            'run_sha256': digest((root / 'RUN.json').read_bytes())}


if __name__ == '__main__':
    try:
        result = audit(sys.argv[1], Path(__file__).resolve().parent)
    except Exception as exc:
        print(serial({'decision': 'HOLD_AUDIT', 'error': f'{type(exc).__name__}:{exc}'}))
        raise
    print(serial(result))
