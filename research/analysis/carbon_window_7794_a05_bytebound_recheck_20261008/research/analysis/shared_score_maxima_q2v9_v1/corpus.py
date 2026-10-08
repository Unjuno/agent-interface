"""Frozen exact test design. Generating inputs does not execute a policy."""
from itertools import product
import json


def cases():
    rows = []
    for coefficients in product((-1, 0, 1), repeat=6):
        for error in ([0, 0, 0], [0, 1, 0]):
            rows.append({'id': f'g{len(rows):04}', 'a': list(coefficients[:3]),
                         'b': list(coefficients[3:]), 'e': error[:], 'domain': [-1, 1]})
    directed = [
        ('common_offset', [2,1,0], [4,4,4], [0,0,0], [-1,1]),
        ('incompatible_pairs', [0,1,1], [0,1,-1], [0,0,0], [-1,1]),
        ('interior_singleton', [0,0,0], [0,1,-1], [0,0,0], [-1,1]),
        ('left_endpoint', [0,1], [0,1], [0,0], [-1,1]),
        ('right_endpoint', [0,1], [0,-1], [0,0], [-1,1]),
        ('exact_tie', [3,3,0], [2,2,2], [0,0,0], [-2,2]),
        ('independent_residual', [2,0,1], [0,0,0], [1,2,0], [-1,1]),
        ('single_candidate', [5], [-7], [2], [-2,3]),
        ('rational_crossing', ['1/3','2/3',0], ['2/3','-1/3',0], [0,0,'1/5'], ['-1/2','5/4']),
        ('point_domain', [0,1,2], [2,0,-2], [0,0,0], ['1/2','1/2']),
        ('heterogeneous_residual', [3,1,0,2], [-2,1,3,0], [0,1,2,0], [-2,1]),
        ('large_integer', [10**30,10**30+1,10**30-1], [10**30]*3, [0,0,0], [-1,1]),
    ]
    for name, a, b, e, domain in directed:
        rows.append({'id': name, 'a': a, 'b': b, 'e': e, 'domain': domain})
    if len(rows) != 1470:
        raise RuntimeError('corpus size changed')
    return rows


def encoded():
    return (json.dumps(cases(), sort_keys=True, separators=(',', ':')) + '\n').encode()


if __name__ == '__main__':
    import sys
    sys.stdout.buffer.write(encoded())
