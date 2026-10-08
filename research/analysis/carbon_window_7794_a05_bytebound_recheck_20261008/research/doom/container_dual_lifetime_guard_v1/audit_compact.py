import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'results/result.json').read_text())
assert r['valid_allocation_count']==2
assert r['decision']=='RETAIN_DUAL_LIFETIME_GUARD_PLUS_DEADLINE_AS_DEVELOPMENT_CANDIDATE'
assert r['kill_preserved_pairs']==2 and r['death_regressions']==0
for x in r['valid_allocations']:
    assert x['decision']=='PASS_SINGLE_PAIR_CANDIDATE'
    assert x['source_health_deadline']==97 and x['source_health_guard']==97
    assert x['guard_minus_deadline_ms']<0
    assert x['terminal_audit_deadline']==0 and x['terminal_audit_guard']==0
    assert x['guard_kills']>=x['deadline_kills'] and x['guard_deaths']<=x['deadline_deaths']
print('PASS compact dual-lifetime guard audit')
