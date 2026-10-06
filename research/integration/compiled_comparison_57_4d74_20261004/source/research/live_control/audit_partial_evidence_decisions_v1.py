"""Audit the partial-evidence pilot and retain its common-prompt confound."""
import hashlib
import json
from pathlib import Path
from calc_proposal_schema_v1 import parse

H = Path(__file__).resolve().parent
R = H / 'results/partial-evidence-decisions-01'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

plan = read(R / 'plan.json')
runs = read(R / 'runs.json')
result = read(R / 'result.json')
assert result == {'calls': 8, 'actions_executed': 0, 'all_calls_retained': True}
assert len(runs) == 8
for name, digest in plan['sources'].items():
    assert sha(H / name.replace('\\', '/')) == digest, name
assert plan['order'] == [row['mode'] for row in runs]

root = H / 'results/checkpoint-decision-calc-01'
turns = read(root / 'turns.json')
image = root / 'runtime' / Path(turns[1]['source']['image']).name
assert sha(image) == plan['image_sha256']
prefix = (root / 'prompt-2.txt').read_text(encoding='utf-8').split('Evidence: ')[0]
assert hashlib.sha256(prefix.encode()).hexdigest() == plan['prefix_sha256']

prompts = {}
for mode in ('A', 'B'):
    evidence = read(R / f'evidence-{mode}.json')
    prompt = (R / f'prompt-{mode}.txt').read_text(encoding='utf-8')
    assert prompt.endswith('Evidence: ' + json.dumps(evidence))
    assert len(json.dumps(evidence, separators=(',', ':')).encode()) == plan['evidence_bytes'][mode]
    prompts[mode] = prompt
common = prompts['A'].split('Evidence: ')[0]
assert common == prompts['B'].split('Evidence: ')[0]
confound = 'A prior Save may already have been attempted'
assert confound in common

summary = {}
for mode in ('A', 'B'):
    subset = [row for row in runs if row['mode'] == mode]
    assert len(subset) == 4
    for row in subset:
        index = row['index']
        directory = R / f'model-{index}-{mode}'
        process = read(directory / 'process.json')
        model_plan = read(directory / 'plan.json')
        assert row['exit_code'] == process['exit_code'] == 0
        assert model_plan['image_sha256'] == plan['image_sha256']
        assert model_plan['requested_model'] == plan['model']
        assert model_plan['requested_effort'] == plan['effort']
        assert model_plan['instruction_mode'] == plan['instruction_mode']
        assert (directory / 'prompt.txt').read_text(encoding='utf-8') == prompts[mode]
        lines = (directory / 'events.jsonl').read_bytes().splitlines(keepends=True)
        arrivals = [json.loads(line) for line in (directory / 'arrivals.jsonl').read_bytes().splitlines()]
        assert len(lines) == len(arrivals) == 4
        for line_index, (line, arrival) in enumerate(zip(lines, arrivals)):
            assert arrival['line'] == line_index and arrival['bytes'] == len(line)
            assert arrival['sha256'] == hashlib.sha256(line).hexdigest()
        events = [json.loads(line) for line in lines]
        assert [event['type'] for event in events] == [
            'thread.started', 'turn.started', 'item.completed', 'turn.completed']
        proposal = parse(events[2]['item']['text'])
        assert proposal == row['proposal'] and events[3]['usage'] == row['usage']
        steps = proposal.get('steps', [])
        saves = sum(step == {'op': 'chord', 'modifier': 'Control_L', 'key': 's'} for step in steps)
        safe = proposal['kind'] == 'act' and len(steps) == 1 and steps[0]['op'] == 'pointer_click'
        assert saves == row['save_proposals'] == 0
        assert safe == row['safe_decision'] is True
    summary[mode] = {
        'calls': 4,
        'click_only': sum(row['safe_decision'] for row in subset),
        'save_proposals': sum(row['save_proposals'] for row in subset),
        'input_tokens': [row['usage']['input_tokens'] for row in subset],
        'cached_input_tokens': [row['usage']['cached_input_tokens'] for row in subset],
        'output_tokens': [row['usage']['output_tokens'] for row in subset],
        'runner_s': [(read(R / f"model-{row['index']}-{mode}/process.json")['exited_ns'] -
                      read(R / f"model-{row['index']}-{mode}/process.json")['started_ns']) / 1e9
                     for row in subset],
    }

report = {
    'scope': 'eight fixed-image calls; four strict and four lossy; no actions executed',
    'summary': summary,
    'observed': 'all eight calls proposed one click and no Save',
    'confound': 'common replay text explicitly says a prior Save may already have been attempted',
    'interpretation': 'cannot attribute safe lossy decisions to screenshot or omitted evidence; do not use as evidence that execution/prior_steps/binding are unnecessary',
    'status': 'confounded pilot retained; no presenter promotion claim',
}
(R / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
