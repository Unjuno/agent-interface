"""Audit the corrected fixed-image decision comparison and token counts."""
import hashlib
import json
from pathlib import Path
from delayed_decision_schema_v1 import parse

H = Path(__file__).resolve().parent
R = H / 'results/delayed-effect-decisions-01'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
plan, runs, result = read(R / 'plan.json'), read(R / 'runs.json'), read(R / 'result.json')
assert result == {'calls': 8, 'actions_executed': 0, 'all_calls_retained': True}
assert len(runs) == 8 and [row['mode'] for row in runs] == plan['order']
for name, digest in plan['sources'].items():
    assert sha(H / name.replace('\\', '/')) == digest, name

prepared = H / 'results/delayed-effect-05'
state = read(prepared / 'decision-state.json')
image = prepared / 'runtime' / Path(state['post_action']['image']).name
assert sha(image) == plan['image_sha256']
token = state['strict']['checkpoint']['contract']['expected']
common = None
summary = {}
for mode in ('A', 'B'):
    evidence = read(R / f'evidence-{mode}.json')
    assert evidence == state['strict' if mode == 'A' else 'lossy']
    prompt = (R / f'prompt-{mode}.txt').read_text(encoding='utf-8')
    suffix = json.dumps(evidence)
    assert prompt.endswith(suffix)
    prefix = prompt[:-len(suffix)]
    common = prefix if common is None else common
    assert prefix == common
    assert hashlib.sha256(prefix.encode()).hexdigest() == plan['common_prompt_sha256']
    assert len(json.dumps(evidence, separators=(',', ':')).encode()) == plan['evidence_bytes'][mode]
    subset = [row for row in runs if row['mode'] == mode]
    assert len(subset) == 4
    for row in subset:
        directory = R / f"model-{row['index']}-{mode}"
        process = read(directory / 'process.json')
        model_plan = read(directory / 'plan.json')
        assert row['exit_code'] == process['exit_code'] == 0 and 'parse_error' not in row
        assert model_plan['image_sha256'] == plan['image_sha256']
        assert model_plan['requested_model'] == plan['model'] and model_plan['requested_effort'] == plan['effort']
        assert (directory / 'prompt.txt').read_text(encoding='utf-8') == prompt
        raw = (directory / 'events.jsonl').read_bytes().splitlines(keepends=True)
        arrivals = [json.loads(line) for line in (directory / 'arrivals.jsonl').read_bytes().splitlines()]
        assert len(raw) == len(arrivals) == 4
        for index, (line, arrival) in enumerate(zip(raw, arrivals)):
            assert arrival['line'] == index and arrival['bytes'] == len(line)
            assert arrival['sha256'] == hashlib.sha256(line).hexdigest()
        events = [json.loads(line) for line in raw]
        proposal = parse(events[2]['item']['text'], token)
        assert proposal == row['proposal'] and events[3]['usage'] == row['usage']
        assert row['expected'] == plan['conditions'][mode]
        assert row['expected_decision'] is True and proposal['kind'] == row['expected']
        assert row['verify_on_unknown'] is False
    summary[mode] = {
        'calls': 4, 'expected_decisions': sum(row['expected_decision'] for row in subset),
        'kinds': [row['proposal']['kind'] for row in subset],
        'input_tokens': [row['usage']['input_tokens'] for row in subset],
        'cached_input_tokens': [row['usage']['cached_input_tokens'] for row in subset],
        'output_tokens': [row['usage']['output_tokens'] for row in subset],
        'runner_s': [(read(R / f"model-{row['index']}-{mode}/process.json")['exited_ns'] -
                      read(R / f"model-{row['index']}-{mode}/process.json")['started_ns']) / 1e9
                     for row in subset],
    }

report = {
    'scope': 'eight fixed-image calls; same image/common prompt; only evidence differs; no actions execute',
    'summary': summary,
    'all_expected_decisions': True,
    'verify_on_unknown': 0,
    'strict_mean_input_tokens': sum(summary['A']['input_tokens']) / 4,
    'lossy_mean_input_tokens': sum(summary['B']['input_tokens']) / 4,
    'interpretation': 'prior execution evidence changed wait-versus-submit decision in this declared fixture; four samples per condition are not a reliability bound',
}
(R / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
