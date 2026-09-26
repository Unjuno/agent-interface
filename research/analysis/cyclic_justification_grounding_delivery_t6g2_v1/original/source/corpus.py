"""Fixed complete two-root/two-claim family and separately named boundaries."""
from itertools import combinations, product
import json
from pathlib import Path


def cases():
    for row in json.loads((Path(__file__).parent.parent / 'DIRECTED.json').read_text()):
        yield row
    bodies = list(combinations(range(4), 1)) + list(combinations(range(4), 2))
    families = [(x,) for x in bodies] + list(combinations(bodies, 2))
    for gid, (left, right) in enumerate(product(families, repeat=2)):
        graph = {'root_count': 2, 'node_count': 4,
                 'rules': [[h, list(body)] for h, family in [(2, left), (3, right)] for body in family]}
        for before in range(4):
            for after in range(4):
                if after & ~before:
                    continue
                yield {'id': f'g{gid:04d}-{before}-{after}', 'family': 'exhaustive', 'graph': graph,
                       'before': [k for k in range(2) if before & (1 << k)],
                       'after': [k for k in range(2) if after & (1 << k)]}
