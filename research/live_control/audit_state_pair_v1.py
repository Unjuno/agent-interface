"""Audit record extraction and actual usage without rerunning failed answers."""
import hashlib
import json
from pathlib import Path
from composed_result_v1 import decode
from shared_result_v1 import canonical

HERE=Path(__file__).resolve().parent;root=HERE/'results/model-state-pair-01'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(root/'plan.json');rows=[];common=None
for n,digest in plan['sources'].items():assert sha(HERE/n)==digest
for s in plan['schedule']:
    d=root/s['name'];p=read(d/'plan.json');proc=read(d/'process.json')
    assert proc['exit_code']==0
    assert p['stdin_sha256']==s['stdin_sha256']==sha(d/'prompt.txt')==sha(root/(s['name']+'.txt'))
    assert sha(Path(s['source']))==s['source_sha256']
    text=(d/'prompt.txt').read_text(encoding='utf-8');payload=json.loads(text[text.index('\n{')+1:])
    assert canonical(decode(payload) if s['arm']=='composed' else payload)==canonical(read(Path(s['source'])))
    if common is None:common=p['args']
    assert p['args']==common
    lines=(d/'events.jsonl').read_bytes().splitlines(keepends=True)
    arrivals=[json.loads(x) for x in (d/'arrivals.jsonl').read_text().splitlines()]
    assert len(lines)==len(arrivals)
    for i,(line,a) in enumerate(zip(lines,arrivals)):
        assert a['line']==i and a['sha256']==hashlib.sha256(line).hexdigest() and a['bytes']==len(line)
    times=[proc['started_ns'],proc['stdin_closed_ns']]+[a['received_ns'] for a in arrivals]+[proc['exited_ns']]
    assert times==sorted(times)
    es=[json.loads(x) for x in lines]
    assert [e['type'] for e in es]==['thread.started','turn.started','item.completed','turn.completed']
    assert es[2]['item']['type']=='agent_message'
    try:answer=json.loads(es[2]['item']['text']);parse_error=None
    except ValueError as error:answer=None;parse_error=str(error)
    usage=es[-1]['usage'];assert all(type(v) is int and v>=0 for v in usage.values())
    assert usage['cached_input_tokens']<=usage['input_tokens']
    rows.append(dict(name=s['name'],correct=canonical(answer)==canonical(s['expected']),answer=answer,
        expected=s['expected'],parse_error=parse_error,usage=usage,
        stderr=(d/'stderr.txt').read_text(),local_process_seconds=(times[-1]-times[0])/1e9))
pairs=[]
for case in ('pending','terminal'):
    a=next(r for r in rows if r['name']==case+'-full');b=next(r for r in rows if r['name']==case+'-composed')
    pairs.append(dict(case=case,input_difference=a['usage']['input_tokens']-b['usage']['input_tokens'],
        full_input=a['usage']['input_tokens'],composed_input=b['usage']['input_tokens'],both_correct=a['correct'] and b['correct']))
report=dict(evidence_audit_passed=True,all_answers_correct=all(r['correct'] for r in rows),rows=rows,pairs=pairs,
    audit_sha256=sha(Path(__file__)),limits='Two known static records, requested model only; no GUI action, full context identity, billed cost or causal latency proof.')
with (root/'audit.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
print(json.dumps(dict(all_answers_correct=report['all_answers_correct'],pairs=pairs)))
