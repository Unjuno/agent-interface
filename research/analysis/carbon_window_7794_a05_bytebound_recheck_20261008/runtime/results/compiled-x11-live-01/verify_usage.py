"""Replay exact stored counters/boundaries against this primary caller's own log."""
import hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=json.loads((HERE/'usage-projection.json').read_text()); window=p['windows'][0]
entries={}
for row in [window['begin'],window['end'],*window['usage_records']]: entries.setdefault(row['source_line'],[]).append(row)
for call in window['calls']:
    entries.setdefault(call['source_line'],[]).append(call)
    entries.setdefault(call['output']['source_line'],[]).append(call['output'])
found={}; usage={}
with Path(p['source_session']).open(encoding='utf-8') as source:
    for index,line in enumerate(source,1):
        if index not in entries: continue
        record=json.loads(line); payload=record.get('payload',{})
        for row in entries[index]:
            if hashlib.sha256(line.encode('utf-8')).hexdigest()!=row['source_sha256']: raise ValueError('source line changed')
            if 'usage' in row:
                if record['type']!='token_usage_record' or payload['response_id']!=row['response_id'] or payload['usage']!=row['usage']: raise ValueError('usage source mismatch')
                rid=payload['response_id']
                if rid in usage and usage[rid]!=payload['usage']: raise ValueError('conflicting response')
                usage[rid]=payload['usage']
            if 'call_id' in row and payload['call_id']!=row['call_id']: raise ValueError('tool boundary mismatch')
        found[index]=True
        if len(found)==len(entries): break
if len(found)!=len(entries): raise ValueError('missing source records')
fields=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')
totals={k:sum(r[k] for r in usage.values()) for k in fields}; totals['uncached_input_tokens']=totals['input_tokens']-totals['cached_input_tokens']
if totals!=window['totals']: raise ValueError('usage total mismatch')
print(json.dumps({'status':'PASS','source_lines_checked':len(entries),'unique_responses':len(usage),'totals':totals,'scope':'selected whole-context usage; no tool-only/image billing attribution'},indent=2))
