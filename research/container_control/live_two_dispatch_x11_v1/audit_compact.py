import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'formal-01/result.json').read_text())
assert r['schema']=='live-two-dispatch-x11-v1-result' and r['passed'] is True
assert r['fresh_pass']==3 and r['stale_pass']==3
assert r['right_down_fresh']==3 and r['right_down_stale']==0
assert r['max_visual_error']<0.03
assert r['min_fresh_exact_effect_delta']>0.015
for pair in r['pairs']:
    for a in pair:
        assert a['first_release_reason']=='expired' and a['first_release_verified'] is True
        assert a['final_owned_keycodes']==[] and a['app_terminal_empty'] is True and a['passed'] is True
        if a['condition']=='FRESH':
            assert a['caller_outcome']=='TASK_SUCCEEDED' and a['right_down_count']==1
            assert a['calls']==['reuse_revalidate','final_revalidate','execute','verify_effect']
        else:
            assert a['caller_outcome']=='SAFE_STOP' and a['caller_reason']=='stale' and a['right_down_count']==0
            assert a['calls']==['reuse_revalidate']
print('PASS compact live two-dispatch X11 audit')
