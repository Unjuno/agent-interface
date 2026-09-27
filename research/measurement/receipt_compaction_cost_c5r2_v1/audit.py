"""Raw-only audit and descriptive statistics; imports no study/runtime modules."""
import copy
import hashlib
import json
from pathlib import Path
import statistics
import sys
from collections import Counter

MODES = ('plain', 'compact', 'report_refs')
NAMES = ('minimal', 'detail_256', 'detail_8192', 'repeat_8', 'repeat_64', 'unique_64')
COLUMNS = ['round', 'warmup', 'mode', 'producer_wall_start', 'producer_cpu_start',
           'producer_cpu_end', 'producer_wall_end', 'consumer_wall_start',
           'consumer_cpu_start', 'consumer_cpu_end', 'consumer_wall_end', 'output_sha256']


def encoded(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(b):
    return hashlib.sha256(b).hexdigest()


def expand(view):
    out = copy.deepcopy(view)
    schema = out['schema']
    if schema == 'agent-interface/receipt-view-v3-report-ref':
        if out['report'] != {'report_ref': '/source/raw_report'} or out['report_reference'] != '/source/raw_report':
            raise ValueError('report reference')
        out['report'] = copy.deepcopy(out['source']['raw_report'])
        del out['report_reference'], out['reference_scope']
    elif schema == 'agent-interface/receipt-view-v2-event-refs':
        refs = out.pop('event_references')
        del out['reference_scope']
        visited = set()
        def walk(x, path):
            if path in refs:
                n = refs[path]
                if type(n) is not int or not 0 <= n < len(out['events']) or x != {'event_ref': n}:
                    raise ValueError('event reference')
                visited.add(path)
                return copy.deepcopy(out['events'][n])
            if isinstance(x, dict):
                return {k: walk(v, path + '/' + k.replace('~', '~0').replace('/', '~1')) for k, v in x.items()}
            if isinstance(x, list):
                return [walk(v, path + '/' + str(i)) for i, v in enumerate(x)]
            return x
        out['report'] = walk(out['report'], '/report')
        if visited != set(refs):
            raise ValueError('unvisited reference')
    elif schema != 'agent-interface/receipt-view-v1':
        raise ValueError('receipt schema')
    out['schema'] = 'agent-interface/receipt-view-v1'
    return out


def expected_view(text):
    p = json.loads(text)
    rows = p.get('records', [])
    routine = {'observation', 'command', 'decision_evidence', 'accepted', 'step_started', 'step_completed'}
    visible = [x for x in rows if x.get('event') not in routine]
    return {'schema': 'agent-interface/receipt-view-v1', 'authority': 'none',
            'source': {'path': None, 'sha256': digest(text.encode()), 'bytes': len(text.encode()),
                       'kind': 'received_bytes', 'raw_report': p},
            'report': {k: v for k, v in p.items() if k != 'records'},
            'latest_observations': [], 'events': visible,
            'record_counts': dict(sorted(Counter(x['event'] for x in rows).items())),
            'omitted_from_view': len(rows) - len(visible),
            'scope': 'Received historical receipt. Full history retained in source.raw_report. No input or freshness granted.',
            'motor_state_validation': {'present': False, 'accepted': False, 'reason': 'missing'}}


def inspect(case, execution, expected_input):
    errors = []
    def check(ok, name):
        if not ok:
            errors.append(name)
    try:
        i = case['index']
        check(type(i) is int and 0 <= i < 6 and case['condition'] == NAMES[i], 'condition identity')
        check(case['columns'] == COLUMNS, 'sample schema')
        check(digest(case['input'].encode()) == expected_input == case['input_sha256'], 'input hash')
        check(type(execution['exit']) is int and execution['exit'] == 0 and execution['timeout'] is False, 'process exit')
        check(type(execution['pid']) is int and execution['pid'] == case['pid'], 'process identity')
        check(execution['index'] == i and execution['stderr'] == '', 'execution metadata')
        check(len(case['samples']) == 69, 'sample denominator')
        original = expected_view(case['input'])
        original_report = original['source']['raw_report']
        check(original_report['result']['recovery_required'] is (i != 0), 'synthetic recovery fixture')
        output = {mode: json.loads(case['outputs'][mode]) for mode in MODES}
        check(set(case['outputs']) == set(MODES), 'mode denominator')
        plain_nonreceipt = {k: v for k, v in output['plain'].items() if k != 'receipt'}
        check(plain_nonreceipt['schema'] == 'agent-interface/review-v1' and
              plain_nonreceipt['authority'] == 'none' and plain_nonreceipt['image'] is None and
              plain_nonreceipt['image_status'] == 'no_observation', 'no image or authority')
        s = plain_nonreceipt['outcome_summary']
        check(s['input_release_verified'] is (i == 0), 'retained release outcome')
        check(s['recovery_required'] is (i != 0), 'retained recovery outcome')
        check(s['reported_status'] == original_report['status'] and
              s['execution_status'] == original_report['result']['status'], 'retained status')
        check(s['failed_operation_effect'] == (None if i == 0 else 'unknown'), 'partial effect')
        for mode, out in output.items():
            check(encoded(expand(out['receipt'])) == encoded(original), 'exact reconstruction:' + mode)
            check(encoded({k: v for k, v in out.items() if k != 'receipt'}) == encoded(plain_nonreceipt), 'outcome parity:' + mode)
            check(len(encoded(out['receipt'])) <= len(encoded(original)), 'receipt size:' + mode)
        for n, row in enumerate(case['samples']):
            cycle, slot = divmod(n, 3)
            check(row[:3] == [cycle - 2, cycle < 2, MODES[(cycle + slot) % 3]], 'sample order:' + str(n))
            check(all(type(x) is int and x >= 0 for x in row[3:11]), 'clock types:' + str(n))
            check(row[3] <= row[6] <= row[7] <= row[10] and row[4] <= row[5] <= row[8] <= row[9], 'clock order:' + str(n))
            check(row[11] == digest(case['outputs'][row[2]].encode()), 'wire hash:' + str(n))
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        errors.append('invalid evidence:' + str(exc))
    return errors


def describe(case):
    rows = [r for r in case['samples'] if r[1] is False]
    by = {m: [r for r in rows if r[2] == m] for m in MODES}
    result = []
    for mode in MODES:
        rs = by[mode]
        prod = [r[6] - r[3] for r in rs]
        cpu = [r[5] - r[4] for r in rs]
        consume = [r[10] - r[7] for r in rs]
        total = [a + b for a, b in zip(prod, consume)]
        base = by['plain']
        deltas = [total[k] - ((b[6]-b[3]) + (b[10]-b[7])) for k, b in enumerate(base)]
        added = statistics.median(deltas)
        savings = len(case['outputs']['plain'].encode()) - len(case['outputs'][mode].encode())
        result.append({'condition': case['condition'], 'mode': mode,
                       'receipt_schema': json.loads(case['outputs'][mode])['receipt']['schema'],
                       'wire_bytes': len(case['outputs'][mode].encode()), 'saved_bytes': savings,
                       'producer_wall_ns': [min(prod), statistics.median(prod), max(prod)],
                       'producer_cpu_ns': [min(cpu), statistics.median(cpu), max(cpu)],
                       'consumer_wall_ns': [min(consume), statistics.median(consume), max(consume)],
                       'total_wall_ns': [min(total), statistics.median(total), max(total)],
                       'paired_added_total_ns': added,
                       'conditional_crossover_bytes_per_s': savings * 1e9 / added if savings > 0 and added > 0 else None})
    return result


def main(base):
    freeze = json.loads((Path(__file__).parent / 'FREEZE.json').read_bytes())
    errors, summaries = [], []
    for rel, wanted in freeze['sources'].items():
        if digest((Path(__file__).parent / rel).read_bytes()) != wanted:
            errors.append('source:' + rel)
    for i, name in enumerate(NAMES):
        case = json.loads((base / ('case-' + str(i)) / 'case.json').read_bytes())
        exe = json.loads((base / ('execution-' + str(i) + '.json')).read_bytes())
        errors.extend(name + ':' + x for x in inspect(case, exe, freeze['inputs'][name]['sha256']))
        folder = base / ('case-' + str(i))
        if (folder / 'input.json').read_text() != case['input']:
            errors.append(name + ':input sidecar')
        journal = [json.loads(x) for x in (folder / 'journal.jsonl').read_text().splitlines()]
        if journal != case['samples']:
            errors.append(name + ':journal sidecar')
        for mode in MODES:
            if (folder / (mode + '.json')).read_text() != case['outputs'][mode]:
                errors.append(name + ':output sidecar:' + mode)
        if case['cpu'] != [freeze['cpu']]:
            errors.append(name + ':CPU affinity')
        if not errors:
            summaries.extend(describe(case))
    result = {'status': 'PASS_RAW_FIDELITY' if not errors else 'HOLD_RAW_EVIDENCE',
              'errors': errors, 'conditions': 6, 'measured_calls': 378, 'warmup_calls': 36,
              'summaries': summaries}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main(Path(sys.argv[1])))
