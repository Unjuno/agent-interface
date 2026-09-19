"""Excluded directed toy cases only; no formal schedule execution."""
from candidate import classify
assert classify((0,0,2,2), 1, 'ACTION') == 'T'
assert classify((0,0,2,2), 2, 'ACTION') == 'F'
assert classify((0,2,2,2), 1, 'ACTION') == 'U'
assert classify((0,2,2,2), 1, 'ENVIRONMENT') == 'F'
assert classify((0,2,2,2), None, 'ACTION') == 'F'
assert classify((1,1,1,1), 1, 'ACTION') == 'F'
for edges in ((2,1,1,2), (2,2,0,1)):
    try:
        classify(edges, 1, 'ACTION')
    except ValueError:
        pass
    else:
        raise AssertionError('invalid accepted')
print('PASS: 8 excluded directed toy controls; formal corpus untouched')
