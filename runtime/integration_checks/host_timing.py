"""Read-only timing of retained relay host boundaries, never model latency."""
import argparse
import base64
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

    def image_candidate(attempt, expected_hash):
        name = f'reply-{attempt}.json'
        raw = read(name)
        require(identities[name] == expected_hash, 'image reply hash changed')
        reply = json.loads(raw)
        images = [b for b in reply.get('result', {}).get('content', []) if b.get('type') == 'image']
        if reply.get('status') != 'returned' or len(images) != 1:
            return None
        image = images[0]
        data = image.get('data')
        if image.get('mimeType') != 'image/png' or not isinstance(data, str) or len(data) > 16 * 1024 * 1024:
            return None
        try:
            decoded = base64.b64decode(data, validate=True)
        except ValueError:
            return None
        if not decoded or base64.b64encode(decoded).decode() != data:
            return None
        return {'data': data, 'mime_type': 'image/png', 'image_sha256': hashlib.sha256(decoded).hexdigest()}

    events = [json.loads(line) for line in read('host-events.jsonl').splitlines()]
    require(events, 'empty timeline')
    calls = {}
    active = None
    closed = False
    previous = -1
    next_relay_id = 1
    image_base = None
    last_presentation = None
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
            presentation = {'start_ms': stamp, 'completed_ms': None}
            if 'image_delivery' in event:
                delivery = event['image_delivery']
                require(isinstance(delivery, dict), 'image delivery object')
                if delivery.get('mode') == 'full':
                    require(delivery == {'mode': 'full'}, 'full image delivery shape')
                else:
                    require(type(delivery.get('base_attempt')) is int and
                            image_base is not None and delivery == image_base['reference'],
                            'missing or mismatched reviewed image base')
                    candidate = image_candidate(attempt, call['reply_sha256'])
                    require(candidate is not None and candidate['data'] == image_base['data'],
                            'referenced image bytes differ')
                presentation['image_delivery'] = delivery
            call['presentations'].append(presentation)
            active = ('present', attempt)
        elif kind == 'presentation_callbacks_completed':
            require(active == ('present', attempt), 'presentation completion without start')
            presentation = call['presentations'][-1]
            require(event.get('image_delivery') == presentation.get('image_delivery'),
                    'image delivery completion mismatch')
            presentation['completed_ms'] = stamp
            last_presentation = (attempt, presentation.get('image_delivery'))
            if presentation.get('image_delivery', {}).get('mode') == 'full':
                image_base = None
            active = None
        elif kind == 'review_recorded':
            require(active is None and not call['reviews'], 'overlapping or duplicate review')
            receipt = json.loads(read(f'review-{attempt}.json'))
            review_schema = receipt.get('schema')
            require(review_schema in (
                        'agent-interface/primary-review-receipt-v1',
                        'agent-interface/primary-review-receipt-v2-public-capture') and
                    all(receipt.get(k) == event.get(k) for k in
                        ('reply_sha256', 'call_id', 'source_sequence', 'task', 'phase')),
                    'review receipt identity')
            if review_schema == 'agent-interface/primary-review-receipt-v2-public-capture':
                require('source_sequence' in receipt and receipt['source_sequence'] is None and
                        'source_sequence' in event and event['source_sequence'] is None,
                        'public review cannot assert a source sequence')
            delivery_fields = {}
            if 'image_delivery' in event:
                expected = last_presentation[1] if last_presentation and last_presentation[0] == attempt else None
                require(event['image_delivery'] == expected, 'review image presentation mismatch')
                delivery_fields['image_delivery'] = expected
                if expected == {'mode': 'full'}:
                    candidate = image_candidate(attempt, call['reply_sha256'])
                    if candidate is not None:
                        require(receipt.get('images') == [{'mime_type': candidate['mime_type'],
                                                          'sha256': candidate['image_sha256']}],
                                'review image identity')
                        image_base = {'data': candidate['data'], 'reference': {
                            'mode': 'reviewed-image-reference', 'base_attempt': attempt,
                            'base_reply_sha256': call['reply_sha256'],
                            'base_review_sha256': identities[f'review-{attempt}.json'],
                            'image_sha256': candidate['image_sha256'], 'mime_type': candidate['mime_type']}}
            # This binds the declaration, not its semantic truth or model ingestion.
            call['reviews'].append({'recorded_ms': stamp, 'task': event.get('task'),
                                    'phase': event.get('phase'), **delivery_fields,
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
    partition = None
    if complete and rows:
        start, end = rows[0]['send_ms'], returned[-1]['reply_ms']
        span = end - start
        request_ms = math.fsum(r['send_to_reply_ms'] for r in returned)
        # Presentation can occur after the final reply, so clip every interval
        # to this named span. Repeated presentations count independently.
        presentation_ms = math.fsum(
            max(0, min(p['completed_ms'], end) - max(p['start_ms'], start))
            for r in rows for p in r['presentations'] if p['completed_ms'] is not None)
        other_ms = span - request_ms - presentation_ms
        require(other_ms >= -1e-6, 'overlapping timing partition')
        partition = {
            'span': 'first_send_to_last_reply',
            'total_ms': span,
            'request_outstanding_ms': request_ms,
            'presentation_callbacks_ms': presentation_ms,
            'other_host_intervals_ms': max(0, other_ms),
            'scope': 'Disjoint host-clock intervals only. Other includes orchestration, logging and caller gaps; not isolated model reasoning or wait.'}
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
            'time_partition': partition,
            'calls': rows, 'input_sha256': identities}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transport_directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.transport_directory), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
