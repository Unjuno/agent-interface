"""Read-only timing of retained relay host boundaries, never model latency."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(directory):
    directory = Path(directory)
    identities = {}

    def read(name):
        data = (directory / name).read_bytes()
        identities[name] = hashlib.sha256(data).hexdigest()
        return data

    events = [json.loads(line) for line in read('host-events.jsonl').splitlines()]
    require(events, 'empty timeline')
    calls = {}
    active = None
    closed = False
    previous = -1
    next_relay_id = 1
    for index, event in enumerate(events, 1):
        require(event.get('schema') == 'agent-interface/relay-host-event-v1', 'event schema')
        require(type(event.get('sequence')) is int and event['sequence'] == index, 'event sequence')
        stamp = event.get('host_monotonic_ms')
        require(type(stamp) in (int, float) and math.isfinite(stamp) and stamp >= previous,
                'nonfinite or regressing host clock')
        require(not closed, 'event after transport close')
        previous = stamp
        kind = event.get('kind')
        attempt = event.get('attempt')
        if kind == 'transport_closed':
            # A failed send/presentation may have only its start event.
            closed = True
            continue
        require(type(attempt) is int and attempt > 0, 'attempt identity')
        if kind == 'send_requested':
            require(active is None and attempt == len(calls) + 1, 'overlap or attempt order')
            require(isinstance(event.get('tool'), str), 'tool identity')
            calls[attempt] = {'attempt': attempt, 'tool': event['tool'], 'send_ms': stamp,
                              'reply_ms': None, 'presentations': [], 'reviews': []}
            active = ('send', attempt)
            continue
        require(attempt in calls, 'event without send')
        call = calls[attempt]
        if kind == 'reply_available':
            require(active == ('send', attempt) and event.get('tool') == call['tool'], 'reply order')
            request = json.loads(read(f'request-{attempt}.json'))
            reply = json.loads(read(f'reply-{attempt}.json'))
            require(type(request.get('id')) is int and request['id'] == next_relay_id and
                    request.get('tool') == call['tool'], 'request identity')
            require(type(reply.get('next_id')) is int, 'relay next ID')
            if reply.get('status') == 'refused':
                # The actual relay refuses before dispatch without an id/tool echo.
                # Local attempt numbers advance, but its protocol ID is not consumed.
                require(set(reply) == {'status', 'dispatched', 'next_id', 'error'} and
                        reply['dispatched'] is False and isinstance(reply['error'], str) and
                        reply['next_id'] == next_relay_id and event.get('relay_id') is None,
                        'invalid pre-dispatch refusal')
                call['relay_outcome'] = {'status': 'refused', 'dispatched': False,
                                         'request_id': request['id']}
            else:
                require(reply.get('status') in ('returned', 'unknown_requires_reconciliation') and
                        type(reply.get('id')) is int and reply['id'] == request['id'] == event.get('relay_id') and
                        reply.get('tool') == call['tool'] and reply['next_id'] == next_relay_id + 1,
                        'request/reply identity')
                if reply['status'] == 'unknown_requires_reconciliation':
                    call['relay_outcome'] = {'status': 'unknown_requires_reconciliation',
                                             'dispatch_outcome': 'unknown'}
                next_relay_id = reply['next_id']
            call['reply_sha256'] = identities[f'reply-{attempt}.json']
            require(event.get('reply_sha256') == call['reply_sha256'], 'reply hash')
            call['reply_ms'] = stamp
            active = None
            continue
        require(call['reply_ms'] is not None and
                event.get('reply_sha256') == call['reply_sha256'], 'unbound reply event')
        if kind == 'presentation_started':
            require(active is None, 'overlapping presentation')
            call['presentations'].append({'start_ms': stamp, 'completed_ms': None})
            active = ('present', attempt)
        elif kind == 'presentation_callbacks_completed':
            require(active == ('present', attempt), 'presentation completion without start')
            call['presentations'][-1]['completed_ms'] = stamp
            active = None
        elif kind == 'review_recorded':
            require(active is None and not call['reviews'], 'overlapping or duplicate review')
            receipt = json.loads(read(f'review-{attempt}.json'))
            require(receipt.get('schema') == 'agent-interface/primary-review-receipt-v1' and
                    all(receipt.get(k) == event.get(k) for k in
                        ('reply_sha256', 'call_id', 'source_sequence', 'task', 'phase')),
                    'review receipt identity')
            # This binds the declaration, not its semantic truth or model ingestion.
            call['reviews'].append({'recorded_ms': stamp, 'task': event.get('task'),
                                    'phase': event.get('phase'),
                                    'after_presentation': any(p['completed_ms'] is not None
                                                             for p in call['presentations'])})
        else:
            raise ValueError('unknown event kind')

    rows = list(calls.values())
    for i, row in enumerate(rows):
        reply = row['reply_ms']
        row['send_to_reply_ms'] = None if reply is None else reply - row['send_ms']
        completions = [p['completed_ms'] for p in row['presentations'] if p['completed_ms'] is not None]
        row['send_to_first_callbacks_completed_ms'] = (
            completions[0] - row['send_ms'] if completions else None)
        row['reply_to_next_send_ms'] = (
            rows[i + 1]['send_ms'] - reply if reply is not None and i + 1 < len(rows) else None)
        for review in row['reviews']:
            review['send_to_declared_review_ms'] = review['recorded_ms'] - row['send_ms']
    returned = [r for r in rows if r['reply_ms'] is not None]
    complete = closed and active is None and len(returned) == len(rows)
    return {'schema': 'agent-interface/host-timing-summary-v1',
            'scope': 'single retained host lifetime; boundaries, not model latency or semantic truth',
            'timeline_status': 'complete' if complete else 'partial',
            'transport_closed': closed, 'call_count': len(rows), 'returned_count': len(returned),
            'send_to_reply_total_ms': sum(r['send_to_reply_ms'] for r in returned),
            'first_send_to_last_reply_ms': (
                returned[-1]['reply_ms'] - rows[0]['send_ms'] if returned else None),
            'unmeasured': ['first useful model-visible feedback', 'semantic completion',
                           'isolated model wait/thinking', 'actual model tokens and cost',
                           'matched speedup and human tempo'],
            'calls': rows, 'input_sha256': identities}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transport_directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.transport_directory), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
