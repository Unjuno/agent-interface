import hashlib, importlib.util, json
from pathlib import Path
p=Path(__file__).resolve().parent
freeze=json.loads((p/'FREEZE.json').read_text(encoding='utf-8'))
for name,digest in freeze['sha256'].items():
 if hashlib.sha256((p/name).read_bytes()).hexdigest()!=digest: raise RuntimeError('freeze mismatch '+name)
c=json.loads((p/'conditions.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('pinned_relation_signature',p/'relation_signature.py'); module=importlib.util.module_from_spec(spec); import sys; sys.modules[spec.name]=module; spec.loader.exec_module(module)
source=c['source']; rows=[]
for case in c['cases']:
 visible=case['candidates']; answer=module.revalidate(source,visible,generation=5,complete=True)
 compatible=sum(all(x[k]==source[k] for k in ('surface','container','role','label')) for x in visible)
 alternative='UNKNOWN' if compatible>1 else answer.status
 truth=case['hidden_original_index']
 rows.append({'id':case['id'],'matcher':{'status':answer.status,'candidate_index':answer.candidate_index,'authority':answer.authority},'hidden_original_index':truth,'semantic_correct':answer.status=='REVALIDATED' and answer.candidate_index==truth,'false_rebind':answer.status=='REVALIDATED' and answer.candidate_index!=truth,'conservative_status':alternative})
result={'source_sha256':freeze['sha256']['relation_signature.py'],'rows':rows,'two_candidate_inputs_identical':c['cases'][0]['candidates']==c['cases'][1]['candidates'],'single_candidate_inputs_identical':c['cases'][2]['candidates']==c['cases'][3]['candidates'],'false_rebind_cases':sum(x['false_rebind'] for x in rows),'conservative_abstentions':sum(x['conservative_status']=='UNKNOWN' for x in rows),'classification':'SYNTHETIC_IDENTIFIABILITY_COUNTEREXAMPLE'}
with (p/'raw-result.json').open('x',encoding='utf-8') as f: json.dump(result,f,indent=2); f.write('\n')
print(json.dumps(result,indent=2))
