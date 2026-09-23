#!/usr/bin/env python3
import json, statistics, sys
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text()); c=p['constants']
assert p['schema']=='quiet_watch_scheduler_contention_v1_result'
assert len(p['blocks'])==c['pairs']==20
rat=[]; cm=[]
for i,b in enumerate(p['blocks']):
    assert b['pair']==i and set(b['arms'])=={'idle','contended'}
    for arm in ('idle','contended'):
        r=b['arms'][arm]; s=r['samples']; assert r['n']==len(s)==c['samples_per_block']==300
        for j,(due,wake,late) in enumerate(s):
            assert late==wake-due
            if j: assert due-s[j-1][0]==c['period_ns']
        l=[max(0,x[2]) for x in s]
        assert r['max_late_ns']==max(l)
        assert r['missed_nominal_slots']==sum(1 for x in l if x>=c['period_ns'])
    im=b['arms']['idle']['max_late_ns']; x=b['arms']['contended']['max_late_ns']; rat.append(x/max(im,1)); cm.append(x)
med=statistics.median(rat); medc=statistics.median(cm); over=sum(x>=c['threshold_max_ns'] for x in cm)
d='CONTENTION_TAIL_REPRODUCED_SCOPED' if med>=c['threshold_ratio'] and medc>=c['threshold_max_ns'] and over>=c['threshold_blocks'] else 'HOLD_CONTENTION_ATTRIBUTION'
assert abs(p['summary']['median_paired_max_lateness_ratio']-med)<1e-12
assert p['summary']['contended_median_max_lateness_ns']==medc
assert p['summary']['contended_blocks_max_ge_1ms']==over
assert p['summary']['ratios']==rat
assert p['summary']['decision']==d
print(json.dumps({'pass':True,'decision':d,'median_ratio':med,'contended_median_max_lateness_ns':medc,'over_1ms':over},indent=2))
