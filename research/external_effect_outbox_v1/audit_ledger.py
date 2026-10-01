"""Recalculate effect-level metrics from the compact GitHub measurement ledger."""
import json
from collections import defaultdict
from pathlib import Path

def run(root):
    root=Path(root); data=json.loads((root/'OBSERVED_LEDGER.json').read_text())
    groups={}; seen=set()
    for raw in data['rows']:
        r=dict(zip(data['columns'],raw,strict=True))
        for key,values in data['dictionaries'].items():r[key]=values[r[key]]
        key=(r['allocation'],r['case']); assert key not in seen;seen.add(key)
        g=groups.setdefault(r['allocation']+'/'+r['arm'],dict(cases=0,orphan_effects=0,duplicate_effects=0,
            missing_after_recovery=0,terminal_absent=0))
        g['cases']+=1
        g['orphan_effects']+=r['receiver_final'] if r['local_final']==0 else 0
        g['duplicate_effects']+=max(0,r['receiver_final']-1) if r['local_final']==1 else 0
        g['missing_after_recovery']+=int(r['local_final']==1 and r['receiver_final']==0)
        g['terminal_absent']+=int(r['terminal'] is None)
    expected={'eeo-a2/inline':(50,20,0,0,30),'eeo-a2/outbox':(50,0,10,0,30),'eeo-b1/outbox':(50,0,0,0,30)}
    for key,counts in expected.items():assert tuple(groups[key].values())==counts,(key,groups[key])
    assert sum(v['cases'] for k,v in groups.items() if k.startswith('eeo-a1/'))==22
    result={'audit':'PASS','complete_cases':150,'incomplete_prefix_cases':22,'groups':groups,
            'scope':'measurement ledger only; full event/database consistency is established by audit.py on the full archive'}
    (root/'LEDGER_AUDIT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':run(Path(__file__).resolve().parent)
