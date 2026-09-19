"""Verify raw CLI events and receiver timestamps for the explicit probe."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
root = HERE / 'results/model-boundary-probe-02'
read = lambda name: json.loads((root / name).read_text(encoding='utf-8'))
plan, process = read('plan.json'), read('process.json')
assert hashlib.sha256((HERE / 'model_probe_runner_v1.py').read_bytes()).hexdigest() == plan['runner_sha256']
assert process['exit_code'] == 0
lines = (root / 'events.jsonl').read_bytes().splitlines(keepends=True)
arrivals = [json.loads(line) for line in (root / 'arrivals.jsonl').read_text().splitlines()]
assert len(lines) == len(arrivals) == 4
for index, (line, arrival) in enumerate(zip(lines, arrivals)):
    assert arrival['line'] == index and arrival['bytes'] == len(line)
    assert arrival['sha256'] == hashlib.sha256(line).hexdigest()
times = [process['started_ns'], process['stdin_closed_ns']] + [a['received_ns'] for a in arrivals] + [process['exited_ns']]
assert times == sorted(times)
events = [json.loads(line) for line in lines]
assert [e['type'] for e in events] == ['thread.started', 'turn.started', 'item.completed', 'turn.completed']
assert events[2]['item']['type'] == 'agent_message'
answer = json.loads(events[2]['item']['text'])
assert answer['saved'] is False and 'Nothing has been saved' in answer['evidence']
assert 'Confirm replacement' in answer['next_action'] and 'Save' in answer['next_action']
usage = events[-1]['usage']
assert all(type(v) is int and v >= 0 for v in usage.values())
assert usage['cached_input_tokens'] <= usage['input_tokens']
assert (root / 'stderr.txt').read_text().strip() == 'Reading prompt from stdin...'
assert plan['requested_model'] == 'gpt-5.6-luna'
assert plan['requested_effort'] == 'low'
report = dict(audit_passed=True, usage=usage, answer=answer,
              local_process_seconds=(process['exited_ns']-process['started_ns'])/1e9,
              local_agent_message_arrival_seconds=(arrivals[2]['received_ns']-process['started_ns'])/1e9,
              observed_model_identity=None, no_mcp_diagnostics=True,
              scope='Requested configuration and emitted evidence only; no proof of full context isolation, actual served model identity or causal speedup.',
              audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (root / 'audit.json').open('x') as out:
    json.dump(report, out, indent=2)
    out.write('\n')
print(json.dumps(report))
