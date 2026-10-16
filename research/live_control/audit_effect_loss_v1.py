"""Audit a live tracking-loss terminal with already achieved saved geometry."""
import json
from pathlib import Path
from audit_cause_servo_v2 import frames, read
from report_pages_v2 import digest
from servo_review_v1 import build
from score_drag_v1 import score

HERE = Path(__file__).resolve().parent
root = HERE / 'results/effect-live-03'
runtime = root / 'runtime'
for name, sha in read(root / 'initial/plan.json')['sources'].items():
    assert digest((HERE / name).read_bytes()) == sha, name
for name, sha in read(runtime / 'sources.json').items():
    assert digest((HERE.parent / name).read_bytes()) == sha, name
raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
covered, exchanges = set(), 0
for stage in ('initial', 'servo', 'save', 'effect', 'finish'):
    for path in sorted((root / stage).glob('query-*-request.json')):
        request, reply = read(path), read(path.with_name(path.name.replace('-request', '-reply')))
        a, b = request['after'], reply['cursor']
        assert reply['status'] == 'boundary' and b-a == len(reply['records'])
        assert reply['records'] == raw[a:b] and not covered.intersection(range(a,b))
        covered.update(range(a,b)); exchanges += 1
        if 'command' in request:
            command = dict(request['command'], transport_request_id=request['request_id'])
            assert sum(e['event']=='command' and e['command']==command for e in reply['records']) == 1
assert covered == set(range(len(raw)))
for stage in ('servo', 'save'):
    receipt = read(root / stage / 'receipt.json')
    assert build((root / stage / 'report.json').read_bytes()) == receipt
    assert receipt['program_binding'] is not None and receipt['detail_review_required']
servo = read(root / 'servo/report.json')['terminal']
assert servo['status']=='needs_decision' and servo['steps_completed']==0 and servo['interruption'] is None
feedback = [e for e in raw if e['event']=='servo_feedback']
assert [e['reason'] for e in feedback] == ['correct','lost']
assert feedback[-1]['tracking']['status']=='lost' and feedback[-1]['command']=={'op':'finish'}
continuations = [e for e in raw if e.get('continuation')]
assert len(continuations)==1 and continuations[0]['payload']=={'x':648,'y':391}
fault = read(runtime / 'environment-fault.json')
assert fault['case']=='post-correction-occlusion'
assert continuations[0]['input_ack_ns'] < fault['injected_ns'] < feedback[-1]['emit_started_ns']
lost_index = raw.index(feedback[-1])
assert not any(e['event']=='pointer_admission' for e in raw[lost_index+1:])
assert [e['command']['id'] for e in raw if e['event']=='command' and e['command'].get('op')=='submit'] == ['servo','save']
owners = read(runtime / 'owner-events.json')
for terminal in (e for e in raw if e['event']=='terminal'):
    release=terminal['release']
    assert release['verified'] and not release['buttons_down'] and not release['keys_down']
    assert release in owners
observations = frames(runtime,raw)
effect = next(e for e in raw if e['event']=='saved_effect')
artifact = runtime / Path(effect['artifact']).name
assert digest(artifact.read_bytes())==effect['svg_sha256'] and effect['score']==score(artifact)
assert effect['score']['success'] and score(runtime / 'shape.svg')==effect['score']
save = read(root / 'save/report.json')['terminal']
assert effect['save_id']==save['id'] and effect['save_terminal_ns']==save['terminal_ns'] < effect['sampled_ns']
assert raw[-1]['event']=='independent_evaluation' and raw[-1]['success']
decision = read(root / 'model-decision.json')
assert decision['decision']=='finish without additional displacement'
for key,path in [('servo_report_sha256','servo/report.json'),('effect_reply_sha256','effect/query-0-reply.json'),('saved_image_sha256','runtime/006.png')]:
    assert decision[key]==digest((root / path).read_bytes())
result = dict(audit_passed=True, audit_sha256=digest(Path(__file__).read_bytes()),
              events=len(raw), socket_exchanges=exchanges, exact_frames=len(observations),
              controller_status=servo['status'], controller_reason='lost', task_geometry=effect['score'],
              pointer_admissions_after_lost=0, model_decision=decision,
              initial_capture_to_effect_seconds=(effect['sampled_ns']-observations[0]['capture_ns'])/1e9,
              servo_terminal_to_effect_seconds=(effect['sampled_ns']-servo['terminal_ns'])/1e9,
              limits='One staged environment occlusion and model decision using an independent benchmark oracle. Not general identity/recovery policy, model latency, speed comparison, token accounting or independent process inventory.')
with (root / 'audit.json').open('x') as stream:
    json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
