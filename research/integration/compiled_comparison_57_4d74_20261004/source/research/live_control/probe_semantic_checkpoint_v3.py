"""Probe admission boundaries for the typed OpenTTD view method."""
import json
from pathlib import Path

from semantic_checkpoint_v3 import expand_view, parse


def accept(value, required=None):
    return parse(json.dumps(value), required)


def refuse(value, required=None):
    try:
        accept(value, required)
    except ValueError:
        return
    raise AssertionError('proposal should be refused')


pending = {'prior_turn': 5, 'status': 'uncertain', 'evidence': 'Trees obscure the A-to-B alignment.'}
view = {'kind': 'view', 'method': 'openttd.transparent_trees', 'rationale': 'Reveal road alignment without changing task state.', 'checkpoint': pending}
assert accept(view, 5) == view
assert expand_view(view) == [{'op': 'chord', 'modifier': 'Control_L', 'key': '2'}]
assert accept({'kind': 'stop', 'rationale': 'No justified task mutation.', 'checkpoint': pending}, 5)['kind'] == 'stop'
refuse(view)
refuse({**view, 'method': 'openttd.zoom_in'}, 5)
refuse({**view, 'checkpoint': {**pending, 'status': 'observed'}}, 5)
refuse({**view, 'checkpoint': {**pending, 'prior_turn': 4}}, 5)
refuse({**view, 'extra': True}, 5)
refuse({'kind': 'act', 'steps': [{'op': 'pointer_click', 'x': 10, 'y': 10}], 'rationale': 'click', 'intent': 'inspect', 'expected_effect': 'inspect', 'checkpoint': pending}, 5)
report = {'probe_passed': True, 'accepted': 2, 'refused': 6, 'method': view['method'], 'scope': 'typed admission and local expansion only; no model or GUI task success claim'}
out = Path(__file__).resolve().parent / 'results/semantic-checkpoint-v3-probe.json'
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
