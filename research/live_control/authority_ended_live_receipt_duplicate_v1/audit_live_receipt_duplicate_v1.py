from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
r=json.loads((ROOT/'formal-result.json').read_text())
assert r['schema']=='authority-ended-live-receipt-duplicate-v1-result' and r['seed']==994300
assert r['first_status']=='authority_ended'
assert r['duplicate_before_rejected'] is True and r['duplicate_before_error']=='authority_end_id already issued' and r['input_admissions_after_duplicate_before']==0
assert r['post_sequence']==2 and r['current_sequence']==3 and r['gate']=={'status':'revalidated'} and r['observe2_status']=='completed' and r['input_admissions_before_second_submit']==0
assert r['second_status']=='completed' and r['second_input_admissions']==1 and r['second_release']['verified'] is True and r['second_release']['keys_down']==[] and r['second_release']['buttons_down']==[]
assert r['duplicate_after_rejected'] is True and r['duplicate_after_error']=='authority_end_id already issued' and r['input_admissions_after_duplicate_after_before_finish']==0
assert r['total_post_first_release_input_admissions']==1 and r['third_id_events']==[] and r['score_agreement'] is True and r['ledger_issued_ids']==[r['authority_end_id']]
ev=[json.loads(x) for x in (ROOT/'formal'/'events.jsonl').read_text().splitlines()]
first=next(x for x in ev if x.get('event')=='terminal' and x.get('id')=='first'); rel=first['interruption']['record']
assert first['status']=='authority_ended' and first['interruption']['intent_token']==r['authority_end_id'] and rel['reason']=='expired' and rel['verified'] is True and rel['keys_down']==[] and rel['buttons_down']==[]
post=first['post_authority_observation']; assert post['captures']==1 and post['sequence']==2 and post['sequence_advanced'] is True and post['grants_input_authority'] is False and post['tail_program_steps_resumed']==0 and post['error'] is None and post['within_lifecycle_deadline'] is True
second_accept=next(x for x in ev if x.get('event')=='accepted' and x.get('id')=='second')
post_inputs=[x for x in ev if x.get('event')=='input_admission' and x.get('admitted_ns',0)>rel['verified_ns']]
assert not [x for x in post_inputs if x['admitted_ns']<second_accept['accepted_ns']] and len(post_inputs)==1 and not any(x.get('id')=='third' for x in ev)
second=next(x for x in ev if x.get('event')=='terminal' and x.get('id')=='second'); assert second['status']=='completed' and second['release']['verified'] is True and second['release']['keys_down']==[] and second['release']['buttons_down']==[]
score=json.loads((ROOT/'formal'/'score.json').read_text()); ss=[json.loads(x) for x in (ROOT/'formal'/'scorer-samples.jsonl').read_text().splitlines()]; final=next(x['payload'] for x in reversed(ss) if x.get('direct_final_sample') is True)
keys=('map_exit','episode_finished','player_dead','death_count','kill_count'); assert all(score[k]==final[k] for k in keys)
print('PASS live authority-ended receipt duplicate audit')
