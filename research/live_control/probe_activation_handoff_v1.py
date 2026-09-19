"""Replay an actual activation plus adversarially changed handoff records."""
import copy
import hashlib
import json
from pathlib import Path
from activation_handoff_v1 import evaluate

H = Path(__file__).resolve().parent
path = H / 'results/ready-replan-ink-01/replans.json'
row = json.loads(path.read_text(encoding='utf-8'))[0]
terminal = row['result']['state']['last_resolution']['terminal']
check = row['readiness']['result']['checks'][0]
base = dict(action_id=terminal['id'],
            activation_steps=row['proposal']['steps'] + [{'op': 'observe'}],
            terminal=terminal, source=row['fresh'],
            fresh=check['fresh'], clock=check['clock'])
cases = []


def case(name, modify, expected):
    args = copy.deepcopy(base)
    modify(args)
    result = evaluate(**args)
    assert result.get('reason', 'eligible') == expected, (name, result)
    cases.append({'name': name, 'result': result})


case('archived_click_and_post_terminal_sample', lambda a: None, 'eligible')
for status in ['expired', 'cancelled', 'needs_decision', 'failed']:
    case(status, lambda a, s=status: a['terminal'].update(status=s),
         'activation_not_completed')
case('wrong_action', lambda a: a.update(action_id='unrelated'), 'activation_not_completed')
case('partial', lambda a: a['terminal'].update(steps_completed=1),
     'activation_partial_or_interrupted')
case('failed_release', lambda a: a['terminal']['release'].update(verified=False),
     'release_not_verified')
case('capture_before_release', lambda a: a['fresh'].update(
    capture_ns=a['terminal']['release']['verified_ns'] - 1), 'not_post_terminal_observation')
case('expired_sample', lambda a: a['clock'].update(
    runtime_ns=a['fresh']['capture_ns'] + 1_000_000_000), 'observation_expired')
case('newer_clock_sequence', lambda a: a['clock'].update(sequence=9999), 'sequence_mismatch')
case('changed_binding', lambda a: a['fresh']['pointer_binding'].update(focus=9999),
     'binding_changed_or_missing')
case('focus_changed_after_capture', lambda a: a['fresh'].update(input_focus_after=9999),
     'focus_or_context_changed')
case('held_input', lambda a: a['fresh']['input_state_after'].update(owned_keycodes=[50]),
     'input_not_idle')
case('pointer_moved', lambda a: a['fresh']['input_state_after'].update(pointer=[0, 0]),
     'pointer_moved')
out = H / 'results/activation-handoff-controls-01'
out.mkdir(exist_ok=False)
(out / 'result.json').write_text(json.dumps({
    'scope': 'one archived actual activation; mutated-record refusal controls; no new live input',
    'sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [path, Path(__file__), H / 'activation_handoff_v1.py']},
    'cases': cases}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'cases': len(cases), 'passed': True}))
