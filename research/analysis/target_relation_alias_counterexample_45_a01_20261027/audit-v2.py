import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'conditions.json').read_text(encoding='utf-8')); r=json.loads((p/'raw-result.json').read_text(encoding='utf-8')); f=json.loads((p/'FREEZE.json').read_text(encoding='utf-8'))
source=c['source']; cases=c['cases']; rows=r['rows']; keys=('surface','container','role','label')
checks={'frozen_inputs':all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in f['sha256'].items()),'row_ids_match':[x['id'] for x in rows]==[x['id'] for x in cases],'paired_inputs_identical':cases[0]['candidates']==cases[1]['candidates'] and cases[2]['candidates']==cases[3]['candidates'],'hidden_labels_differ':cases[0]['hidden_original_index']!=cases[1]['hidden_original_index'] and cases[2]['hidden_original_index']!=cases[3]['hidden_original_index'],'no_authority':all(x['matcher']['authority']=='none' for x in rows)}
expected=[]
for case in cases:
 exact=[i for i,v in enumerate(case['candidates']) if all(v[k]==source[k] for k in keys) and frozenset(v['relations'])==frozenset(source['relations'])]; compatible=[v for v in case['candidates'] if all(v[k]==source[k] for k in keys)]; chosen=exact[0] if len(exact)==1 else None; expected.append({'status':'REVALIDATED' if chosen is not None else 'UNKNOWN','index':chosen,'false':chosen is not None and chosen!=case['hidden_original_index'],'alternative':'UNKNOWN' if len(compatible)>1 else 'REVALIDATED'})
checks['matcher_results_independently_recomputed']=all(row['matcher']['status']==want['status'] and row['matcher']['candidate_index']==want['index'] for row,want in zip(rows,expected))
checks['scores_independently_recomputed']=all(row['hidden_original_index']==case['hidden_original_index'] and row['false_rebind']==want['false'] and row['semantic_correct']==(want['index'] is not None and want['index']==case['hidden_original_index']) and row['conservative_status']==want['alternative'] for row,case,want in zip(rows,cases,expected))
checks['predeclared_counterexamples']=[case['id'] for case,want in zip(cases,expected) if want['false']]==['two-swapped','single-replaced']
with (p/'audit-v2-result.json').open('x',encoding='utf-8') as q: json.dump(checks,q,indent=2); q.write('\n')
print(json.dumps(checks,indent=2))
if not all(checks.values()): raise SystemExit(1)
