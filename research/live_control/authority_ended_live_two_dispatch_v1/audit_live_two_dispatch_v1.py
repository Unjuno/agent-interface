from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
result=json.loads((ROOT/'formal-result.json').read_text())
assert result['schema']=='authority-ended-live-two-dispatch-result-v1'
assert result['decision']=='PASS_LIVE_TWO_DISPATCH'
assert result['hard_failures']==[]

def rows(arm):
    p=ROOT/arm/'events.jsonl'
    return [json.loads(x) for x in p.read_text().splitlines()]

def scorer_ok(arm):
    root=ROOT/arm
    score=json.loads((root/'score.json').read_text())
    ss=[json.loads(x) for x in (root/'scorer-samples.jsonl').read_text().splitlines()]
    final=next(x['payload'] for x in reversed(ss) if x.get('direct_final_sample') is True)
    keys=('map_exit','episode_finished','player_dead','death_count','kill_count')
    return all(score[k]==final[k] for k in keys)

v=result['valid']; s=result['stale']
assert v['first_status']=='authority_ended' and v['post_sequence']==2 and v['current_sequence']==3
assert v['gate']=={'status':'revalidated'} and v['observe2_status']=='completed'
assert v['second_sent'] is True and v['second_status']=='completed'
assert v['second_release']['verified'] is True and v['second_release']['keys_down']==[] and v['second_release']['buttons_down']==[]
assert v['input_admissions_before_second_submit']==0 and v['second_input_admissions']==1 and v['score_agreement'] is True
assert s['first_status']=='authority_ended' and s['post_sequence']==s['current_sequence']==2
assert s['gate']=={'status':'stale'} and s['second_sent'] is False and s['second_status'] is None
assert s['input_admissions_before_second_submit']==0 and s['second_input_admissions']==0 and s['score_agreement'] is True

for arm, expect_second in [('formal-valid',True),('formal-stale',False)]:
    ev=rows(arm)
    first=next(x for x in ev if x.get('event')=='terminal' and x.get('id')=='first')
    rel=first['interruption']['record']
    assert first['status']=='authority_ended'
    assert rel['event']=='owner_release' and rel['reason']=='expired' and rel['verified'] is True
    assert rel['keys_down']==[] and rel['buttons_down']==[]
    post=first['post_authority_observation']
    assert post['captures']==1 and post['sequence_advanced'] is True and post['grants_input_authority'] is False
    assert post['tail_program_steps_resumed']==0 and post['within_lifecycle_deadline'] is True and post['error'] is None
    post_inputs=[x for x in ev if x.get('event')=='input_admission' and x.get('admitted_ns',0)>rel['verified_ns']]
    if expect_second:
        second_accept=next(x for x in ev if x.get('event')=='accepted' and x.get('id')=='second')
        assert not [x for x in post_inputs if x['admitted_ns']<second_accept['accepted_ns']]
        second=next(x for x in ev if x.get('event')=='terminal' and x.get('id')=='second')
        assert second['status']=='completed' and second['release']['verified'] is True
        assert second['release']['keys_down']==[] and second['release']['buttons_down']==[]
        assert len([x for x in post_inputs if x['admitted_ns']>=second_accept['accepted_ns']])==1
    else:
        assert not post_inputs and not any(x.get('id')=='second' for x in ev)
    assert scorer_ok(arm)

print('PASS live two-dispatch audit')
