import json,sys
from pathlib import Path
s=json.loads((Path(sys.argv[1])/'formal-01/summary.json').read_text())
assert s['decision']=='PASS_DUAL_LIFETIME_STALL_BACKSTOP'
assert not s['hard_failures'] and len(s['pair_results'])==5
assert all(x<0 for x in s['paired_dual_minus_guard_only_harmful_overshoot_ms'])
for p in s['pair_results']:
    g=p['GUARD_ONLY']; d=p['DUAL_LIFETIME']
    assert g['terminal_empty'] and d['terminal_empty'] and g['balanced'] and d['balanced']
    assert g['owner_verified'] and d['owner_verified']
    assert not g['app_release_before_stall_end'] and d['app_release_before_stall_end']
    assert g['release_reason']=='cancelled' and d['release_reason']=='expired'
    assert max(g['visual_error_max'],d['visual_error_max'])<0.03
print('PASS compact dual-lifetime stall transfer audit')
