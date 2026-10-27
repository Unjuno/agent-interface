import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'conditions.json').read_text(encoding='utf-8')); r=json.loads((p/'raw-result.json').read_text(encoding='utf-8')); f=json.loads((p/'FREEZE.json').read_text(encoding='utf-8'))
checks={'frozen_inputs':all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in f['sha256'].items()),'paired_two_visible_equal':c['cases'][0]['candidates']==c['cases'][1]['candidates'],'paired_single_visible_equal':c['cases'][2]['candidates']==c['cases'][3]['candidates'],'ground_truths_differ':c['cases'][0]['hidden_original_index']!=c['cases'][1]['hidden_original_index'] and c['cases'][2]['hidden_original_index']!=c['cases'][3]['hidden_original_index'],'same_reported_choice':all(x['matcher']=={'status':'REVALIDATED','candidate_index':0,'authority':'none'} for x in r['rows']),'false_rebind_indices':[x['id'] for x in r['rows'] if x['false_rebind']]==['two-swapped','single-replaced'],'conservative_abstains_only_two': [x['conservative_status'] for x in r['rows']]==['UNKNOWN','UNKNOWN','REVALIDATED','REVALIDATED']}
with (p/'audit-result.json').open('x',encoding='utf-8') as q: json.dump(checks,q,indent=2); q.write('\n')
print(json.dumps(checks,indent=2))
if not all(checks.values()): raise SystemExit(1)
