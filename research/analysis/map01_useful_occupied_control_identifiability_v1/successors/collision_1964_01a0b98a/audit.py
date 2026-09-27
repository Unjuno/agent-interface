"""Independent enumeration of feasible latent worlds; does not import candidate."""
import copy
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = Path('/out')

def packed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'

def reference():
    effects = [None] + list(range(-1, 8))
    rows = {}
    for bounds in itertools.product(range(7), repeat=4):
        a, b, c, d = bounds
        if a > b or c > d:
            continue
        possible = [(down, up) for down in range(a, b+1)
                    for up in range(c, d+1) if down <= up]
        if not possible:
            continue
        verdicts = []
        for cause in ('ACTION', 'ENVIRONMENT'):
            for e in effects:
                values = {cause == 'ACTION' and e is not None and down <= e < up
                          for down, up in possible}
                verdicts.append('T' if values == {True} else
                                'F' if values == {False} else 'U')
        rows[bounds] = ''.join(verdicts)
    return rows

def verify(raw, result, expected):
    if raw['effects'] != [None] + list(range(-1, 8)):
        raise ValueError('effect schedule')
    if raw['causes'] != ['ACTION', 'ENVIRONMENT']:
        raise ValueError('cause schedule')
    actual = {}
    for row in raw['rows']:
        if len(row) != 5 or any(type(v) is not int for v in row[:4]):
            raise ValueError('row shape')
        key = tuple(row[:4])
        if key in actual:
            raise ValueError('duplicate')
        actual[key] = row[4]
    if actual != expected:
        raise ValueError('corpus or verdict mismatch')
    counts = Counter(''.join(expected.values()))
    if result['counts'] != dict(counts):
        raise ValueError('counts')
    if result['observations'] != sum(counts.values()) or result['edge_domains'] != len(expected):
        raise ValueError('total')
    if result['raw_sha256'] != hashlib.sha256(packed(raw)).hexdigest():
        raise ValueError('digest')
    exact = sum(s.count('U') for (a,b,c,d), s in expected.items() if a == b and c == d)
    if exact != 0 or result['exact_edge_unknown'] != exact or counts['U'] == 0:
        raise ValueError('identifiability controls')
    comparisons = 0
    for edge, text in expected.items():
        for pos, step in enumerate((1,-1,1,-1)):
            changed = list(edge)
            changed[pos] += step
            narrowed = expected.get(tuple(changed))
            if narrowed is not None:
                comparisons += len(text)
                if any(x != 'U' and x != y for x,y in zip(text,narrowed)):
                    raise ValueError('oracle refinement reversal')
    if result['refinement_comparisons'] != comparisons:
        raise ValueError('refinement count')
    w = result['witness']
    a,b,c,d = w['edges']
    labels = []
    for key in ('true_world','false_world'):
        down, up = w[key]
        if not (a <= down <= b and c <= up <= d and down <= up):
            raise ValueError('infeasible witness')
        labels.append(w['cause'] == 'ACTION' and down <= w['effect'] < up)
    if labels != [True, False] or expected[tuple(w['edges'])][w['effect']+2] != 'U':
        raise ValueError('witness')
    if result['formal_invocations'] != 1 or any(result[k] != 0 for k in ('reruns','replacements','tuning')):
        raise ValueError('invocation accounting')

def main():
    raw = json.loads((OUT / 'RAW.json').read_text())
    result = json.loads((OUT / 'RESULT.json').read_text())
    expected = reference()
    verify(raw, result, expected)
    manifest = json.loads((ROOT / 'SOURCE_FREEZE.json').read_text())
    if result['sources'] != manifest:
        raise ValueError('source manifest differs')
    for name, digest in manifest.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('source hash differs')
    rejections = []
    for mode in ('verdict','missing','duplicate','endpoint','total','digest'):
        r, s = copy.deepcopy(raw), copy.deepcopy(result)
        if mode == 'verdict': r['rows'][0][4] = 'T' + r['rows'][0][4][1:]
        elif mode == 'missing': r['rows'].pop()
        elif mode == 'duplicate': r['rows'].append(r['rows'][0])
        elif mode == 'endpoint': r['rows'][0][0] = -1
        elif mode == 'total': s['observations'] += 1
        elif mode == 'digest': s['raw_sha256'] = '0'*64
        # Rebind non-digest mutations: rejection must be semantic, not hash-only.
        if mode != 'digest': s['raw_sha256'] = hashlib.sha256(packed(r)).hexdigest()
        try:
            verify(r, s, expected)
        except ValueError as exc:
            rejections.append({'mutation': mode, 'rejection': str(exc)})
        else:
            raise ValueError('mutation accepted: ' + mode)
    report = {'decision': 'PASS_CENSORED_USEFUL_EFFECT_MEMBERSHIP_SCOPED',
              'oracle_observations': len(expected)*20, 'mismatches': 0,
              'tamper_controls': rejections, 'independent_no_candidate_import': True,
              'result_sha256': hashlib.sha256((OUT/'RESULT.json').read_bytes()).hexdigest(),
              'raw_sha256': result['raw_sha256'], 'sources_verified': len(manifest)}
    with (OUT / 'AUDIT.json').open('xb') as f:
        f.write(packed(report))
    print(json.dumps(report))

if __name__ == '__main__':
    main()
