"""Audit one real CLI usage probe without attributing tokens to an image."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/model-boundary-probe-01'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    data = path.read_bytes()
    encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    return data.decode(encoding)


events = [json.loads(line) for line in read(ROOT / 'events.jsonl').splitlines()]
assert int(read(ROOT / 'exit-code.txt').strip()) == 0
assert [e['type'] for e in events] == [
    'thread.started', 'turn.started', 'item.completed', 'turn.completed']
item = events[2]['item']
assert item['type'] == 'agent_message'
answer = json.loads(item['text'])
assert answer['saved'] is False
assert 'Nothing has been saved' in answer['evidence']
assert 'Confirm replacement' in answer['next_action']
usage = events[-1]['usage']
for key in ('input_tokens', 'cached_input_tokens', 'output_tokens'):
    assert type(usage[key]) is int and usage[key] >= 0
assert usage['cached_input_tokens'] <= usage['input_tokens']
image = HERE / 'results/browser-emission-live-01/runtime/012.png'
source = json.loads((HERE / 'results/browser-emission-live-01/replace/result.json').read_text())
assert digest(image) == source['image']['sha256']
report = dict(
    audit_passed=True, answer=answer, reported_usage=usage,
    model_identity=None, model_received_ns=None, cost=None,
    image_sha256=digest(image),
    sources={name: digest(ROOT / name) for name in
             ('events.jsonl', 'prompt.txt', 'stderr.txt', 'cli-version.txt', 'exit-code.txt')},
    audit_sha256=digest(Path(__file__)),
    limitations=[
        'Usage belongs to this CLI turn, not this image or the live parent task.',
        'No tool execution items were emitted; absence is limited to this JSONL evidence.',
        'ignore-user-config did not prevent MCP startup diagnostics; environment isolation is unproven.',
        'Requested default model was not identified in emitted JSONL.',
        'No per-event capture timestamps, price calculation or matched-arm comparison.',
        'Known screenshot correctness is a smoke test, not a held-out benchmark.'])
with (ROOT / 'audit.json').open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps(report))
