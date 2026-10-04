"""Replay fixed-input tier evidence; never launches a model or GUI action."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/model-context-01'
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(data):
    return hashlib.sha256(data).hexdigest()

plan = read(ROOT / 'plan.json')
for name, digest in plan['sources'].items():
    assert sha((HERE / name).read_bytes()) == digest, name
prompt = (HERE / 'results/live-append-calc-01/prompt-2.txt').read_bytes()
image = (HERE / 'results/live-append-calc-01/runtime/007.png').read_bytes()
assert sha(prompt) == plan['prompt_sha256']
assert sha(image) == plan['image_sha256']
runs = read(ROOT / 'runs.json')
assert [r['instruction_mode'] for r in runs] == ['builtin', 'responder', 'responder', 'builtin']
rows = []
common_args = None
for run in runs:
    tier = run['instruction_mode']
    root = ROOT / f"{run['index']}-{tier}"
    p = read(root / 'plan.json'); process = read(root / 'process.json')
    assert run['exit_code'] == process['exit_code'] == 0
    assert p['instruction_mode'] == tier
    assert p['requested_model'] == 'gpt-5.6-luna' and p['requested_effort'] == 'low'
    assert p['runner_sha256'] == plan['sources']['model_context_runner_v1.py']
    assert p['image_sha256'] == sha(image)
    assert (root / 'prompt.txt').read_bytes() == prompt
    args = p['args']; at = args.index('-C')
    flags = ['-c', 'model_instructions_file='+json.dumps((HERE/'screenshot_responder_v1.txt').resolve().as_posix())] if tier == 'responder' else []
    if flags:
        assert args[at-len(flags):at] == flags
        assert p['instructions_sha256'] == plan['sources']['screenshot_responder_v1.txt']
    else: assert p['instructions_sha256'] is None
    normalized = args[:at-len(flags)] + args[at:]
    assert normalized[normalized.index('-C')-2:normalized.index('-C')]==['--disable','fast_mode']
    if common_args is None: common_args = normalized
    assert normalized == common_args
    raw = (root / 'events.jsonl').read_bytes().splitlines(keepends=True)
    arrivals = [json.loads(s) for s in (root / 'arrivals.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(raw) == len(arrivals) == 4
    for n, (line, arrival) in enumerate(zip(raw, arrivals)):
        assert arrival['line'] == n and arrival['bytes'] == len(line) and arrival['sha256'] == sha(line)
    events = [json.loads(line) for line in raw]
    assert [e['type'] for e in events] == ['thread.started', 'turn.started', 'item.completed', 'turn.completed']
    assert events[2]['item']['type'] == 'agent_message'
    proposal = json.loads(events[2]['item']['text'])
    assert set(proposal) == {'steps', 'rationale'} and isinstance(proposal['rationale'], str)
    assert len(proposal['steps']) == 1
    step = proposal['steps'][0]
    assert set(step) == {'op', 'x', 'y', 'duration_ms'}
    assert step['op'] == 'pointer_click' and step['duration_ms'] == 80
    # Manually inspected archived screenshot: interior of Excel confirmation button.
    assert type(step['x']) is int and type(step['y']) is int
    assert 698 <= step['x'] <= 872 and 451 <= step['y'] <= 475
    times = [process['started_ns'], process['stdin_closed_ns']] + [a['received_ns'] for a in arrivals] + [process['exited_ns']]
    assert times == sorted(times)
    rows.append(dict(index=run['index'], instruction_mode=tier,
                     runner_seconds=(process['exited_ns']-process['started_ns'])/1e9,
                     proposal_arrival_seconds=(arrivals[2]['received_ns']-process['started_ns'])/1e9,
                     usage=events[3]['usage'], proposed_click=[step['x'], step['y']]))
report = dict(scope='fixed archived screenshot inference only; no GUI execution; instruction replacement changes context; full transmitted context unavailable', rows=rows)
(ROOT / 'audit.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, indent=2))
