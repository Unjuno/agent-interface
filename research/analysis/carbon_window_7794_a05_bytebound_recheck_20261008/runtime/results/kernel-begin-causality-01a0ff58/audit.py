"""Independent raw-only oracle; imports no kernel, candidate or producer."""
import hashlib
import json
from pathlib import Path
import sys

ROOT_KEYS = {'schema', 'freeze_sha256', 'source_commit', 'python', 'platform', 'rows'}
ROW_KEYS = {'arm', 'begin_ns', 'started_ns', 'ended_ns', 'manifest_matches', 'accepted',
    'exception', 'stage_after', 'execution_present', 'request_preserved'}


def audit(data, freeze_bytes):
    errors = []
    if type(data) is not dict or set(data) != ROOT_KEYS:
        return {'disposition': 'HOLD', 'errors': ['root schema'], 'rows': 0}
    freeze = json.loads(freeze_bytes)
    if data['schema'] != 'begin-causality-v1' or data['freeze_sha256'] != hashlib.sha256(freeze_bytes).hexdigest() or data['source_commit'] != freeze['source_commit']:
        errors.append('provenance')
    if any(type(data[k]) is not str or not data[k] for k in ('python', 'platform')):
        errors.append('environment')
    if type(data['rows']) is not list:
        return {'disposition': 'HOLD', 'errors': errors + ['rows type'], 'rows': 0}
    expected = {(arm, b, s, e, m) for arm in ('baseline', 'candidate')
        for b in (1, 2, 3, 4) for s in (0, 1, 2, 3, 4, 5)
        for e in range(s, 7) for m in (False, True)}
    seen = set()
    gaps = {'baseline': 0, 'candidate': 0}
    accepted_counts = {'baseline': 0, 'candidate': 0}
    for index, row in enumerate(data['rows']):
        if type(row) is not dict or set(row) != ROW_KEYS:
            errors.append(f'row {index} schema')
            continue
        if any(type(row[k]) is not int for k in ('begin_ns', 'started_ns', 'ended_ns')) or any(type(row[k]) is not bool for k in ('manifest_matches', 'accepted', 'execution_present', 'request_preserved')) or type(row['arm']) is not str or type(row['stage_after']) is not str or (row['exception'] is not None and type(row['exception']) is not str):
            errors.append(f'row {index} type')
            continue
        key = tuple(row[k] for k in ('arm', 'begin_ns', 'started_ns', 'ended_ns', 'manifest_matches'))
        if key not in expected or key in seen:
            errors.append(f'row {index} coverage')
            continue
        seen.add(key)
        arm, begin, start, end, matching = key
        want = matching and (arm == 'baseline' or start >= begin)
        if row['accepted'] is not want or row['execution_present'] is not want or row['stage_after'] != ('executed' if want else 'authorized') or row['exception'] != (None if want else 'ContractError') or row['request_preserved'] is not True:
            errors.append(f'row {index} outcome/state')
        if row['accepted']:
            accepted_counts[arm] += 1
            if start < begin:
                gaps[arm] += 1
    if seen != expected or len(data['rows']) != 432:
        errors.append('incomplete denominator')
    return {'disposition': 'HOLD' if errors else 'PASS_SCOPED_ENGINEERING', 'errors': errors,
        'rows': len(data['rows']), 'unique_cases': len(seen), 'accepted': accepted_counts,
        'accepted_pre_begin': gaps, 'scientific_or_product_pass': False}


def main():
    root = Path(__file__).resolve().parent
    freeze_bytes = (root / 'FREEZE.json').read_bytes()
    result = audit(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')), freeze_bytes)
    mismatches = []
    for path, digest in json.loads(freeze_bytes)['files'].items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
            mismatches.append(path)
    if mismatches:
        result['errors'].append('source mismatch: ' + ', '.join(mismatches))
        result['disposition'] = 'HOLD'
    result['raw_sha256'] = hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()
    with Path(sys.argv[2]).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result))
    sys.exit(0 if not result['errors'] else 1)


if __name__ == '__main__':
    main()
