"""Verify GUI-decision commitments precede recovery and independent evaluation."""
import json
from pathlib import Path
from audit_cause_servo_v2 import frames,read
from report_pages_v2 import digest
from servo_review_v1 import build
from score_drag_v1 import score

HERE=Path(__file__).resolve().parent
root=HERE/'results/gui-effect-live-01'; runtime=root/'runtime'
for name,sha in read(root/'initial/plan.json')['sources'].items():
    assert digest((HERE/name).read_bytes())==sha
for name,sha in read(runtime/'sources.json').items():
    assert digest((HERE.parent/name).read_bytes())==sha
raw=[json.loads(line) for line in (runtime/'events.jsonl').read_text().splitlines()]
covered=set(); exchanges=0
for stage in ('initial','servo','save','decide','recover','resave','decide_after','effect','finish'):
    for path in sorted((root/stage).glob('query-*-request.json')):
        q,r=read(path),read(path.with_name(path.name.replace('-request','-reply')))
        a,b=q['after'],r['cursor']
        assert r['status']=='boundary' and b-a==len(r['records']) and r['records']==raw[a:b]
        assert not covered.intersection(range(a,b))
        covered.update(range(a,b));exchanges+=1
        if 'command' in q:
            echo=dict(q['command'],transport_request_id=q['request_id'])
            assert sum(e['event']=='command' and e['command']==echo for e in r['records'])==1
assert covered==set(range(len(raw)))
owners=read(runtime/'owner-events.json')
for stage in ('servo','save','recover','resave'):
    r=read(root/stage/'report.json');receipt=read(root/stage/'receipt.json')
    assert build((root/stage/'report.json').read_bytes())==receipt
    assert r['terminal']['status']=='completed'
    release=r['terminal']['release']
    assert release['verified'] and not release['keys_down'] and not release['buttons_down'] and release in owners
history=read(root/'recover/received-history.json')
previous=read(root/'save/report.json')['last_reply']; later=read(root/'decide/result.json')
assert history['records']==previous['records']+later['records'] and history['cursor']==later['cursor']
assert history['records']==raw[history['cursor']-len(history['records']):history['cursor']]
commits=[]
for stage,previous_stage in [('decide','save'),('decide_after','resave')]:
    c=read(root/stage/'commit.json');d=read(root/c['decision_file'])
    assert digest((root/c['decision_file']).read_bytes())==c['sha256'] and d==read(root/stage/'decision.json')
    assert digest((root/previous_stage/'report.json').read_bytes())==c['previous_report_sha256']
    assert d['image_sha256']==c['image']['sha256']==digest((runtime/Path(c['image']['path']).name).read_bytes())
    matches=[(i,e) for i,e in enumerate(raw) if e['event']=='command' and e['command'].get('gui_decision_sha256')==c['sha256']]
    assert len(matches)==1
    i,e=matches[0];assert e['command']['op']=='clock'
    assert raw[i+1]['event']=='clock' and raw[i+1]['sequence']==c['image']['sequence']
    commits.append((i,e['received_ns'],d))
effect_index=next(i for i,e in enumerate(raw) if e['event']=='saved_effect')
recovery_index=next(i for i,e in enumerate(raw) if e['event']=='command' and e['command'].get('id')=='recover')
assert commits[0][0] < recovery_index < commits[1][0] < effect_index
assert not any(e['event'] in ('saved_effect','independent_evaluation') for e in raw[:commits[1][0]+1])
assert [e['command']['id'] for e in raw if e['event']=='command' and e['command'].get('op')=='submit']==['servo','save','recover','resave']
assert commits[0][2]['task_met'] is False and commits[1][2]['task_met'] is True
assert commits[0][2]['displayed_geometry']==dict(x=50,y=50,width=40,height=30)
effect=raw[effect_index];artifact=runtime/Path(effect['artifact']).name
assert digest(artifact.read_bytes())==effect['svg_sha256']
assert effect['score']==score(artifact)==score(runtime/'shape.svg') and effect['score']['success']
assert effect['save_id']=='resave' and effect['save_terminal_ns']==read(root/'resave/report.json')['terminal']['terminal_ns']
for k,v in commits[1][2]['displayed_geometry'].items():assert abs(v-effect['score']['actual'][k])<=.001
observations=frames(runtime,raw)
assert raw[-1]['event']=='independent_evaluation' and raw[-1]['success']
result=dict(audit_passed=True,audit_sha256=digest(Path(__file__).read_bytes()),events=len(raw),socket_exchanges=exchanges,
            exact_frames=len(observations),decision_hashes_precede_recovery_and_oracle=True,
            gui_predicted_success=commits[1][2]['task_met'],saved_geometry=effect['score'],
            initial_capture_to_gui_success_commit_seconds=(commits[1][1]-observations[0]['capture_ns'])/1e9,
            initial_capture_to_independent_effect_seconds=(effect['sampled_ns']-observations[0]['capture_ns'])/1e9,
            limits='One familiar-layout model GUI repair. Echo proves in-stream commitment ordering, not external authenticity or blindness to prior fixture knowledge. Not speed/token comparison, generalized recovery or complete SVG semantics.')
with (root/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
