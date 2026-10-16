"""Offline effect review of preserved GUI trials, NOT a socket-receipt adapter.

Recompute the declared fixture geometry score from saved SVG. Keep local visual
success, program completion and task effect separate, including contradictory
evidence. No controller input or lease authority is created by this review.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image
from session_v9 import Decoder

HERE = Path(__file__).resolve().parent
NS = '{http://www.w3.org/2000/svg}'
CASES = [(c, n) for c, names in (
    ('servo-occlusion-02', ('normal', 'partial', 'hidden', 'replacement')),
    ('servo-distractor-02', ('blue', 'red')),
    ('servo-distractor-03', ('blue', 'red')),
) for n in names]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_svg(path, distractor):
    """Only these two frozen, 118%-zoom fixtures; not general SVG semantics."""
    root = ET.parse(path).getroot()
    rects = root.findall(NS + 'rect')
    if any('transform' in node.attrib for node in root.iter()):
        raise ValueError('transformed fixture unsupported')
    if len(rects) != (2 if distractor else 1) or len(list(root.iter(NS + 'rect'))) != len(rects):
        raise ValueError('unexpected rectangle structure')
    target = next((r for r in rects if r.get('id') == 'target'), None) if distractor else rects[0]
    if target is None:
        raise ValueError('missing target')
    values = {k: float(target.get(k)) for k in ('x', 'y', 'width', 'height')}
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError('nonfinite geometry')
    expected = dict(y=50, width=12 if distractor else 40, height=10 if distractor else 30)
    preserved = all(abs(values[k] - v) <= 1e-6 for k, v in expected.items())
    if distractor:
        other = next((r for r in rects if r.get('id') == 'distractor'), None)
        if other is None:
            raise ValueError('missing distractor')
        preserved = preserved and all(other.get(k) == str(v) for k, v in dict(x=74, y=50, width=12, height=10).items())
    dx = (values['x'] - 50) * 1.18
    target_dx = 12 if distractor else 24
    return dict(status='passed' if abs(dx - target_dx) <= 1 and preserved else 'failed',
                saved_dx=dx, target_dx=target_dx, geometry_preserved=preserved,
                scope='declared target displacement and fixture rectangle geometry only; not full document equivalence')


def review(cohort, name):
    directory = HERE / 'results' / cohort / name
    result = json.loads((directory / 'result.json').read_text())
    events = [json.loads(line) for line in (directory / 'events.jsonl').read_text().splitlines()]
    manifest = directory.parent / 'sources.json'
    for source, expected in json.loads(manifest.read_text()).items():
        assert digest(HERE / source) == expected, source
    feedback = [e for e in events if e['event'] == 'servo_feedback']
    assert feedback == result['controller']
    terminals = [e for e in events if e['event'] == 'terminal' and e.get('id') == 'servo']
    if result['terminal']['status'] == 'rejected':
        assert not terminals
        assert not any(e.get('id') == 'servo' and e['event'] in ('accepted', 'pointer_admission') for e in events)
        release = 'not recorded for rejected servo; no admission'
    else:
        assert terminals == [result['terminal']]
        release = terminals[0]['release']
        assert release['verified'] and not release['buttons_down'] and not release['keys_down']
    decoder = Decoder('live-control')
    frames = 0
    for event in events:
        if event['event'] != 'observation':
            continue
        frames += 1
        assert event['sequence'] == frames
        frame = decoder.accept((directory / f'{frames:03d}.ait').read_bytes())
        with Image.open(directory / Path(event['image']).name) as image:
            assert image.size == (frame.width, frame.height) and image.tobytes() == frame.pixels
    effect = score_svg(directory / 'shape.svg', 'distractor' in cohort)
    dx_key = 'target_dx' if 'distractor' in cohort else 'saved_dx'
    assert abs(effect['saved_dx'] - result[dx_key]) < 1e-9
    assert (abs(effect['saved_dx'] - effect['target_dx']) <= 1) == result['precision_pass']
    reason = feedback[-1]['reason'] if feedback else 'not evaluated'
    local_goal = reason == 'local_goal_reached'
    program = result['terminal']['status']
    # A stopped controller can still have achieved the scored geometry; show both.
    conflict = []
    if local_goal and effect['status'] == 'failed':
        conflict.append('visual goal contradicts saved task effect')
    if program == 'completed' and effect['status'] == 'failed':
        conflict.append('completed program did not achieve scored task')
    if program != 'completed' and effect['status'] == 'passed':
        conflict.append('scored geometry passed while controller stopped')
    return dict(case=f'{cohort}/{name}', evidence_kind='historical backend events plus saved SVG; no caller clock/socket binding',
                program_status=program, visual_reason=reason, local_visual_goal=local_goal,
                release=release, task_effect=effect, conflicts=conflict,
                detail_review_required=bool(conflict) or program != 'completed' or effect['status'] != 'passed',
                exact_frames=frames,
                evidence={n: digest(directory / n) for n in ('events.jsonl', 'result.json', 'shape.svg')},
                source_manifest_sha256=digest(manifest), authority='none; historical review, no automatic retry')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    rows = [review(*case) for case in CASES]
    by_name = {r['case']: r for r in rows}
    assert by_name['servo-occlusion-02/normal']['task_effect']['status'] == 'passed'
    false_goal = by_name['servo-occlusion-02/replacement']
    assert false_goal['local_visual_goal'] and false_goal['task_effect']['status'] == 'failed' and len(false_goal['conflicts']) == 2
    assert by_name['servo-occlusion-02/hidden']['visual_reason'] == 'lost'
    assert by_name['servo-distractor-02/red']['task_effect']['saved_dx'] < -47
    assert by_name['servo-distractor-03/red']['program_status'] == 'rejected'
    output = dict(format='servo-effect-corpus-review-v1', rows=rows,
                  reviewer_sha256=digest(Path(__file__)),
                  limits='Known-case offline evidence review. Not a live compact-card fallback test, new GUI trial, identity fix, general scoring, or performance/token measurement.')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps([dict(case=r['case'], program=r['program_status'], visual=r['visual_reason'], effect=r['task_effect']['status'], conflicts=r['conflicts'], frames=r['exact_frames']) for r in rows]))


if __name__ == '__main__':
    main()
