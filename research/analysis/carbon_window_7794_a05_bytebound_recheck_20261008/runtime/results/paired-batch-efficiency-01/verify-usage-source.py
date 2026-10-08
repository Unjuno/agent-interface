import hashlib,json
from pathlib import Path
root=Path('/var/tmp/agent-interface-evidence-storage-main')
p=json.loads((root/'results-local/paired-batch-efficiency-01/usage-projection.json').read_text())
windows=p['windows']
expected={r['source_line']:r for w in windows for r in w['usage_records']}
found=set()
actual={w['name']:{} for w in windows}
source='/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl'
with open(source,encoding='utf-8') as stream:
    for i,line in enumerate(stream,1):
        if i>windows[-1]['end']['source_line']:break
        for w in windows:
            if w['begin']['source_line']<=i<=w['end']['source_line']:
                r=json.loads(line)
                if r.get('type')=='token_usage_record':
                    e=expected.get(i)
                    if e is None or e['source_sha256']!=hashlib.sha256(line.encode()).hexdigest() or e['usage']!=r['payload']['usage']:
                        raise RuntimeError('Usage source/coverage mismatch')
                    found.add(i)
                    rid=r['payload']['response_id']
                    if rid in actual[w['name']] and actual[w['name']][rid]!=r['payload']['usage']:
                        raise RuntimeError('Conflicting duplicate')
                    actual[w['name']][rid]=r['payload']['usage']
                for edge in ('begin','end'):
                    if i==w[edge]['source_line']:
                        expected_type='custom_tool_call' if edge=='begin' else 'custom_tool_call_output'
                        if r['payload']['call_id']!=w[edge+'_call_id'] or r['payload']['type']!=expected_type or hashlib.sha256(line.encode()).hexdigest()!=w[edge]['source_sha256']:
                            raise RuntimeError('Boundary source mismatch')
if found!=set(expected):raise RuntimeError('Missing retained usage')
for w in windows:
    for k,v in w['totals'].items():
        total=sum(u['input_tokens']-u['cached_input_tokens'] if k=='uncached_input_tokens' else u[k] for u in actual[w['name']].values())
        if total!=v:raise RuntimeError('Total mismatch')
print(json.dumps({'status':'PASS_SOURCE_COVERAGE_AND_TOTALS','usage_records':len(found),'windows':len(windows)}))

