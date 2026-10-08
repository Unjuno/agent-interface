"""Audit planner v4 and bounded waits in the live partial-terminal path."""
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path

from PIL import Image

from delayed_decision_schema_v1 import parse
from planner_evidence_v4 import present


H = Path(__file__).resolve().parent
CAL = H / 'results/partial-terminal-03'
LIVE = H / 'results/partial-terminal-live-03'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_sources(root):
    plan = read(root / 'plan.json')
    for name, digest in plan['sources'].items():
        assert sha(H / Path(name.replace('\\', '/'))) == digest
    return plan


check_sources(CAL)
live_plan = check_sources(LIVE)
assert live_plan['seed'] == 248 and live_plan['deadline_ms'] == 1100

# The first v6 integration stopped before model delivery because the prior
# presenter explicitly allowed only journal revisions v4/v5.
failed = H / 'results/partial-terminal-live-02'
check_sources(failed)
assert read(failed / 'failure.json') == {
    'type': 'ValueError', 'message': 'validated durable exchange required'}
assert not (failed / 'before-return/model-1').exists()
failed_events = [json.loads(line) for line in
                 (failed / 'before-return/runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
assert any(event.get('event') == 'terminal' and event.get('status') == 'expired'
           and event.get('steps_completed') == 3 for event in failed_events)

controls_root = H / 'results/planner-evidence-controls-04'
check_sources(controls_root)
assert read(controls_root / 'result.json') == {
    'valid_revisions': 3, 'refusals': 5, 'model_calls': 0, 'gui_actions': 0}

# Preserve the two calibration failures and verify why each failed.
first = H / 'results/partial-terminal-01'
assert read(first / 'failure.json')['type'] == 'AssertionError'
first_events = [json.loads(line) for line in
                (first / 'before-return/runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
first_terminal = next(event for event in first_events if event.get('event') == 'terminal'
                      and event.get('steps_completed') == 6)
assert first_terminal['status'] == 'completed'
settle = next(event for event in first_events if event.get('event') == 'settle_result')
assert settle['reason'] == 'pixel_quiet' and settle['elapsed_ms'] < 1100

second = H / 'results/partial-terminal-02'
assert read(second / 'failure.json')['type'] == 'StopIteration'
second_events = [json.loads(line) for line in
                 (second / 'before-return/runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
assert any(event.get('event') == 'terminal' and event.get('status') == 'expired'
           and event.get('steps_completed') == 3 for event in second_events)
assert any(event.get('event') == 'independent_evaluation' and event.get('success') is False
           for event in second_events)
assert read(second / 'before-return/finish.json')['reply']['status'] == 'timeout'

# The no-model calibration establishes the causal boundary before the live calls.
cal_result = read(CAL / 'result.json')
assert cal_result == {
    'model_calls': 0,
    'episodes': [
        {'label': 'before-return', 'return_before_expiry': False,
         'steps_completed': 3, 'steps_total': 6, 'first_effect': 'UNKNOWN',
         'second_effect': 'UNKNOWN', 'independent_success': False},
        {'label': 'after-return', 'return_before_expiry': True,
         'steps_completed': 4, 'steps_total': 6, 'first_effect': 'UNKNOWN',
         'second_effect': 'VERIFIED', 'independent_success': True},
    ],
}

sys.path.insert(0, str(H.parent / 'observation_tiles'))
from tile_transport import Decoder

live_result = read(LIVE / 'result.json')
assert live_result['model_calls'] == 2
expected = {
    'before-return': {'steps': 3, 'decision': 'submit_once', 'new': 1},
    'after-return': {'steps': 4, 'decision': 'wait_and_check', 'new': 0},
}
metrics = {}
post_images = {}

for label, want in expected.items():
    root = LIVE / label
    result = read(root / 'result.json')
    assert result == next(item for item in live_result['episodes'] if item['label'] == label)
    assert result['expired_steps_completed'] == want['steps']
    assert result['expired_steps_total'] == 6
    assert result['model_decision'] == want['decision']
    assert result['new_input_submissions'] == want['new']
    assert result['independent_success'] is True

    state = read(root / 'decision-state.json')
    replay = present(
        state['unknown'], expected_request_id=state['unknown']['request_id'],
        expected_contract=state['strict']['binding']['expected_contract'],
        phase_report=state['phase'], prior_steps=state['steps'])
    assert replay == state['strict']
    terminal_view = state['strict']['execution']['programs'][0]
    assert terminal_view['terminal'] == 'expired'
    assert terminal_view['journal_format'] == 'durable-submit-v6'
    assert terminal_view['steps_completed'] == want['steps']
    assert terminal_view['steps_total'] == 6
    assert terminal_view['release_empty'] is True
    completed_prefix = state['steps'][:want['steps']]
    assert ({'op': 'key', 'key': 'Return'} in completed_prefix) is (label == 'after-return')

    prompt = (root / 'prompt.txt').read_text(encoding='utf-8')
    assert json.loads(prompt.split('Evidence: ')[1]) == state['strict']
    model_lines = (root / 'model-1/events.jsonl').read_bytes().splitlines(keepends=True)
    arrivals = [json.loads(line) for line in
                (root / 'model-1/arrivals.jsonl').read_bytes().splitlines()]
    assert len(model_lines) == len(arrivals) == 4
    for index, (line, arrival) in enumerate(zip(model_lines, arrivals)):
        assert arrival['line'] == index and arrival['bytes'] == len(line)
        assert arrival['sha256'] == hashlib.sha256(line).hexdigest()
    model_events = [json.loads(line) for line in model_lines]
    assert [event['type'] for event in model_events] == [
        'thread.started', 'turn.started', 'item.completed', 'turn.completed']
    proposal_text = model_events[2]['item']['text']
    proposal = read(root / 'proposal.json')
    goal = state['strict']['checkpoint']['contract']['expected']
    assert proposal == parse(proposal_text, goal)
    assert proposal['kind'] == want['decision']
    assert model_events[3]['usage'] == result['usage']
    assert result['usage']['input_tokens'] in (9822, 9823)
    model_plan = read(root / 'model-1/plan.json')
    image = root / 'runtime' / Path(state['post_action']['image']).name
    assert model_plan['image_sha256'] == sha(image)
    assert model_plan['runner_sha256'] == sha(H / 'model_context_runner_v1.py')
    assert model_plan['instructions_sha256'] == sha(H / 'screenshot_responder_v1.txt')
    assert model_plan['requested_model'] == 'gpt-5.6-luna'
    assert model_plan['requested_effort'] == 'low'
    assert (root / 'model-1/prompt.txt').read_text(encoding='utf-8') == prompt
    post_images[label] = image

    events = [json.loads(line) for line in
              (root / 'runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
    calls = read(root / 'calls.json')
    task_terminals = [event for event in events if event.get('event') == 'terminal']
    expired = next(event for event in task_terminals if event['status'] == 'expired')
    assert expired['steps_completed'] == want['steps']
    assert expired['release']['verified'] is True
    assert expired['release']['keys_down'] == [] and expired['release']['buttons_down'] == []
    assert expired['post_release_observation']['captures'] == 2
    assert all(event['release']['verified'] and event['release']['keys_down'] == [] and
               event['release']['buttons_down'] == [] for event in task_terminals)

    submissions = [call for call in calls
                   if call['result']['request']['command']['op'] == 'submit']
    task_submissions = [call for call in submissions
                        if call['result']['request']['command']['steps'] == state['steps']]
    assert len(task_submissions) == 1
    new_submissions = [call for call in submissions
                       if call['result']['request']['command']['steps'] != state['steps'] and
                       len(call['result']['request']['command']['steps']) == 5]
    assert len(new_submissions) == want['new']
    if label == 'before-return':
        assert new_submissions[0]['result']['state']['last_resolution']['terminal']['status'] == 'completed'
    checkpoint_calls = [call for call in calls
                        if call['result']['request']['command']['op'] == 'effect_checkpoint']
    statuses = [call['result']['state']['last_resolution']['checkpoint']['evidence']['status']
                for call in checkpoint_calls]
    assert statuses[0] == 'UNKNOWN'
    assert statuses[1:] == result['post_decision_effect_statuses']
    assert statuses[-1] == 'VERIFIED'
    assert len(statuses) == 2
    assert result['post_decision_effect_calls'] == 1
    assert result['wait_requested_ms'] == 6000
    assert result['poll_requested_ms'] == 50
    wait_command = checkpoint_calls[1]['result']['request']['command']
    assert wait_command['wait_ms'] == 6000 and wait_command['poll_ms'] == 50
    wait_evidence = checkpoint_calls[1]['result']['state']['last_resolution']['checkpoint']['evidence']
    assert wait_evidence['sample_attempts'] == result['verifier_sample_attempts']

    first_cursor = checkpoint_calls[0]['result']['reply']['cursor']
    next_cursor = checkpoint_calls[1]['result']['reply']['cursor']
    between = events[first_cursor:next_cursor]
    admissions = [event for event in between
                  if event['event'] in ('input_admission', 'pointer_admission')]
    assert (len(admissions) > 0) is (label == 'before-return')
    if label == 'after-return':
        assert len(submissions) == 2  # navigation and the original partial program

    effect_log = [json.loads(line) for line in
                  (root / 'runtime/delayed-effects.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [record['event'] for record in effect_log] == ['received', 'committed']
    verified = checkpoint_calls[-1]['result']['state']['last_resolution']['checkpoint']['evidence']
    assert urllib.parse.parse_qs((root / 'runtime/submitted.txt').read_text(encoding='utf-8')) == verified['actual']
    assert sha(root / 'runtime/submitted.txt') == verified['artifact_sha256']
    finish = read(root / 'finish.json')
    evaluation = next(record for record in finish['reply']['records']
                      if record['event'] == 'independent_evaluation')
    assert evaluation['success'] is True
    assert not Path(read(root / 'endpoint.json')['socket']).exists()

    decoder = Decoder('live-control')
    observations = [event for event in events if event.get('event') == 'observation']
    for index, event in enumerate(observations, 1):
        frame = decoder.accept((root / 'runtime' / f'{index:03d}.ait').read_bytes())
        with Image.open(root / 'runtime' / Path(event['image']).name) as captured:
            assert (captured.width, captured.height, captured.mode, captured.tobytes()) == (
                frame.width, frame.height, frame.mode, frame.pixels)

    accepted = next(event for event in events if event.get('event') == 'accepted'
                    and event.get('id') == expired['id'])
    final_checkpoint = checkpoint_calls[-1]
    metrics[label] = {
        'events': len(events), 'frames': len(observations),
        'durable_calls': len(calls), 'expired_steps_completed': want['steps'],
        'model_decision': want['decision'], 'model_runner_s': result['model_runner_s'],
        'usage': result['usage'], 'new_input_submissions': want['new'],
        'post_decision_checkpoint_count': len(result['post_decision_effect_statuses']),
        'expired_acceptance_to_terminal_ms':
            (expired['terminal_ns'] - accepted['accepted_ns']) / 1e6,
        'initial_unknown_call_end_to_first_post_decision_call_begin_ms':
            (checkpoint_calls[1]['begin_ns'] - checkpoint_calls[0]['end_ns']) / 1e6,
        'expired_acceptance_to_verified_call_end_ms':
            (final_checkpoint['end_ns'] - accepted['accepted_ns']) / 1e6,
        'independent_success': True, 'exact_frames': True,
    }

# The rendered page below the browser chrome is pixel-identical. The ephemeral
# localhost port changes a small address-bar region and is not hidden.
with Image.open(post_images['before-return']).convert('RGB') as before, \
        Image.open(post_images['after-return']).convert('RGB') as after:
    assert before.size == after.size
    assert before.crop((0, 100, before.width, before.height)).tobytes() == \
        after.crop((0, 100, after.width, after.height)).tobytes()

report = {
    'scope': ('two fresh private Chromium sessions; v6-bound strict evidence drives '
              'different model decisions; one bounded verifier query completes each'),
    'calibration': cal_result['episodes'],
    'live': metrics,
    'page_pixels_below_browser_chrome_equal': True,
    'previous_before_return_post_decision_calls': read(
        H / 'results/partial-terminal-live-01/before-return/result.json')[
            'post_decision_effect_statuses'].__len__(),
    'current_before_return_post_decision_calls': 1,
    'planner_v4_controls': {'valid_revisions': 3, 'refusals': 5},
    'retained_v6_presenter_failure': True,
    'model_calls': 2, 'unsafe_proposals_executed': 0,
    'all_independent_success': True,
}
dump_path = LIVE / 'audit.json'
dump_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
