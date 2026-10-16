"""Bounded, offline reconciliation of local received event slices.

No socket access, input submission, retry, admission inference or lease refresh.
The caller must supply slices from one trusted runtime session. Cursor/record
agreement cannot authenticate that provenance. An assembled history still needs
review before any next input decision.
"""
import argparse
import copy
import json
from pathlib import Path

MAX_BYTES = 8 * 1024 * 1024


def encoded(value):
    return json.dumps(value, sort_keys=True, allow_nan=False).encode()


def assemble(segments):
    if not isinstance(segments, list) or not 1 <= len(segments) <= 32:
        raise ValueError('1..32 received slices required')
    if len(encoded(segments)) > MAX_BYTES:
        raise ValueError('history byte capacity exceeded')
    slots, evidence = {}, []
    start = None
    frontier = None
    for index, segment in enumerate(segments):
        request, reply = segment['request'], segment['reply']
        after, cursor, records = request['after'], reply['cursor'], reply['records']
        if type(after) is not int or type(cursor) is not int or after < 0 or cursor < after:
            raise ValueError('nonnegative integer cursor interval required')
        if not isinstance(records, list) or cursor - after != len(records):
            raise ValueError('cursor length mismatch')
        if reply.get('status') not in ('boundary', 'unattributed_rejection'):
            raise ValueError('unresolved transport status retained externally; cannot assemble')
        if not all(isinstance(record, dict) for record in records):
            raise ValueError('record objects required')
        if start is None:
            start = frontier = after
        if after < start or after > frontier:
            raise ValueError('gap or history before starting cursor')
        if max(frontier, cursor) - start > 256:
            raise ValueError('history record capacity exceeded')
        for offset, record in enumerate(records, after):
            if offset in slots and encoded(slots[offset]) != encoded(record):
                raise ValueError('conflicting overlap')
            slots[offset] = copy.deepcopy(record)
        frontier = max(frontier, cursor)
        evidence.append({'slice': index, 'after': after, 'cursor': cursor,
                         'status': reply['status'], 'request': copy.deepcopy(request),
                         'reply_metadata': copy.deepcopy({k: v for k, v in reply.items() if k != 'records'})})
    return {'state': 'assembled_review_required', 'start_cursor': start,
            'review_batch': {'cursor': frontier, 'records': [slots[i] for i in range(start, frontier)]},
            'slices': evidence,
            'authority': 'none; received history only, no continuation approval, admission inference or refreshed image'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('segments', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    # Bound the read itself, including a file that grows after an initial stat.
    with args.segments.open('rb') as source:
        data = source.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('input file byte capacity exceeded')
    result = assemble(json.loads(data))
    with args.out.open('x') as target:
        target.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
