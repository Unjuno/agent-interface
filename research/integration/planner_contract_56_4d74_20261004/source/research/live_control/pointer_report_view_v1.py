"""Reversible presentation of a saved caller report; never sends input.

Only exact duplicate top-level receipts/terminal are replaced with explicit
references. Unique records, errors, timings and unknown fields remain verbatim
as JSON values. This is not a token counter or a bounded output guarantee.
"""
import copy
import json
import sys
from pathlib import Path


def pack(report):
    payload = copy.deepcopy(report)
    references = {}
    exchanges = report.get('exchanges', [])
    for field in ('last_reply', 'continuation_batch', 'terminal'):
        if field not in report:
            continue
        for index, exchange in enumerate(exchanges):
            reply = exchange.get('reply')
            if not isinstance(reply, dict):
                continue
            path = ['exchanges', index, 'reply']
            candidate = reply
            if field == 'terminal':
                records = reply.get('records', [])
                if not records:
                    continue
                candidate = records[-1]
                path += ['records', len(records) - 1]
            # Serialized equality also distinguishes bool/int/float values.
            if json.dumps(report[field], sort_keys=True, allow_nan=False) == json.dumps(candidate, sort_keys=True, allow_nan=False):
                references[field] = path
                del payload[field]
                break
    return {'format': 'pointer-report-view-v1', 'payload': payload, 'references': references}


def unpack(view):
    if view['format'] != 'pointer-report-view-v1':
        raise ValueError('unsupported view')
    report = copy.deepcopy(view['payload'])
    for field, path in view['references'].items():
        if field not in ('last_reply', 'continuation_batch', 'terminal') or field in report:
            raise ValueError('invalid duplicate reference')
        value = view['payload']
        for key in path:
            value = value[key]
        report[field] = copy.deepcopy(value)
    return report


if __name__ == '__main__':
    source = json.loads(Path(sys.argv[1]).read_text())
    view = pack(source)
    assert unpack(view) == source
    print(json.dumps(view, ensure_ascii=False, allow_nan=False))
