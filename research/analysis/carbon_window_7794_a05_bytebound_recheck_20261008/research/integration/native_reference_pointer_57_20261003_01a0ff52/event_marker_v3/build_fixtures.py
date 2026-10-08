"""Prospective parsed-JSON marker/location controls; no runtime import."""
from copy import deepcopy
import json
from pathlib import Path

VALUES = [False, True, 0, 1, 0.0, 1.0, -0.0, None, '0', '1', [], {}, [0], {'x': 0}]


def projected(number, marker, path):
    value = {'event_ref': marker}
    return {'schema': 'agent-interface/receipt-view-v2-event-refs',
            'events': [{'kind': 'zero'}, {'kind': 'one'}],
            'report': value if path == '/report' else {'value': value},
            'event_references': {path: number}, 'reference_scope': 'local'}


def fixtures():
    rows = []
    for number in (0, 1):
        for location, path in enumerate(('/report/value', '/report')):
            for token, marker in enumerate(VALUES):
                rows.append({'id': f'decode.{number}.{location}.{token}', 'mode': 'decode',
                             'input': projected(number, marker, path)})
    for token, marker in enumerate(VALUES):
        value = projected(0, marker, '/report/value')
        value['event_references'] = {}
        rows.append({'id': f'literal.{token}', 'mode': 'literal', 'input': value})
    events = [{'event_ref': False}, {'event_ref': 0}, {'event_ref': 0.0}]
    rows.append({'id': 'roundtrip.marker-types', 'mode': 'roundtrip',
                 'input': {'schema': 'agent-interface/receipt-view-v1', 'events': events,
                           'report': {'rows': deepcopy(events)}}})
    event = {'kind': 'escaped-key', 'payload': [1, True, 1.0]}
    rows.append({'id': 'roundtrip.escaped-keys', 'mode': 'roundtrip',
                 'input': {'schema': 'agent-interface/receipt-view-v1', 'events': [event],
                           'report': {'a/b': {'c~d': deepcopy(event)}}}})
    return rows


if __name__ == '__main__':
    path = Path(__file__).with_name('fixtures.json')
    if path.exists():
        raise SystemExit('prospective fixture path already exists')
    path.write_text(json.dumps(fixtures(), indent=2, sort_keys=True, allow_nan=False) + '\n')
