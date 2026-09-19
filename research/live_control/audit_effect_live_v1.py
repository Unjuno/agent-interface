"""Audit actual false-goal receipts, rejected transport and live saved-effect checkpoint."""
import copy
import json
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace
from audit_cause_servo_v2 import frames, read
from effect_checkpoint_v1 import checkpoint
from effect_command_once_v1 import CommandOnce
from report_pages_v2 import digest
from servo_review_v1 import build
from score_drag_v1 import score

HERE = Path(__file__).resolve().parent
rows = []
for cohort in ('effect-live-01', 'effect-live-02'):
    root = HERE / 'results' / cohort
    runtime = root / 'runtime'
    for name, sha in read(root / 'initial/plan.json')['sources'].items():
        assert digest((HERE / name).read_bytes()) == sha, name
    for name, sha in read(runtime / 'sources.json').items():
        assert digest((HERE.parent / name).read_bytes()) == sha, name
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    covered, count = set(), 0
    for stage in ('initial', 'servo', 'save', 'effect', 'finish'):
        for path in sorted((root / stage).glob('query-*-request.json')):
            q, reply = read(path), read(path.with_name(path.name.replace('-request', '-reply')))
            count += 1
            if cohort == 'effect-live-01' and stage == 'effect':
                assert reply == {'status': 'error', 'error': 'ValueError', 'message': 'runtime command required'}
                assert not any(e['event'] == 'command' and e['command'].get('op') == 'effect' for e in raw)
                continue
            a, b = q['after'], reply['cursor']
            assert reply['status'] == 'boundary' and b-a == len(reply['records'])
            assert reply['records'] == raw[a:b] and not covered.intersection(range(a,b))
            covered.update(range(a,b))
            if 'command' in q:
                own = [e for e in reply['records'] if e['event'] == 'command' and e['command'].get('transport_request_id') == q['request_id']]
                assert len(own) == 1 and own[0]['command'] == dict(q['command'], transport_request_id=q['request_id'])
    assert covered == set(range(len(raw)))
    for stage in ('servo', 'save'):
        assert build((root / stage / 'report.json').read_bytes()) == read(root / stage / 'receipt.json')
    card = read(root / 'servo/receipt.json')
    assert card['format'] == 'servo-review-v1' and card['status'] == 'completed' and card['corrections'] == 0
    assert card['feedback'][0]['delta'] == [20,0] and card['task_success'].startswith('unknown')
    assert not any(e.get('continuation') for e in raw)
    assert not score(runtime / 'shape.svg')['success']
    assert score(runtime / 'shape.svg')['actual']['x'] == 50
    assert all(e['release']['verified'] and not e['release']['buttons_down'] and not e['release']['keys_down'] for e in raw if e['event'] == 'terminal')
    observed = frames(runtime, raw)
    effects = [e for e in raw if e['event'] == 'saved_effect']
    if cohort == 'effect-live-02':
        assert len(effects) == 1
        effect = effects[0]
        artifact = runtime / Path(effect['artifact']).name
        assert digest(artifact.read_bytes()) == effect['svg_sha256']
        assert effect['score'] == score(artifact) and not effect['score']['success']
        save_terminal = next(e for e in raw if e['event'] == 'terminal' and e['id'] == 'save')
        assert effect['save_terminal_ns'] == save_terminal['terminal_ns'] < effect['sampled_ns']
        effect_ns = effect['sampled_ns']
    else:
        assert effects == []
        effect_ns = None
    rows.append(dict(cohort=cohort, events=len(raw), exchanges=count, exact_frames=len(observed),
                     task_success=False, compact_card_returned=True,
                     capture_to_saved_effect_seconds=None if effect_ns is None else (effect_ns-observed[0]['capture_ns'])/1e9))

# Checkpoint guards on recorded events; no GUI trial or current-state proof.
events = copy.deepcopy(raw[:next(i for i,e in enumerate(raw) if e['event'] == 'saved_effect')])
command = {'op': 'effect', 'save_id': 'save'}
guard_cases = []
with tempfile.TemporaryDirectory() as temp:
    directory = Path(temp)
    engine = SimpleNamespace(lock=threading.RLock(), active=None)
    positive = HERE / 'results/cause-servo-live-02/runtime/shape.svg'
    assert checkpoint(engine, events, positive, directory, command)['score']['success']
    for case in ('busy', 'wrong_id', 'failed_save', 'wrong_steps', 'unknown_field'):
        altered, q = copy.deepcopy(events), dict(command)
        engine.active = ('synthetic',) if case == 'busy' else None
        if case == 'wrong_id': q['save_id'] = 'servo'
        if case == 'unknown_field': q['extra'] = True
        if case == 'failed_save':
            [e for e in altered if e['event']=='terminal'][-1]['status'] = 'needs_decision'
        if case == 'wrong_steps':
            [e['command'] for e in altered if e['event']=='command' and e['command'].get('op')=='submit'][-1]['steps'] = [{'op':'observe'}]
        try:
            checkpoint(engine, altered, positive, directory, q)
        except ValueError as exc:
            guard_cases.append(dict(case=case, reason=str(exc)))
        else:
            raise AssertionError(case)
writes=[]
sender=CommandOnce(writes.append)
assert sender.send('effect-test', command)['state']=='stdin_flushed'
assert sender.send('effect-test', command)['replayed'] and len(writes)==1
try:
    sender.send('effect-test', dict(command, save_id='other'))
except ValueError:
    pass
else:
    raise AssertionError('dedup payload conflict')
output=dict(audit_passed=True, rows=rows, checkpoint_guard_cases=guard_cases,
            positive_checkpoint='offline preserved successful SVG; not fresh GUI positive control',
            effect_dedup_one_write=True, audit_sha256=digest(Path(__file__).read_bytes()),
            limits='No live recovery, inverse post-goal tracking-loss case, token accounting or speed comparison. No full SVG equivalence or independent per-child cleanup inventory.')
with (HERE / 'results/effect-live-audit-01.json').open('x') as stream:
    json.dump(output,stream,indent=2);stream.write('\n')
print(json.dumps(output))
