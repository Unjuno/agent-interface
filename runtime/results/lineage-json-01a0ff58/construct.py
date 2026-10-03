"""Freeze a finite JSON-identity corpus before collecting any matrix results."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
BASE = '3116528f3abe0fec72cfc1b5b2b5b4b05538512e'
PATH = 'runtime/cli_v1/lineage.py'


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def fixture():
    return {
        'program': {'source': {'observation_seq': 1, 'binding_revision': 1},
                    'ops': [{'op': 'pointer_move', 'x': 1, 'y': 0}]},
        'receipt': {'receipt_id': 'synthetic-r1', 'role': 'ADMISSION_DEPENDENCY',
                    'currentness': 'CURRENT', 'point': [1, 0], 'observation_seq': 1,
                    'binding_revision': 1, 'source_receipt_id': 'synthetic-s1'},
        'sidecar': {'role': 'ADMISSION_DEPENDENCY', 'currentness': 'CURRENT',
                    'point': [1, 0], 'observation_seq': 1, 'binding_revision': 1},
        'current': {'current_observation_seq': 1, 'current_binding_revision': 1},
    }


def seal(case):
    p, r, s = (case[k] for k in ('program', 'receipt', 'sidecar'))
    r['digest'] = digest(r)
    s['program_digest'] = digest(p)
    s['evidence_receipt_digest'] = r['digest']
    s['digest'] = digest(s)


def main():
    cases = []
    locations = []
    for owner in ('sidecar', 'receipt'):
        locations += [(owner, 'point', 0), (owner, 'point', 1),
                      (owner, 'observation_seq'), (owner, 'binding_revision')]
    locations += [('program', 'source', 'observation_seq'),
                  ('program', 'source', 'binding_revision'),
                  ('program', 'ops', 0, 'x'), ('program', 'ops', 0, 'y'),
                  ('current', 'current_observation_seq'),
                  ('current', 'current_binding_revision')]
    for loc in locations:
        initial = fixture()
        cursor = initial
        for key in loc:
            cursor = cursor[key]
        values = [cursor, float(cursor), bool(cursor), cursor + 1,
                  str(cursor), None, [], {}]
        for variant, value in enumerate(values):
            case = fixture()
            target = case
            for key in loc[:-1]:
                target = target[key]
            target[loc[-1]] = value
            seal(case)
            cases.append({'id': '.'.join(map(str, loc)) + f':{variant}', 'input': case})
    control = fixture()
    control['program']['source'] = {'binding_revision': 1, 'observation_seq': 1}
    seal(control)
    cases.append({'id': 'reordered-control', 'input': control})
    for kind in ('receipt', 'sidecar', 'program'):
        case = fixture()
        seal(case)
        if kind == 'program':
            case['program']['ops'][0]['x'] = 2
        else:
            case[kind]['digest'] = '0' * 64
        cases.append({'id': f'corrupt-{kind}-digest', 'input': case})
    (ROOT / 'corpus.json').write_bytes(encode(cases) + b'\n')
    baseline = subprocess.check_output(['git', 'show', f'{BASE}:{PATH}'])
    (ROOT / 'baseline.txt').write_bytes(baseline)
    (ROOT / 'candidate.txt').write_bytes(Path(PATH).read_bytes())
    files = ['baseline.txt', 'candidate.txt', 'corpus.json', 'construct.py',
             'run_matrix.py', 'audit.py']
    freeze = {'schema': 'lineage-json-freeze-v1', 'base_sha': BASE,
              'worker': '01a0ff58-8f42-73c3-857d-35a2636e7bd3',
              'policy': 'FINAL-v5', 'case_count': len(cases),
              'scope': 'ordinary input-free engineering; canonical JSON identity only',
              'decision': 'candidate exact oracle agreement; immutable inputs; effective corruptions',
              'hashes': {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}}
    (ROOT / 'freeze.json').write_bytes(encode(freeze) + b'\n')
    print(json.dumps({'frozen': len(cases), 'hashes': freeze['hashes']}, sort_keys=True))


if __name__ == '__main__':
    main()
