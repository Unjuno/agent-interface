from __future__ import annotations
import base64,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from authority_ended_bridge_v1 import AuthorityEndedNotReady
from two_dispatch_gate_v1 import open_replan_token,current_revalidation
r=json.loads((ROOT/'formal-result.json').read_text())
assert r['schema']=='authority-ended-live-delivery-race-v1-result' and r['seed']==994200
assert r['early_gate_rejected'] is True and r['early_gate_error']=='post-authority observation required'
assert r['early_post_release_input_admissions']==0 and r['input_admissions_through_terminal']==0 and r['input_admissions_before_second_submit']==0
assert r['first_terminal_status']=='authority_ended' and r['post_sequence']==2 and r['current_sequence']==3
assert r['gate']=={'status':'revalidated'} and r['observe2_status']=='completed'
assert r['second_input_admissions']==1 and r['second_status']=='completed' and r['score_agreement'] is True
assert r['second_release']['verified'] is True and r['second_release']['keys_down']==[] and r['second_release']['buttons_down']==[]
b64=(ROOT/'formal-raw-text.json.gz.b64').read_text().strip()
rawbytes=gzip.decompress(base64.b64decode(b64))
assert hashlib.sha256(rawbytes).hexdigest()=='a03c8a6818ddb27ef03f0b3521c8dfd73cd314b2580ab830993ec2425eabad92'
bundle=json.loads(rawbytes)
def text(name):
 e=bundle['files'][name]; b=e['utf8'].encode(); assert hashlib.sha256(b).hexdigest()==e['sha256']; return e['utf8']
ev=[json.loads(x) for x in text('events.jsonl').splitlines()]
early=next(x for x in ev if x.get('event')=='authority_ended' and x.get('id')=='first')
term=next(x for x in ev if x.get('event')=='terminal' and x.get('id')=='first')
rel=early['interruption']['record']
assert early['cause']=='scheduled_deadline' and early['grants_input_authority'] is False and early['tail_program_steps_resumed']==0
assert rel['reason']=='expired' and rel['verified'] is True and rel['keys_down']==[] and rel['buttons_down']==[]
er={'terminal_status':'authority_ended','steps_completed':0,'release_verified':rel['verified'],'keys_down':rel['keys_down'],'buttons_down':rel['buttons_down'],'post_release_input_admissions':0,'post_authority':None}
try: open_replan_token(er)
except AuthorityEndedNotReady as e: assert str(e)=='post-authority observation required'
else: raise AssertionError('early event incorrectly opened replan token')
post=term['post_authority_observation']
assert post['captures']==1 and post['sequence']==2 and post['sequence_advanced'] is True and post['grants_input_authority'] is False and post['tail_program_steps_resumed']==0 and post['error'] is None and post['within_lifecycle_deadline'] is True
second_accept=next(x for x in ev if x.get('event')=='accepted' and x.get('id')=='second')
assert not [x for x in ev if x.get('event')=='input_admission' and rel['verified_ns'] < x.get('admitted_ns',0) < second_accept['accepted_ns']]
obs2=next(x for x in ev if x.get('event')=='observation' and x.get('id')=='observe2')
class T: used=False; post_sequence=post['sequence']
assert obs2['sequence']>post['sequence'] and current_revalidation(T(),obs2['sequence'])=={'status':'revalidated'}
si=next(i for i,x in enumerate(ev) if x.get('event')=='step_started' and x.get('id')=='second'); ti=next(i for i,x in enumerate(ev) if x.get('event')=='terminal' and x.get('id')=='second')
assert len([x for x in ev[si:ti+1] if x.get('event')=='input_admission'])==1
second=ev[ti]; assert second['status']=='completed' and second['release']['verified'] is True and second['release']['keys_down']==[] and second['release']['buttons_down']==[]
score=json.loads(text('score.json')); samples=[json.loads(x) for x in text('scorer-samples.jsonl').splitlines()]; final=next(x['payload'] for x in reversed(samples) if x.get('direct_final_sample') is True)
keys=('map_exit','episode_finished','player_dead','death_count','kill_count'); assert all(score[k]==final[k] for k in keys)
print('PASS retained live authority-ended delivery-race audit')
