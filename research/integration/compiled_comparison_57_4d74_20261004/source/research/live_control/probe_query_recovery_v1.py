"""Recovery faults from actual query replies, plus shared-phase compatibility."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from append_checkpoint_v1 import load, store
from durable_submit_v5 import run
from form_proposal_schema_v1 import parse, validate
from phased_submit_v2 import execute
from recover_query_once_v1 import recover_query_once

H = Path(__file__).resolve().parent
R = H / 'results/query-recovery-controls-01'
R.mkdir(exist_ok=False)
S = H / 'results/checkpoint-decision-calc-01'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
calls, turns = read(S / 'calls.json'), read(S / 'turns.json')
rows = []
for case in ['matched_unknown', 'matched_verified', 'timeout', 'closed',
             'transport_error', 'unrelated_reply', 'conflicting_echo',
             'no_pending', 'wrong_pending_operation', 'wrong_expected_identity']:
    index = 8 if case == 'matched_unknown' else 16
    state = copy.deepcopy(calls[index - 1]['result']['state'])
    original = copy.deepcopy(calls[index]['result'])
    q = original['request']
    state['pending'] = {'request': q, 'write_state': 'may_have_been_sent',
                        'echo_seen': False, 'accepted': False, 'conflict': False}
    identifier = q['request_id']
    if case == 'no_pending':
        state['pending'] = None
    if case == 'wrong_pending_operation':
        state['pending']['request']['command'] = {'op': 'clock'}
    if case == 'wrong_expected_identity':
        identifier = 'other-query'
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'journal.jsonl'
        store(path, state)
        before = path.read_bytes()
        seen = []

        def fake(session, request, **kwargs):
            seen.append(copy.deepcopy(request))
            assert 'command' not in request and request['read_request_id'] == q['request_id']
            if case == 'transport_error':
                raise ConnectionError('injected read failure')
            if case in ('timeout', 'closed'):
                return {'status': case, 'cursor': request['after'], 'records': []}
            reply = copy.deepcopy(original['reply'])
            reply.pop('command_receipt')
            if case == 'unrelated_reply':
                reply['records'][-1]['transport_request_id'] = 'unrelated-query'
            if case == 'conflicting_echo':
                reply['records'][0]['command']['transport_request_id'] = 'other-command'
            return reply

        error = None
        result = None
        try:
            result = recover_query_once(path, identifier, transport=fake)
        except (ConnectionError, ValueError) as exc:
            error = {'type': type(exc).__name__, 'detail': str(exc)}
        after = load(path)
        guard_case = case in ('no_pending', 'wrong_pending_operation', 'wrong_expected_identity')
        assert len(seen) == (0 if guard_case else 1)
        if guard_case or case == 'transport_error':
            assert error and path.read_bytes() == before
        else:
            assert error is None
        if case.startswith('matched_'):
            assert after['pending'] is None
            event = after['last_resolution']['checkpoint']
            assert event['evidence']['status'] == ('UNKNOWN' if case == 'matched_unknown' else 'VERIFIED')
            assert event['task_success'] is None and event['authority'] == 'none'
        elif case != 'no_pending':
            assert after['pending'] is not None
            if case == 'conflicting_echo':
                assert after['pending']['conflict'] is True
            if case == 'closed':
                assert after['continuation']['channel_closed'] is True

            def forbidden(*args, **kwargs):
                raise AssertionError('unresolved query allowed a new command')

            try:
                run(path, {'command': {'op': 'clock'}}, forbidden)
            except ValueError as exc:
                assert str(exc) == 'unresolved command; read only'
            else:
                raise AssertionError('missing pending guard')
        rows.append({'case': case, 'read_transport_calls': len(seen), 'error': error,
                     'pending_retained': after['pending'] is not None})

replayed = 0
for row in turns:
    subset = [c['result'] for c in calls[row['calls_begin'] + 3:row['calls_end']]]
    responses, used = iter(subset), []

    def fake(spec):
        result = next(responses)
        used.append(result)
        assert all(result['request']['command'][k] == v for k, v in spec['command'].items())
        return result

    result = execute(fake, row['proposal'], row['checked'], row['fresh'])
    if 'handoff' in result:
        result['handoff']['elapsed_s'] = row['phases']['handoff']['elapsed_s']
    assert result == row['phases'] and used == subset
    replayed += 1

proposal = {'kind': 'act', 'rationale': 'Enter the declared local form value.',
            'steps': [{'op': 'pointer_click', 'x': 100, 'y': 180, 'duration_ms': 80},
                      {'op': 'text', 'text': 't000240'}, {'op': 'key', 'key': 'Return'}]}
assert parse(json.dumps(proposal), 't000240') == proposal
invalid = []
wrong = copy.deepcopy(proposal); wrong['steps'][1]['text'] = 'other'
invalid.append(('undeclared_text', wrong))
wrong = copy.deepcopy(proposal); wrong['steps'][0]['x'] = True
invalid.append(('boolean_coordinate', wrong))
wrong = copy.deepcopy(proposal); wrong['steps'][1] = {'op': 'chord', 'modifier': 'Control_L', 'key': 's'}
invalid.append(('browser_save_chord', wrong))
wrong = copy.deepcopy(proposal); wrong['steps'].append(copy.deepcopy(wrong['steps'][0]))
invalid.append(('second_pointer_in_tail', wrong))
for name, value in invalid:
    def forbidden(spec):
        raise AssertionError('invalid model proposal reached transport')
    try:
        execute(forbidden, value, {'eligible': True}, {}, validate_proposal=lambda p: validate(p, 't000240'))
    except ValueError:
        pass
    else:
        raise AssertionError(name)
try:
    parse('{"kind":"stop","kind":"stop","rationale":"x"}', 't000240')
except ValueError:
    pass
else:
    raise AssertionError('duplicate key accepted')
names = [Path(__file__), H / 'recover_query_once_v1.py', H / 'durable_submit_v5.py',
         H / 'phased_submit_v2.py', H / 'form_proposal_schema_v1.py', S / 'calls.json', S / 'turns.json']
report = {'scope': 'offline archived replies and injected transport faults; no live input',
          'recovery_controls': rows, 'default_calc_phase_replays': replayed,
          'invalid_proposals_refused_before_transport': [name for name, _ in invalid],
          'duplicate_json_key_refused': True,
          'sources': {str(p.relative_to(H)): hashlib.sha256(p.read_bytes()).hexdigest() for p in names}}
(R / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'recovery_controls': len(rows), 'legacy_phase_replays': replayed,
                  'proposal_refusals': len(invalid) + 1}))
