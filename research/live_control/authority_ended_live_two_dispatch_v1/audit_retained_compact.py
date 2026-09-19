from __future__ import annotations
import base64,gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
res=json.loads((ROOT/'formal-result.json').read_text())
assert res['decision']=='PASS_LIVE_TWO_DISPATCH' and res['hard_failures']==[]
v=res['valid']; s=res['stale']
assert v['first_status']=='authority_ended' and v['post_sequence']==2 and v['current_sequence']==3
assert v['gate']=={'status':'revalidated'} and v['input_admissions_before_second_submit']==0
assert v['second_sent'] is True and v['second_input_admissions']==1 and v['second_status']=='completed'
assert v['second_release']['verified'] is True and v['second_release']['keys_down']==[] and v['second_release']['buttons_down']==[]
assert s['first_status']=='authority_ended' and s['post_sequence']==s['current_sequence']==2
assert s['gate']=={'status':'stale'} and s['second_sent'] is False and s['second_input_admissions']==0

# Reconstruct the GitHub-retained valid raw text bundle.
b64=(ROOT/'formal-valid-raw-text.json.gz.b64').read_text().strip()
valid_bundle_bytes=gzip.decompress(base64.b64decode(b64))
assert hashlib.sha256(valid_bundle_bytes).hexdigest()=='af07c99f46ac0c24bfa98d9c717f16c27f1ff6ba9ec56b7fea5c29c5cac06c1c'
valid_bundle=json.loads(valid_bundle_bytes)
def raw(name):
    entry=valid_bundle['files'][name]; data=entry['utf8'].encode()
    assert hashlib.sha256(data).hexdigest()==entry['sha256']; return entry['utf8']
ve=[json.loads(x) for x in raw('events.jsonl').splitlines()]
first=next(x for x in ve if x.get('event')=='terminal' and x.get('id')=='first')
rel=first['interruption']['record']; assert rel['reason']=='expired' and rel['verified'] is True and rel['keys_down']==[] and rel['buttons_down']==[]
second_accept=next(x for x in ve if x.get('event')=='accepted' and x.get('id')=='second')
post_inputs=[x for x in ve if x.get('event')=='input_admission' and x.get('admitted_ns',0)>rel['verified_ns']]
assert not [x for x in post_inputs if x['admitted_ns']<second_accept['accepted_ns']]
assert len([x for x in post_inputs if x['admitted_ns']>=second_accept['accepted_ns']])==1
vscore=json.loads(raw('score.json')); vsamples=[json.loads(x) for x in raw('scorer-samples.jsonl').splitlines()]
vfinal=next(x['payload'] for x in reversed(vsamples) if x.get('direct_final_sample') is True)
keys=('map_exit','episode_finished','player_dead','death_count','kill_count')
assert all(vscore[k]==vfinal[k] for k in keys)

# Stale full raw remained local; GitHub retains the exact claim-relevant extract plus source hashes.
se=json.loads((ROOT/'formal-stale-compact-evidence.json').read_text())
assert se['source_sha256']['events.jsonl']=='d3186958dab266d1487caeeab63db5c6004942925136586d6aa192aad3fe10d4'
assert se['first_terminal']['status']=='authority_ended'
srel=se['first_terminal']['interruption']['record']
assert srel['reason']=='expired' and srel['verified'] is True and srel['keys_down']==[] and srel['buttons_down']==[]
assert se['post_release_input_admissions']==[] and se['second_id_events']==[]
assert all(se['score'][k]==se['direct_final_sample']['payload'][k] for k in keys)
print('PASS retained live two-dispatch compact audit')
