"""Recorded transport replay plus inter-phase fault controls, no live input."""
import copy
import hashlib
import json
from pathlib import Path
from phased_submit_v1 import execute

H = Path(__file__).resolve().parent
R = H / 'results/phased-replan-ink-01'
rows = json.loads((R / 'replans.json').read_text(encoding='utf-8'))
row = next(r for r in rows if 'handoff' in r)
calls = json.loads((R / 'calls.json').read_text(encoding='utf-8'))
recorded = [c['result'] for c in calls[row['calls_begin'] + 3:row['calls_end']]]
assert len(recorded) == 5
results = []


def case(name, mutate, expected, count, error=False):
    responses = copy.deepcopy(recorded)
    mutate(responses)
    sent = []

    def call(spec):
        i = len(sent)
        assert i < len(responses), 'unexpected extra transport'
        sent.append(spec)
        if error and i == count - 1:
            raise ConnectionError('synthetic lost response')
        original = recorded[i]['request']['command']
        assert all(original[k] == v for k, v in spec['command'].items())
        return responses[i]

    try:
        result = execute(call, row['proposal'], row['verdict'], row['fresh'])
    except ConnectionError:
        assert error
        result = {'reason': 'transport_exception_propagated'}
    assert result.get('reason', result.get('status')) == expected, (name, result)
    assert len(sent) == count
    results.append({'name': name, 'result': result.get('reason', result.get('status')),
                    'exchanges': count,
                    'keyboard_tail_sent': any(any(s['op'] in ('text', 'chord')
                        for s in q['command'].get('steps', [])) for q in sent)})


case('unchanged_actual_transcript', lambda r: None, 'completed', 5)
case('activation_pending', lambda r: r[0]['state'].update(pending={'unresolved': True}),
     'activation_unresolved_or_interrupted', 1)
case('activation_expired', lambda r: r[0]['state']['last_resolution']['terminal'].update(status='expired'),
     'activation_unresolved_or_interrupted', 1)
case('first_clock_pending', lambda r: r[1]['state'].update(pending={'unresolved': True}),
     'handoff_clock_unresolved', 2)
case('observation_expired', lambda r: r[2]['state']['last_resolution']['terminal'].update(status='expired'),
     'handoff_observation_unresolved_or_interrupted', 3)
case('second_clock_pending', lambda r: r[3]['state'].update(pending={'unresolved': True}),
     'handoff_clock_unresolved', 4)
case('changed_focus', lambda r: r[2]['state']['continuation']['observation'].update(input_focus_after=9999),
     'handoff_refused', 4)
case('pointer_moved', lambda r: r[2]['state']['continuation']['observation']['input_state_after'].update(pointer=[0, 0]),
     'handoff_refused', 4)
case('tail_expired', lambda r: r[4]['state']['last_resolution']['terminal'].update(status='expired'),
     'tail_unresolved_or_interrupted', 5)
case('lost_activation_reply', lambda r: None, 'transport_exception_propagated', 1, True)
case('lost_tail_reply', lambda r: None, 'transport_exception_propagated', 5, True)
out = H / 'results/phased-submit-controls-01'
out.mkdir(exist_ok=False)
(out / 'result.json').write_text(json.dumps({'scope': 'archived responses and synthetic faults, not live fault injection',
    'sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [Path(__file__), H / 'phased_submit_v1.py', R / 'calls.json', R / 'replans.json']},
    'cases': results}, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results, indent=2))
