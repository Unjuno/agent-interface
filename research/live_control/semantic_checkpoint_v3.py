"""Semantic-effect checkpoint with one typed, task-state-preserving view method."""
import json

from openttd_proposal_schema_v5 import parse as parse_steps

CHECKPOINT_FIELDS = {'prior_turn', 'status', 'evidence'}
STATUSES = {'observed', 'contradicted', 'uncertain'}
INTENTS = {'progress', 'inspect', 'repair'}
MUTATING_STEPS = {'pointer_click', 'pointer_drag'}
VIEW_METHODS = {'openttd.transparent_trees'}


def checkpoint(value, required_turn):
    if required_turn is None:
        if value is not None:
            raise ValueError('checkpoint must be null without a pending effect')
        return
    if (type(value) is not dict or set(value) != CHECKPOINT_FIELDS
            or type(value.get('prior_turn')) is not int
            or value['prior_turn'] != required_turn
            or value.get('status') not in STATUSES
            or type(value.get('evidence')) is not str
            or not 1 <= len(value['evidence']) <= 400):
        raise ValueError('exact checkpoint for pending effect required')


def parse(text, required_turn=None):
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError('one JSON object required') from exc
    if type(value) is not dict or value.get('kind') not in ('act', 'view', 'verify', 'stop'):
        raise ValueError('act, view, verify or stop required')
    if value['kind'] == 'act':
        if (set(value) != {'kind', 'steps', 'rationale', 'intent', 'expected_effect', 'checkpoint'}
                or value.get('intent') not in INTENTS
                or type(value.get('expected_effect')) is not str
                or not 1 <= len(value['expected_effect']) <= 300):
            raise ValueError('exact checkpointed act fields required')
        parse_steps(json.dumps({key: value[key] for key in ('kind', 'steps', 'rationale')}))
        checkpoint(value['checkpoint'], required_turn)
        status = value['checkpoint']['status'] if required_turn is not None else None
        mutating = any(step['op'] in MUTATING_STEPS for step in value['steps'])
        if value['intent'] == 'inspect' and mutating:
            raise ValueError('inspect cannot mutate')
        if status == 'uncertain' and (value['intent'] != 'inspect' or mutating):
            raise ValueError('uncertain effect permits inspection or a typed view method only')
        if status == 'contradicted' and value['intent'] != 'repair':
            raise ValueError('contradicted effect requires repair or stop')
        if value['intent'] == 'repair' and status != 'contradicted':
            raise ValueError('repair requires contradicted checkpoint')
    elif value['kind'] == 'view':
        if set(value) != {'kind', 'method', 'rationale', 'checkpoint'}:
            raise ValueError('exact typed view fields required')
        if value.get('method') not in VIEW_METHODS:
            raise ValueError('unsupported typed view method')
        checkpoint(value['checkpoint'], required_turn)
        if required_turn is None or value['checkpoint']['status'] != 'uncertain':
            raise ValueError('typed view requires an uncertain pending effect')
        if type(value.get('rationale')) is not str or not 1 <= len(value['rationale']) <= 600:
            raise ValueError('view rationale length')
    else:
        expected = {'kind', 'rationale', 'checkpoint'} | ({'road_visible'} if value['kind'] == 'verify' else set())
        if set(value) != expected:
            raise ValueError('exact checkpointed terminal fields required')
        parse_steps(json.dumps({key: value[key] for key in expected if key != 'checkpoint'}))
        checkpoint(value['checkpoint'], required_turn)
        if value['kind'] == 'verify' and required_turn is not None and value['checkpoint']['status'] != 'observed':
            raise ValueError('verification requires observed pending effect')
    return value


def expand_view(proposal):
    if proposal.get('kind') != 'view' or proposal.get('method') != 'openttd.transparent_trees':
        raise ValueError('supported typed view proposal required')
    return [{'op': 'chord', 'modifier': 'Control_L', 'key': '2'}]


def next_checkpoint_turn(turn, proposal):
    if proposal['kind'] == 'act' and any(step['op'] == 'pointer_drag' for step in proposal['steps']):
        return turn
    return None
