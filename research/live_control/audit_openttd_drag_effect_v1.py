"""Rebuild and audit posthoc drag-region evidence for frozen OpenTTD v6."""
import hashlib
import json
from pathlib import Path

from openttd_drag_effect_v1 import build


HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/timing-envelope-openttd-l-06/fixed-astra'
REPORT = ROOT.parent / 'drag-effect-audit.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    rows = []
    for turn in (5, 9, 11):
        destination = ROOT.parent / f'drag-effect-turn-{turn}.png'
        rows.append(build(ROOT, turn, destination))
    assert [row['crop_box'] for row in rows] == [[621, 220, 725, 292]] * 3
    assert [row['before_sequence'] for row in rows] == [22, 38, 45]
    assert [row['after_sequence'] for row in rows] == [24, 40, 48]
    assert [row['crop_changed_pixels'] for row in rows] == [3628, 250, 451]
    assert [row['full_frame_changed_pixels'] for row in rows] == [152384, 143475, 174150]
    report = {
        'audit_passed': True,
        'study': 'retained OpenTTD L v6 posthoc diagnostic',
        'rows': rows,
        'interpretation': 'the first A-to-B drag has a larger local pixel effect than the two repeated same-path drags; semantic attribution comes only from the separate source-pinned observer audit',
        'scope': 'one archived episode; no live planner comparison, causal interface benefit, or general threshold claim',
        'source_sha256': {
            'builder': sha(HERE / 'openttd_drag_effect_v1.py'),
            'audit': sha(Path(__file__)),
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
