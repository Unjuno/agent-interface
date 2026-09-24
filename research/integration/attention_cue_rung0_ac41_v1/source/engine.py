"""Rung-0 observation packaging only; this module has no native-input backend."""
import base64
import json
import sys
import time

FIELDS = {'cue_id', 'session', 'surface', 'generation', 'emitted_ns', 'roi'}
DEFAULT = [0, 0, 16, 16]
MAX_AGE_NS = 2_000_000_000


def package(request):
    current, frames, cue = request['current'], request['frames'], request['cue']
    now = time.monotonic_ns()
    reason, roi = 'NO_CUE', DEFAULT[:]
    if cue is not None:
        reason = 'ACCEPTED'
        if not isinstance(cue, dict) or set(cue) != FIELDS:
            reason = 'SCHEMA'
        elif not isinstance(cue['cue_id'], str) or not cue['cue_id']:
            reason = 'SCHEMA'
        elif any(type(cue[k]) is not int for k in ('surface', 'generation', 'emitted_ns')):
            reason = 'SCHEMA'
        elif cue['session'] != current['session']:
            reason = 'SESSION'
        elif cue['surface'] != current['surface']:
            reason = 'SURFACE'
        elif cue['generation'] != current['generation']:
            reason = 'GENERATION'
        elif not 0 <= now - cue['emitted_ns'] <= MAX_AGE_NS:
            reason = 'TIME'
        elif (not isinstance(cue['roi'], list) or len(cue['roi']) != 4
              or any(type(v) is not int for v in cue['roi'])):
            reason = 'ROI'
        else:
            x, y, w, h = cue['roi']
            if not (0 <= x and 0 <= y and 1 <= w <= 16 and 1 <= h <= 16
                    and x + w <= 64 and y + h <= 48):
                reason = 'ROI'
        if reason == 'ACCEPTED':
            roi = cue['roi'][:]
    selected = frames[-3:]
    output = []
    x, y, w, h = roi
    for frame in selected:
        if any(frame[k] != current[k] for k in ('session', 'surface', 'generation')):
            raise ValueError('untrusted frame scope')
        raw = base64.b64decode(frame['pixels_b64'], validate=True)
        if len(raw) != 64 * 48 * 4:
            raise ValueError('unexpected pixel layout')
        cropped = b''.join(raw[((y+j)*64+x)*4:((y+j)*64+x+w)*4] for j in range(h))
        output.append({'frame_id': frame['frame_id'], 'captured_ns': frame['captured_ns'],
                       'pixels_b64': base64.b64encode(cropped).decode('ascii')})
    return {'reason': reason, 'roi': roi, 'checked_ns': now, 'frames': output,
            'history': 'COMPLETE' if len(selected) == 3 else 'MISSING_HISTORY',
            'decoded_bytes': len(output)*w*h*4, 'authority_granted': False,
            'action': None, 'lease_extended': False}


if __name__ == '__main__':
    result = package(json.load(sys.stdin))
    print(json.dumps(result, sort_keys=True))
