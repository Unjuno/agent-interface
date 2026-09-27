import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'formal-01/result.json').read_text())
assert r['decision']=='PASS_MAP01_LIVE_TWO_DISPATCH' and not r['hard_failures']
assert r['fresh_pass']==3 and r['stale_pass']==3
assert r['fresh_right_admissions']==3 and r['stale_right_admissions']==0
flat=[a for p in r['pairs'] for a in p]
for a in flat:
    assert a['hard_gate_pass'] is True
    assert a['first_status']=='authority_ended'
    assert a['post_authority']['captures']==1 and a['post_authority']['sequence_advanced'] is True
    assert a['post_authority']['within_lifecycle_deadline'] is True and a['post_authority']['error'] is None
    assert a['post_authority']['grants_input_authority'] is False and a['post_authority']['tail_program_steps_resumed']==0
    assert a['owner_expiry_releases']==1 and a['owner_expiry_all_verified'] is True and a['owner_all_verified'] is True
    assert a['terminal_score_audit_exit']==0 and a['shift_input_admissions']==1
    if a['condition']=='FRESH':
        assert a['current_sequence']>a['post_sequence']
        assert a['caller_outcome']=='TASK_NOT_VERIFIED' and a['caller_reason']=='unavailable'
        assert a['calls']==['reuse_revalidate','final_revalidate','execute','verify_effect']
        assert a['right_input_admissions']==1 and a['second_terminal_status']=='completed' and a['second_terminal_release_verified'] is True
    else:
        assert a['current_sequence']==a['post_sequence']
        assert a['caller_outcome']=='SAFE_STOP' and a['caller_reason']=='stale'
        assert a['calls']==['reuse_revalidate'] and a['right_input_admissions']==0 and a['second_terminal_status'] is None
print('PASS compact real MAP01 live two-dispatch audit')
