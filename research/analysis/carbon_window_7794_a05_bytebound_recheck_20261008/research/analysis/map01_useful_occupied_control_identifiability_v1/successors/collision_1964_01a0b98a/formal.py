import hashlib
import json
import platform
from collections import Counter
from pathlib import Path
from candidate import classify

ROOT = Path(__file__).resolve().parent
OUT = Path('/out')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def source_check():
    manifest = json.loads((ROOT / 'SOURCE_FREEZE.json').read_text())
    for name, expected in manifest.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('source mismatch: ' + name)
    return manifest

def invalid_checks():
    bad = [((2, 1, 1, 2), 1, 'ACTION'),
           ((0, 1, 2, 1), 1, 'ACTION'),
           ((2, 2, 0, 1), 1, 'ACTION'),
           ((0, True, 1, 2), 1, 'ACTION'),
           ((0, 1, 1, 2), 1.5, 'ACTION'),
           ((0, 1, 1, 2), 1, 'UNVERIFIED'),
           ((0, 1, 2), 1, 'ACTION')]
    for args in bad:
        try:
            classify(*args)
        except ValueError:
            continue
        raise AssertionError(('invalid accepted', args))
    return len(bad)

def main():
    # Exclusive marker is created BEFORE any formal corpus evaluation.
    with (OUT / 'INVOCATION.json').open('x') as f:
        json.dump({'issue': 1964, 'formal_invocations': 1,
                   'reruns': 0, 'replacements': 0, 'tuning': 0}, f)
    sources = source_check()
    effects = (None,) + tuple(range(-1, 8))
    causes = ('ACTION', 'ENVIRONMENT')
    rows, counts, lookup = [], Counter(), {}
    exact_unknown = 0
    for dl in range(7):
        for dh in range(dl, 7):
            for rl in range(7):
                for rh in range(rl, 7):
                    if dl > rh:
                        continue
                    edge = (dl, dh, rl, rh)
                    values = ''.join(classify(edge, e, c)
                                     for c in causes for e in effects)
                    lookup[edge] = values
                    rows.append([*edge, values])
                    counts.update(values)
                    if dl == dh and rl == rh:
                        exact_unknown += values.count('U')
    comparisons = 0
    for edge, values in lookup.items():
        dl, dh, rl, rh = edge
        for refined in ((dl+1, dh, rl, rh), (dl, dh-1, rl, rh),
                        (dl, dh, rl+1, rh), (dl, dh, rl, rh-1)):
            if refined not in lookup:
                continue
            for a, b in zip(values, lookup[refined]):
                comparisons += 1
                if a != 'U' and a != b:
                    raise AssertionError(('refinement reversal', edge, refined))
    invalid_count = invalid_checks()
    raw = {'effects': list(effects), 'causes': list(causes), 'rows': rows}
    (OUT / 'RAW.json').write_bytes(canonical(raw) + b'\n')
    result = {'issue': 1964, 'sources': sources, 'grid': list(range(7)),
              'edge_domains': len(rows), 'observations': sum(counts.values()),
              'counts': dict(counts), 'exact_edge_unknown': exact_unknown,
              'refinement_comparisons': comparisons,
              'invalid_rejections': invalid_count,
              'witness': {'edges': [0, 2, 2, 4], 'effect': 1,
                          'cause': 'ACTION', 'true_world': [0, 3],
                          'false_world': [2, 3]},
              'raw_sha256': hashlib.sha256((OUT / 'RAW.json').read_bytes()).hexdigest(),
              'python': platform.python_version(), 'platform': platform.platform(),
              'formal_invocations': 1, 'reruns': 0, 'replacements': 0, 'tuning': 0,
              'decision': 'CANDIDATE_COMPLETE_REQUIRES_INDEPENDENT_AUDIT'}
    (OUT / 'RESULT.json').write_bytes(canonical(result) + b'\n')
    print(json.dumps({k: result[k] for k in ('edge_domains', 'observations', 'counts',
                     'exact_edge_unknown', 'refinement_comparisons', 'decision')}))

if __name__ == '__main__':
    main()
