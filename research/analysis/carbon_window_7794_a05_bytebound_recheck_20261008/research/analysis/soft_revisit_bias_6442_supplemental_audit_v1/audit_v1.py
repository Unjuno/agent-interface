"""Independent exact-transcript audit for the frozen #6442 A03 schedule only.

No candidate, legacy auditor, policy or fixture imports. This does not evaluate
new hierarchy schedules or authorize actions, formal reruns or runtime use.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

POLICIES = ('stateless', 'hard', 'soft', 'exhaustive')
STRATA = (('stable', 8), ('partial', 8), ('revision', 8), ('no_target', 4), ('unsafe', 4))
MAX_BYTES = 1024 * 1024


def expected_row(fixture_id, policy):
    kind = fixture_id.rsplit('-', 1)[0]
    visits = Counter()
    events, labels, target = [], [], None
    while len(events) < 12:
        events.append({'type': 'observe', 'node': 'root', 'source_epoch': 1})
        if policy in ('hard', 'exhaustive'):
            eligible = [edge for edge in ('alpha', 'beta')
                        if not visits[edge] and not (kind == 'unsafe' and edge == 'alpha')]
            edge = eligible[0] if eligible else None
        elif policy == 'stateless':
            edge = 'beta' if kind == 'unsafe' else 'alpha'
        else:
            alpha_cap = 2 if kind in ('partial', 'revision') else 1
            beta_cap = 2 if kind in ('partial', 'revision') else 1
            edge = ('alpha' if kind != 'unsafe' and visits['alpha'] < alpha_cap
                    else 'beta' if visits['beta'] < beta_cap else None)
        if edge is None:
            events.append({'type': 'refuse', 'reason': 'no_safe_unvisited_edge'})
            break
        visits[edge] += 1
        events.append({'type': 'navigate', 'edge_id': edge})
        if edge == 'beta':
            label = 'Help'
        elif kind == 'stable' or kind in ('partial', 'revision') and visits[edge] >= 2:
            label = 'Profile'
        else:
            label = None
        events.append({'type': 'observe_child', 'edge_id': edge, 'label': label})
        if label is not None:
            labels.append(label)
        if label == 'Profile':
            target = label
            break
        events.append({'type': 'backtrack', 'edge_id': edge})
    return {'fixture_id': fixture_id, 'policy': policy, 'events': events,
            'observed_labels': labels, 'claimed_target': target,
            'event_count': len(events), 'budget': 12}


def audit_rows(rows):
    expected_pairs = {(f'{kind}-{i:02d}', policy) for kind, count in STRATA
                      for i in range(count) for policy in POLICIES}
    errors, seen = [], set()
    successes = {policy: {'stable': 0, 'partial_revision': 0} for policy in POLICIES}
    if type(rows) is not list:
        return {'rows': 0, 'errors': ['rows must be a list'], 'successes': successes, 'decision': 'HOLD'}
    for index, row in enumerate(rows):
        if type(row) is not dict:
            errors.append(f'row {index}: expected object')
            continue
        fixture_id, policy = row.get('fixture_id'), row.get('policy')
        if type(fixture_id) is not str or type(policy) is not str:
            errors.append(f'row {index}: invalid pair identity')
            continue
        pair = fixture_id, policy
        if pair not in expected_pairs or pair in seen:
            errors.append(f'row {index}: unknown or duplicate pair {pair}')
            continue
        seen.add(pair)
        expected = expected_row(fixture_id, policy)
        # JSON representation preserves int/float/bool distinctions that Python
        # dict equality loses (True == 1 and 12.0 == 12). No normalization of raw.
        try:
            actual_text = json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False)
            expected_text = json.dumps(expected, sort_keys=True, separators=(',', ':'), allow_nan=False)
        except (TypeError, ValueError):
            errors.append(f'row {index}: invalid JSON value')
            continue
        if actual_text != expected_text:
            errors.append(f'row {index}: frozen transcript/budget/schema mismatch {pair}')
            continue
        if expected['claimed_target']:
            kind = fixture_id.rsplit('-', 1)[0]
            stratum = 'partial_revision' if kind in ('partial', 'revision') else 'stable'
            successes[policy][stratum] += 1
    if seen != expected_pairs or len(rows) != 128:
        errors.append('expected exactly all 128 distinct frozen pairs')
    return {'rows': len(rows), 'errors': errors, 'successes': successes,
            'decision': 'HOLD' if errors else 'PASS_RETAINED_TRANSCRIPT_SCOPED'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.input.resolve() == args.output.resolve():
        parser.error('output must be a new path, distinct from immutable input')
    with args.input.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        result = {'rows': 0, 'errors': ['input exceeds 1 MiB bound'], 'decision': 'HOLD'}
    else:
        try:
            rows = [json.loads(line, object_pairs_hook=unique_object) for line in data.splitlines()]
            result = audit_rows(rows)
        except (ValueError, UnicodeError):
            result = {'rows': 0, 'errors': ['invalid JSONL input'], 'decision': 'HOLD'}
    if len(data) > MAX_BYTES:
        result.update(input_sha256=None, input_prefix_sha256=hashlib.sha256(data).hexdigest())
    else:
        result.update(input_sha256=hashlib.sha256(data).hexdigest())
    result['auditor_version'] = '6442-supplemental-v1'
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'rows': result['rows'], 'decision': result['decision'], 'errors': len(result['errors'])}))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
