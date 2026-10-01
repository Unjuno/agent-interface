"""Private, input-free composition of unchanged queue/codec modules."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'vendor'))
sys.path.insert(0, str(ROOT / 'vendor/observation_tiles'))
from queue_contract import Record, reduce_candidate
from tile_transport import Encoder, Decoder, Frame


def scope(record):
    return '/'.join(record[k] for k in ('session', 'target', 'stream'))


def produce(request):
    mode = request['mode']
    if mode not in ('FIFO', 'ENCODE_THEN_SELECT', 'SELECT_THEN_ENCODE'):
        raise ValueError('mode')
    records = [x['record'] for x in request['burst']]
    selection = reduce_candidate([Record(**r) for r in records],
                                 request['now_ns'], request['max_age_ns'])
    selected = set(selection['delivered_ids'])
    encoders, encoded, messages = {}, [], []

    def encode(item):
        r, f = item['record'], item['frame']
        key = scope(r)
        e = encoders.setdefault(key, Encoder(key, 'O2', request['tile_size']))
        frame = Frame(f['width'], f['height'], f['mode'], bytes.fromhex(f['pixels']))
        wire = e.encode(frame, action_id=r['event_id'], observed_ns=r['t_ns'],
                        context=(r['session'], r['target'], r['stream']))
        result = {'event_id': r['event_id'], 'scope': key, 'wire': wire.hex()}
        encoded.append(result)
        return dict(result, kind='FRAME')

    for item in request['bootstrap']:
        messages.append(encode(item))
    for item in request['burst']:
        r = item['record']
        deliver = mode == 'FIFO' or r['event_id'] in selected
        if r['kind'] == 'FRAME':
            if mode != 'SELECT_THEN_ENCODE' or deliver:
                message = encode(item)
                if deliver:
                    messages.append(message)
        elif deliver:
            messages.append({'kind': 'CRITICAL', 'record': r})
    return {'pid': os.getpid(), 'mode': mode, 'selection': selection,
            'encoded': encoded, 'messages': messages,
            'input_authority': False, 'continuous_visual_coverage': False,
            'coverage_kind': 'all_supplied_frames' if mode == 'FIFO' else 'selected_frames'}


def consume(request):
    decoders, observations, critical = {}, [], []

    def state(d):
        return {'sequence': d.sequence, 'metadata': d.metadata,
                'pixels': None if d.frame is None else d.frame.pixels.hex()}

    for message in request['messages']:
        if message['kind'] == 'CRITICAL':
            critical.append(message['record'])
            continue
        key = message['scope']
        d = decoders.setdefault(key, Decoder(key))
        before = state(d)
        try:
            d.accept(bytes.fromhex(message['wire']))
            ok, error = True, None
        except ValueError as exc:
            ok, error = False, str(exc)
        observations.append({'event_id': message['event_id'], 'scope': key,
                             'accepted': ok, 'error': error,
                             'before': before, 'after': state(d)})
    return {'pid': os.getpid(), 'observations': observations, 'critical': critical,
            'final': {k: state(v) for k, v in decoders.items()},
            'input_authority': False, 'task_success': None}


if __name__ == '__main__':
    data = json.load(sys.stdin)
    fn = {'produce': produce, 'consume': consume}[sys.argv[1]]
    print(json.dumps(fn(data), sort_keys=True, separators=(',', ':')))
