from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
r=json.loads((ROOT/'formal-result.json').read_text())
e=json.loads((ROOT/'compact-evidence.json').read_text())
assert r['schema']=='authority-ended-live-receipt-duplicate-v1-result' and r['seed']==994300
assert r['duplicate_before_rejected'] is True and r['duplicate_before_error']=='authority_end_id already issued' and r['input_admissions_after_duplicate_before']==0
assert r['post_sequence']==2 and r['current_sequence']==3 and r['gate']=={'status':'revalidated'} and r['input_admissions_before_second_submit']==0
assert r['second_status']=='completed' and r['second_input_admissions']==1
assert r['second_release']['verified'] is True and r['second_release']['keys_down']==[] and r['second_release']['buttons_down']==[]
assert r['duplicate_after_rejected'] is True and r['duplicate_after_error']=='authority_end_id already issued' and r['input_admissions_after_duplicate_after_before_finish']==0
assert r['total_post_first_release_input_admissions']==1 and r['third_id_events']==[] and r['score_agreement'] is True and r['ledger_issued_ids']==[r['authority_end_id']]
first=e['first_terminal']; rel=first['interruption']['record']; post=first['post_authority_observation']
assert first['status']=='authority_ended' and first['interruption']['intent_token']==r['authority_end_id']
assert rel['reason']=='expired' and rel['verified'] is True and rel['keys_down']==[] and rel['buttons_down']==[]
assert post['captures']==1 and post['sequence']==2 and post['sequence_advanced'] is True and post['grants_input_authority'] is False and post['tail_program_steps_resumed']==0 and post['error'] is None and post['within_lifecycle_deadline'] is True
assert len(e['post_first_release_input_admissions'])==1 and e['third_id_events']==[]
second=e['second_terminal']; assert second['status']=='completed' and second['release']['verified'] is True and second['release']['keys_down']==[] and second['release']['buttons_down']==[]
keys=('map_exit','episode_finished','player_dead','death_count','kill_count')
assert all(e['score'][k]==e['direct_final_sample']['payload'][k] for k in keys)
assert e['formal_result']==r
expected={
 'events.jsonl':'96232e30fe21be9f118515fc2498ba7f419fc097d4515fcdfc48478390d0ce8c',
 'owner-events.json':'796bf184196954df6a4da04a602ca60f5a10a60cd2b50dff25d8d83b3bec2661',
 'score.json':'1713ab2bf315674112571f4b6fd6f91b59f0e6372e5b0c1b349dd80a567a777b',
 'scorer-samples.jsonl':'66f18f2527416927e0b340e50f9e6c5167e9bdb76c082f5ed3147d9175abcd9e'}
for k,v in expected.items(): assert e['source_sha256'][k]==v
print('PASS retained live authority-ended receipt duplicate audit')
