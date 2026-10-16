"""Independent saved-SVG score for the predeclared 20px-at-118%-zoom task."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from report_pages_v2 import digest


def score(path):
    root = ET.parse(path).getroot()
    rects = root.findall('{http://www.w3.org/2000/svg}rect')
    if len(rects) != 1 or any(e.get('transform') for e in root.iter()):
        return {'success': False, 'reason': 'unsupported structure/transform; do not silently ignore'}
    actual = {k: float(rects[0].get(k)) for k in ('x', 'y', 'width', 'height')}
    checks = {'x': abs(actual['x'] - 66.95) <= 1,
              'y': abs(actual['y'] - 50) <= .1,
              'width': abs(actual['width'] - 40) <= .1,
              'height': abs(actual['height'] - 30) <= .1}
    return {'success': all(checks.values()), 'actual': actual, 'checks': checks,
            'expected': {'x': 66.95, 'y': 50, 'width': 40, 'height': 30},
            'scope': 'saved untransformed fixture rectangle geometry only; not full SVG equivalence'}


if __name__ == '__main__':
    root = Path(sys.argv[1])
    source = root / 'runtime/shape.svg'
    result = dict(score(source), svg_sha256=digest(source.read_bytes()),
                  scorer_sha256=digest(Path(__file__).read_bytes()))
    with (root / 'strict-score.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
