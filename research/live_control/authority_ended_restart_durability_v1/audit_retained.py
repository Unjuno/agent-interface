from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
off=json.loads((ROOT/'offline-result.json').read_text())
assert off['schema']=='authority-ended-durable-token-state-result-v2'
assert off['hard_gate_pass'] is True and off['decision']=='RETAIN_DURABLE_TOKEN_STATE_CANDIDATE'
assert len(off['rows'])==13 and all(r['pass'] for r in off['rows'])
live=json.loads((ROOT/'live-result.json').read_text())
ev=json.loads((ROOT/'live-compact-evidence.json').read_text())
assert live['schema']=='authority-ended-live-durable-restart-v1-result' and live['seed']==994400
assert ev['formal_result']==live
rid=live['authority_end_id']
assert live['first_status']=='authority_ended' and live['post_sequence']==2 and live['current_sequence']==3
assert live['issue_process']['rc']==0 and live['issue_process']['result']['entries'][rid]=={'post_sequence':2,'status':'pending'}
assert live['restart_recover_process']['rc']==0 and live['restart_recover_process']['result']['id']==rid
assert live['duplicate_before_process']['rc']==10 and live['duplicate_before_process']['result']['status']=='duplicate'
assert live['revalidate_process']['rc']==0 and live['revalidate_process']['result']['gate']=={'status':'revalidated'}
assert live['consume_process']['rc']==0 and live['consume_process']['result']['entries'][rid]=={'post_sequence':2,'status':'consumed'}
assert live['input_before_second']==0 and live['second_input_admissions']==1 and live['total_post_first_release_input_admissions']==1
assert live['second_status']=='completed' and live['second_release']['verified'] is True and live['second_release']['keys_down']==[] and live['second_release']['buttons_down']==[]
assert live['restart_recover_after_consume']['rc']==12 and live['restart_recover_after_consume']['result']['status']=='consumed_reject'
assert live['duplicate_after_process']['rc']==10 and live['duplicate_after_process']['result']['status']=='duplicate'
assert live['load_after']['rc']==0 and live['load_after']['result']['entries']=={rid:{'post_sequence':2,'status':'consumed'}}
assert live['input_after_second_release_before_finish']==0 and live['score_agreement'] is True
first=ev['first_terminal']; rel=first['interruption']['record']; post=first['post_authority_observation']
assert first['status']=='authority_ended' and first['interruption']['intent_token']==rid
assert rel['reason']=='expired' and rel['verified'] is True and rel['keys_down']==[] and rel['buttons_down']==[]
assert post['captures']==1 and post['sequence']==2 and post['sequence_advanced'] is True and post['grants_input_authority'] is False and post['tail_program_steps_resumed']==0 and post['error'] is None and post['within_lifecycle_deadline'] is True
assert ev['durable_state']=={'schema':'authority-ended-durable-token-state-v2','entries':{rid:{'post_sequence':2,'status':'consumed'}}}
assert len(ev['post_first_release_input_admissions'])==1
second=ev['second_terminal']; assert second['status']=='completed' and second['release']['verified'] is True and second['release']['keys_down']==[] and second['release']['buttons_down']==[]
keys=('map_exit','episode_finished','player_dead','death_count','kill_count')
assert all(ev['score'][k]==ev['direct_final_sample']['payload'][k] for k in keys)
expected={'events.jsonl':'20fed76098eec378b0e4d0b4ab6e37e3695ad18a0a902e18d783bde982f2457c','owner-events.json':'908c09e76b6ea2c9df725c998da490153e907cff4c0ed3bed3e5e719c08becf9','score.json':'a395bf5e8f0dc645577c5184bd02e8ddce2409531f3f64b95cd3bab3849c26ab','scorer-samples.jsonl':'ad96428ac91b06cf3445fca84445d3e8800c36bd5b76e4d9dd602b878280481b','durable-token-state.json':'883159a0ebdbd910c72da031539ac298d95a28ba2452d2bb06c23817f64c265c'}
for k,v in expected.items(): assert ev['source_sha256'][k]==v
print('PASS retained authority-ended restart durability audit')
