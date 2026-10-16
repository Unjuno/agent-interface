"""Audit registered static presentation pairs, retaining cache differences."""
import hashlib
import json
from pathlib import Path
from shared_result_v1 import canonical, decode

HERE = Path(__file__).resolve().parent
root = HERE / 'results/model-presentation-pair-01'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
plan = read(root / 'plan.json')
for name, digest in plan['sources'].items():
    assert sha(HERE/name) == digest
rows = []
common_args = None
for s in plan['schedule']:
    folder = root/s['name']
    assert sha(root/(s['name']+'.txt')) == sha(folder/'prompt.txt')
    assert hashlib.sha256((folder/'prompt.txt').read_text(encoding='utf-8').encode()).hexdigest() == s['prompt_sha256']
    assert sha(Path(s['image'])) == s['image_sha256']
    source = HERE/'results/browser-emission-live-01'/s['stage']/'result.json'
    assert sha(source) == s['source_sha256']
    payload = json.loads((folder/'prompt.txt').read_text(encoding='utf-8').split('\n', 1)[1])
    restored = decode(payload) if s['arm'] == 'shared' else payload
    assert canonical(restored) == canonical(read(source))
    runplan, proc = read(folder/'plan.json'), read(folder/'process.json')
    assert proc['exit_code'] == 0
    args = runplan['args'][:]
    args[args.index('-i')+1] = '<image>'
    if common_args is None: common_args = args
    assert args == common_args
    lines = (folder/'events.jsonl').read_bytes().splitlines(keepends=True)
    arrivals = [json.loads(x) for x in (folder/'arrivals.jsonl').read_text().splitlines()]
    assert len(lines) == len(arrivals) == 4
    for i, (line,a) in enumerate(zip(lines,arrivals)):
        assert a['line']==i and a['bytes']==len(line) and a['sha256']==hashlib.sha256(line).hexdigest()
    times=[proc['started_ns'],proc['stdin_closed_ns']]+[a['received_ns'] for a in arrivals]+[proc['exited_ns']]
    assert times==sorted(times)
    events=[json.loads(x) for x in lines]
    assert [e['type'] for e in events]==['thread.started','turn.started','item.completed','turn.completed']
    assert events[2]['item']['type']=='agent_message'
    answer=json.loads(events[2]['item']['text'])
    assert answer['saved'] is s['expected_saved']
    assert answer['program_completion_proves_task_success'] is False
    assert (folder/'stderr.txt').read_text().strip()=='Reading prompt from stdin...'
    usage=events[-1]['usage']
    assert all(type(v) is int and v>=0 for v in usage.values())
    assert usage['cached_input_tokens']<=usage['input_tokens']
    rows.append(dict(name=s['name'],usage=usage,answer=answer,prompt_bytes=s['prompt_bytes'],
        local_answer_arrival_seconds=(arrivals[2]['received_ns']-proc['started_ns'])/1e9))
pairs=[]
for stage in ('replace','confirm'):
    full=next(r for r in rows if r['name']==stage+'-full')
    shared=next(r for r in rows if r['name']==stage+'-shared')
    difference=full['usage']['input_tokens']-shared['usage']['input_tokens']
    pairs.append(dict(stage=stage,input_token_difference=difference,
        percent_of_full=100*difference/full['usage']['input_tokens']))
report=dict(audit_passed=True,rows=rows,pairs=pairs,
    audit_sha256=sha(Path(__file__)),decision='Keep shared representation experimental; two easy known scenes and under 1 percent turn-input difference do not justify adoption.',
    limits='Same requested model and CLI arguments, not verified served identity or identical hidden context. Cache differs. Static screenshot task with explicit semantic caution; no GUI action/recovery or causal latency claim.')
with (root/'audit.json').open('x',encoding='utf-8') as out: json.dump(report,out,indent=2);out.write('\n')
print(json.dumps(dict(audit_passed=True,pairs=pairs)))
