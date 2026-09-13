"""Probe one-way, state-aware tree-view admission."""
import json
from pathlib import Path

from semantic_checkpoint_v4 import VIEW_METHOD, expand_view, parse


def refuse(value, required=None, trees='unknown'):
    try:
        parse(json.dumps(value), required, trees)
    except ValueError:
        return
    raise AssertionError('proposal should be refused')


pre = {'kind': 'view', 'method': VIEW_METHOD, 'rationale': 'Dense trees obscure the task before placement.', 'checkpoint': None}
pending = {'prior_turn': 5, 'status': 'uncertain', 'evidence': 'Trees obscure the attempted segment.'}
recover = {**pre, 'rationale': 'Reveal the pending segment without another task mutation.', 'checkpoint': pending}
assert parse(json.dumps(pre), None, 'opaque') == pre
assert parse(json.dumps(recover), 5, 'opaque') == recover
steps, state = expand_view(pre, 'opaque')
assert steps == [{'op': 'chord', 'modifier': 'Control_L', 'key': '2'}] and state == 'transparent'
refuse(pre, None, 'transparent')
refuse(pre, None, 'unknown')
refuse(recover, 5, 'transparent')
refuse({**recover, 'checkpoint': {**pending, 'status': 'observed'}}, 5, 'opaque')
refuse({**pre, 'method': 'openttd.transparent_trees'}, None, 'opaque')
report = {'probe_passed': True, 'valid_accepted': 2, 'invalid_refused': 5,
          'method': VIEW_METHOD, 'transition': 'known opaque -> transparent',
          'proactive_allowed': True, 'repeat_toggle_refused': True,
          'scope': 'schema and local expansion only; general view-state detection and fresh model efficacy untested'}
out = Path(__file__).resolve().parent / 'results/semantic-checkpoint-v4-probe.json'
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
