"""Generate candidate results from the pinned analyzer and raw identity cases."""
import hashlib, importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
freeze=json.loads((HERE/'FREEZE.json').read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for key,name in [('analyzer_sha256','analyzer.py'),('tests_sha256','tests.py'),('raw_sha256','raw_cases.json'),('candidate_runner_sha256','candidate.py')]:
    if sha(HERE/name)!=freeze[key]: raise SystemExit(f'frozen input drift: {key}')
out=HERE/'candidate_results.json'
if out.exists(): raise FileExistsError(f'refusing to overwrite {out}')
spec=importlib.util.spec_from_file_location('pinned_candidate',HERE/'analyzer.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
raw=json.loads((HERE/'raw_cases.json').read_text(encoding='utf-8'))
results=[{'case_id':case['case_id'],'result':module.analyze(case['events'])} for case in raw['cases']]
payload={'schema':'direct-retained-token-key-candidate-v1','analyzer_sha256':sha(HERE/'analyzer.py'),'tests_sha256':sha(HERE/'tests.py'),'case_count':len(results),'results':results}
out.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'case_count':len(results),'output':str(out)},indent=2))
