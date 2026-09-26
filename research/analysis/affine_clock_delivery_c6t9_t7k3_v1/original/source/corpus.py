"""Fixed synthetic exact-arithmetic corpus; no measurements or randomness."""
from __future__ import annotations
from itertools import combinations_with_replacement, product
from copy import deepcopy

SCOPE = {'from':'observer-clock', 'to':'deadline-clock', 'epoch':'declared-e0'}

def base():
    return {'scope':dict(SCOPE), 'expected_scope':dict(SCOPE), 'rate':['1','2'],
            'offset':['-10','0'], 'valid_s':['-20','20'],
            'samples':[{'s':'10','lo':'10','hi':'10'}],
            'release':['11','12'], 'deadline':'14'}

def records():
    rates = (['1','1'], ['1/2','3/2'], ['1','2'])
    offsets = (['-2','2'], ['0','0'], ['-20','0'])
    windows0 = tuple(combinations_with_replacement((-1,0,1), 2))
    windows1 = tuple(combinations_with_replacement((1,2,3), 2))
    releases = ((0,1),(1,2),(2,3),(-2,-1))
    deadlines = (-2,0,1,2,3,4,6)
    for i, (rate, offset, w0, w1, rel, d) in enumerate(product(
        rates, offsets, windows0, windows1, releases, deadlines
    )):
        doc = {'scope':dict(SCOPE),'expected_scope':dict(SCOPE),
               'rate':list(rate), 'offset':list(offset), 'valid_s':['-20','20'],
               'samples':[{'s':'0','lo':str(w0[0]),'hi':str(w0[1])},
                          {'s':'2','lo':str(w1[0]),'hi':str(w1[1])}],
               'release':list(map(str,rel)), 'deadline':str(d)}
        yield {'id':f'grid-{i:05d}', 'input':doc}
    directed = []
    def add(name, **changes):
        d = base();d.update(changes);directed.append({'id':'direct-'+name,'input':d})
    add('correlated_ontime')
    add('nominal_false_ontime',deadline='13')
    add('nominal_false_late',deadline='45/4')
    add('lower_equality',deadline='11')
    add('upper_equality',deadline='14')
    add('singleton_ontime',rate=['1','1'],offset=['0','0'],samples=[{'s':'0','lo':'0','hi':'0'}],release=['1','2'],deadline='2')
    add('singleton_late',rate=['1','1'],offset=['0','0'],samples=[{'s':'0','lo':'0','hi':'0'}],release=['1','2'],deadline='1')
    add('inconsistent',samples=[{'s':'0','lo':'0','hi':'0'},{'s':'0','lo':'1','hi':'1'}])
    add('empty_release',release=['1','1'])
    add('reversed_release',release=['2','1'])
    add('nonpositive_rate',rate=['0','1'])
    add('reversed_rate',rate=['2','1'])
    add('missing_samples',samples=[])
    add('foreign_epoch',scope={'from':'observer-clock','to':'deadline-clock','epoch':'other'})
    add('outside_horizon',release=['19','21'])
    add('float_rate',rate=[0.5,'2'])
    yield from directed

COUNT = 3*3*6*6*4*7 + 16
if __name__=='__main__':
    import json,sys
    for row in records():
        sys.stdout.write(json.dumps(row, sort_keys=True,separators=(',',':'))+'\n')
