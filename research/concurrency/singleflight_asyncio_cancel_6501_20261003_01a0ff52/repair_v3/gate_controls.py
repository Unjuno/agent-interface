"""Exact copied gate-only witnesses; no candidate import or raw mutation."""
import copy
import json


def serialize(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def reordered_gates(raw):
    for index, row in enumerate(raw['rows']):
        if row['scenario'] not in ('cancel_first', 'cancel_last'):
            continue
        altered = copy.deepcopy(raw)
        events = altered['rows'][index]['events']
        gate = next(e for e in events if e['kind'] == 'gate_open')
        events.remove(gate)
        last_request = max(i for i, e in enumerate(events) if e['kind'] == 'cancel_request')
        events.insert(last_request + 1, gate)
        for seq, event in enumerate(events, 1):
            event['seq'] = seq
        yield index, altered
