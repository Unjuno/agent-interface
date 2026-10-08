"""Read-only research adapter: screen coordinates refer to a named old frame."""
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cue_4316 import extract, unique_pairs

POLICIES = ('CURRENT_GEOMETRY', 'REFERENCE_GEOMETRY')
SCOPE = ('session', 'surface', 'generation', 'intent')

def refusal(reason):
    return dict(status=reason, local_roi=None, origin_used=None, extraction=None,
                grants_authority=False, task_input=False, extends_lease=False,
                verifies_effect=False)

def adapt(req, policy):
    if policy not in POLICIES:
        raise ValueError('unknown policy')
    c, current = req['cue'], req['current']
    expected = {'cue_id','session','surface','generation','intent','clock',
                'emitted_ns','screen_roi','reference_id','reference_sha256'}
    if type(c) is not dict or set(c) != expected:
        return refusal('REJECT_SCHEMA')
    if (any(type(c[k]) is not int or c[k] < 1 for k in ('surface','generation','intent'))
            or type(c['emitted_ns']) is not int or c['emitted_ns'] < 0
            or any(type(c[k]) is not str or not c[k] for k in
                   ('cue_id','session','reference_id','reference_sha256'))
            or c['clock'] != 'MONOTONIC'):
        return refusal('REJECT_SCHEMA')
    if any(c[k] != current[k] for k in SCOPE):
        return refusal('REJECT_SCOPE')
    anchors = [a for a in req['references'] if a['frame_id'] == c['reference_id']]
    if len(anchors) != 1:
        return refusal('HOLD_REFERENCE')
    anchor = anchors[0]
    if (anchor['root_rgb_sha256'] != c['reference_sha256']
            or any(anchor[k] != c[k] for k in SCOPE)
            or anchor['capture_end_ns'] > c['emitted_ns']):
        return refusal('REJECT_REFERENCE')
    r = c['screen_roi']
    if (type(r) is not list or len(r) != 4 or any(type(v) is not int for v in r)
            or r[0] < 0 or r[1] < 0 or r[2] < 1 or r[3] < 1
            or r[0]+r[2] > anchor['root_size'][0]
            or r[1]+r[3] > anchor['root_size'][1]):
        return refusal('REJECT_ROI')
    # The sole policy difference. No guessed object tracking or semantic inference.
    origin = (current if policy == 'CURRENT_GEOMETRY' else anchor)['origin']
    local_roi = [r[0]-origin[0], r[1]-origin[1], r[2], r[3]]
    inner = {k: c[k] for k in SCOPE}
    inner.update(cue_id=c['cue_id'], kind='IMPORTANT_CHANGE', clock=c['clock'],
                 emitted_ns=c['emitted_ns'], roi=local_roi)
    extracted = extract(dict(context={k:current[k] for k in SCOPE},
                             frames=copy.deepcopy(req['frames']), now_ns=req['now_ns'],
                             cues=[inner]))
    result = refusal(extracted['responses'][0]['status'])
    result.update(local_roi=local_roi, origin_used=list(origin), extraction=extracted,
                  reference_id=c['reference_id'])
    return result

if __name__ == '__main__':
    raw = sys.stdin.buffer.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError('bounded input exceeded')
    request = json.loads(raw, object_pairs_hook=unique_pairs,
                         parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    print(json.dumps(adapt(request, sys.argv[1]), sort_keys=True, separators=(',',':')), flush=True)
