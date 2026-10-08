"""Independent exact-source usage/boundary replay for this caller's own log."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
projections=[json.loads((root/f'usage-{label}.json').read_text()) for label in ('whole',)]
entries={}; actual={}; totals={}
for pi,p in enumerate(projections):
    for wi,w in enumerate(p['windows']):
        actual[pi,wi]={}
        for row in [w['begin'],w['end'],*w['usage_records']]: entries.setdefault(row['source_line'],[]).append((pi,wi,row))
        for c in w['calls']:
            entries.setdefault(c['source_line'],[]).append((pi,wi,c)); entries.setdefault(c['output']['source_line'],[]).append((pi,wi,c['output']))
found=set()
with Path(projections[0]['source_session']).open(encoding='utf-8') as source:
    for index,line in enumerate(source,1):
        if index not in entries: continue
        record=json.loads(line); payload=record.get('payload',{})
        for pi,wi,row in entries[index]:
            if hashlib.sha256(line.encode('utf-8')).hexdigest()!=row['source_sha256']: raise ValueError('source digest changed')
            if 'call_id' in row and row['call_id']!=payload['call_id']: raise ValueError('tool ID changed')
            if 'usage' in row:
                if record['type']!='token_usage_record' or payload['response_id']!=row['response_id'] or payload['usage']!=row['usage']: raise ValueError('usage changed')
                rid=payload['response_id']; known=actual[pi,wi]
                if rid in known and known[rid]!=payload['usage']: raise ValueError('conflicting response')
                known[rid]=payload['usage']
        found.add(index)
        if len(found)==len(entries): break
if len(found)!=len(entries): raise ValueError('missing source lines')
results=[]
for pi,p in enumerate(projections):
    for wi,w in enumerate(p['windows']):
        fields=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')
        t={k:sum(r[k] for r in actual[pi,wi].values()) for k in fields}; t['uncached_input_tokens']=t['input_tokens']-t['cached_input_tokens']
        if t!=w['totals']: raise ValueError('totals changed')
        results.append({'name':w['name'],'unique_responses':len(actual[pi,wi]),'totals':t})
print(json.dumps({'status':'PASS','source_lines':len(found),'windows':results,'scope':'combined construction/control/first-oracle window; billing unavailable; not arm-specific cost comparison'},indent=2))
