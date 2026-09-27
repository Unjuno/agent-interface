"""Independent raw-only reconstruction; imports neither reader nor runner."""
import copy
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'


def read_view(folder):
    raw_bytes = (folder / 'RAW.json').read_bytes()
    raw = json.loads(raw_bytes)
    cases = []
    for c in raw['cases']:
        stdout, stderr = (folder / c['stdout']).read_bytes(), (folder / c['stderr']).read_bytes()
        cases.append({'envelope': c, 'stdout': stdout, 'stderr': stderr,
                      'record': json.loads(stdout) if stdout else None})
    objects = {p.name: p.read_bytes() for p in (folder / 'objects').iterdir()}
    return {'raw': raw, 'raw_sha256': sha(raw_bytes), 'cases': cases, 'objects': objects,
            'journal': (folder / 'journal.jsonl').read_bytes()}


def audit(view, construction=False):
    errors = []
    def check(ok, label):
        if not ok:
            errors.append(label)
    def strict(actual, expected):
        return json_bytes(actual) == json_bytes(expected)
    raw = view['raw']
    if construction:
        expected = [(16, 1, 0), (16, 8, 0), (64, 1, 0), (64, 32, 0)]
    else:
        expected = []
        orders = ((1, 32, 128), (32, 128, 1), (128, 1, 32))
        for n in (128, 512, 2048):
            for rep, order in enumerate(orders):
                expected.extend((n, b, rep) for b in order)
    check(raw['status'] == 'COMPLETE', 'terminal')
    check(raw['formal'] is (not construction), 'phase')
    check(len(view['cases']) == len(expected) == len(raw['cases']), 'denominator')
    check(raw['start_wall_ns'] < raw['end_wall_ns'], 'parent_clock')
    check(view['journal'] == b''.join(json_bytes(c) for c in raw['cases']), 'journal')
    if not construction:
        freeze_bytes = (ROOT / 'FREEZE.json').read_bytes()
        freeze = json.loads(freeze_bytes)
        check(raw['freeze_sha256'] == sha(freeze_bytes), 'raw_freeze')
        for name, expected_sha in freeze['sha256'].items():
            check(sha((ROOT / name).read_bytes()) == expected_sha, 'source:' + name)
        upstream = (ROOT / 'reader.py').read_bytes()
        git = hashlib.sha1(b'blob ' + str(len(upstream)).encode() + b'\0' + upstream).hexdigest()
        check(git == 'ea72c166c2cea511ea91031dfbb14563fe4e3245', 'upstream_identity')
    for key, value in view['objects'].items():
        check(key == sha(value), 'object:' + key)
    metrics = []
    pids = []
    for index, (case, target) in enumerate(zip(view['cases'], expected)):
        n, batch, rep = target
        c, r = case['envelope'], case['record']
        label = str(index) + ':'
        check(strict([c['n'], c['batch'], c['rep']], list(target)), label + 'schedule')
        check(strict(c['index'], index), label + 'index')
        check(type(c['returncode']) is int and c['returncode'] == 0, label + 'exit')
        check(case['stderr'] == b'', label + 'stderr')
        check(sha(case['stdout']) == c['stdout_sha256'], label + 'stdout_hash')
        check(sha(case['stderr']) == c['stderr_sha256'], label + 'stderr_hash')
        check(json.loads(case['stdout']) == r, label + 'parsed_stdout')
        check(strict([r['n'], r['batch'], r['rep']], list(target)), label + 'child_schedule')
        check(r['affinity'] == [0], label + 'affinity')
        check(type(r['pid']) is int and r['pid'] > 0, label + 'pid')
        pids.append(r['pid'])
        check(r['freeze_sha256'] == raw['freeze_sha256'], label + 'child_freeze')
        check(r['source_unchanged'] is True, label + 'source_unchanged')
        data = view['objects'][r['input_sha256']]
        check(len(data) == 256 * n and data.endswith(b'\n'), label + 'corpus_size')
        lines = data.splitlines(keepends=True)
        check(len(lines) == n, label + 'corpus_count')
        for i, line in enumerate(lines, 1):
            record = json.loads(line)
            pad = record.pop('padding')
            check(strict(record, {'delivery_id': 'delivery:' + str(i), 'event': 'progress',
                                  'value': 'item-' + str(i).zfill(6)}), label + 'payload')
            check(len(line) == 256 and pad and set(pad) == {chr(97 + i % 26)}, label + 'padding')
            record['padding'] = pad
            check(json_bytes(record) == line, label + 'canonical_bytes')
        m, size = n // batch, len(data)
        expected_cursor = {'schema': 'agent-interface/experimental-read-cursor-v1',
                           'stream_id': f'backlog-3988-{n}', 'offset': size,
                           'next_sequence': n + 1, 'prefix_sha256': sha(data)}
        expected_trace = [[batch, k * batch * 256, k * batch + 1,
                           'end' if k == m else 'limit', None, 'none', False, False]
                          for k in range(1, m + 1)]
        for mode in ('timed', 'accounting'):
            p = r['passes'][mode]
            check(view['objects'][p['data']] == data, label + mode + '_returned_bytes')
            check(strict(p['cursor'], expected_cursor), label + mode + '_cursor')
            check(strict(json.loads(view['objects'][p['trace']]), expected_trace), label + mode + '_trace')
            clocks = p['clocks']
            check(len(clocks) == 5 and all(type(v) is int and v >= 0 for v in clocks), label + mode + '_clock_type')
            cpu0, cpu1, wall0, first, wall1 = clocks
            check(cpu0 < cpu1 and wall0 <= first <= wall1 and wall0 < wall1, label + mode + '_clock_order')
        expected_counts = {'opens': m, 'reads': m, 'requested_bytes': m * 1048577,
                           'read_bytes': size * m, 'hash_calls': 2 * m,
                           'hash_bytes': size * m}
        check(strict(r['counts'], expected_counts), label + 'accounting')
        expected_empty = {'schema': 'agent-interface/experimental-inbox-read-v1',
                          'records': [], 'tail_state': 'end', 'problem': None,
                          'next_cursor': expected_cursor, 'authority': 'none',
                          'acknowledged': False, 'input_dispatched': False}
        check(strict(r['empty'], expected_empty), label + 'empty_tail')
        cpu0, cpu1, wall0, first, wall1 = r['passes']['timed']['clocks']
        metrics.append({'n': n, 'batch': batch, 'rep': rep, 'cpu_ns': cpu1 - cpu0,
                        'wall_ns': wall1 - wall0, 'first_ns': first - wall0,
                        'read_bytes': size * m, 'hash_bytes': size * m})
    check(len(set(pids)) == len(pids), 'unique_processes')
    summary = []
    for n, batch in sorted({(r['n'], r['batch']) for r in metrics}):
        rows = [r for r in metrics if r['n'] == n and r['batch'] == batch]
        item = {'n': n, 'batch': batch, 'repetitions': len(rows)}
        for measure in ('cpu_ns', 'wall_ns', 'first_ns', 'read_bytes', 'hash_bytes'):
            values = [r[measure] for r in rows]
            item[measure] = {'median': statistics.median(values), 'min': min(values), 'max': max(values)}
        summary.append(item)
    ratio = None
    if not construction and not errors:
        lookup = {(r['n'], r['batch']): r for r in summary}
        ratio = lookup[2048, 128]['cpu_ns']['median'] / lookup[2048, 1]['cpu_ns']['median']
    verdict = ('FAIL_AUDIT' if errors else 'PASS_CONSTRUCTION' if construction else
               'PASS_READER_BATCH_COST_SCOPED' if ratio <= .5 else 'HOLD_BATCH_CPU_BENEFIT_NOT_ESTABLISHED')
    return {'verdict': verdict, 'errors': errors, 'cases': len(view['cases']),
            'raw_sha256': view['raw_sha256'], 'cpu_ratio_128_over_1_at_2048': ratio,
            'summary': summary}


def controls(view, construction=False):
    checks = {}
    names = ('missing_case', 'duplicate_case', 'wrong_exit', 'read_byte_count',
             'hash_byte_count', 'clock_bool', 'cursor', 'authority', 'returned_record', 'trace')
    for name in names:
        v = copy.deepcopy(view)
        c = v['cases'][0]
        r = c['record']
        if name == 'missing_case':
            v['cases'].pop()
        elif name == 'duplicate_case':
            v['cases'][1] = copy.deepcopy(c)
        elif name == 'wrong_exit':
            c['envelope']['returncode'] = None
        elif name == 'read_byte_count':
            r['counts']['read_bytes'] += 1
        elif name == 'hash_byte_count':
            r['counts']['hash_bytes'] += 1
        elif name == 'clock_bool':
            r['passes']['timed']['clocks'][0] = True
        elif name == 'cursor':
            r['passes']['timed']['cursor']['offset'] -= 256
        elif name == 'authority':
            r['empty']['acknowledged'] = True
        elif name == 'returned_record':
            key = r['passes']['timed']['data']
            altered = v['objects'][key].replace(b'item-000001', b'item-999999', 1)
            v['objects'][sha(altered)] = altered
            r['passes']['timed']['data'] = sha(altered)
        else:
            key = r['passes']['timed']['trace']
            trace = json.loads(v['objects'][key])
            trace[0][0] += 1
            altered = json_bytes(trace)
            v['objects'][sha(altered)] = altered
            r['passes']['timed']['trace'] = sha(altered)
        # Refresh transport hashes, so semantic controls do not merely fail a checksum.
        if name not in ('missing_case', 'duplicate_case'):
            c['stdout'] = json_bytes(r)
            c['envelope']['stdout_sha256'] = sha(c['stdout'])
        v['raw']['cases'] = [c['envelope'] for c in v['cases']]
        v['journal'] = b''.join(json_bytes(c) for c in v['raw']['cases'])
        checks[name] = bool(audit(v, construction)['errors'])
    return checks


if __name__ == '__main__':
    folder = Path(sys.argv[1]).resolve()
    construction = '--construction' in sys.argv
    view = read_view(folder)
    result = audit(view, construction)
    result['corruption_controls'] = controls(view, construction)
    print(json_bytes(result).decode(), end='')
    raise SystemExit(0 if not result['errors'] and all(result['corruption_controls'].values()) else 2)
