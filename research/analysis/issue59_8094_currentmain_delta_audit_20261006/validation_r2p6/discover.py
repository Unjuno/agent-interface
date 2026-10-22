import copy,hashlib,json,subprocess,sys
from pathlib import Path
r=Path(__file__).parent
base=json.loads((r/'original/RESULT.json').read_bytes())
probes=[]
for name in ('baseline','duplicate_replace','modified_candidate_null','unbound_candidate_ref','candidate_equals_main'):
 d=copy.deepcopy(base)
 if name=='duplicate_replace':d['paths'][2]=copy.deepcopy(d['paths'][1])
 elif name=='modified_candidate_null':d['paths'][1]['candidate_sha']=None
 elif name=='unbound_candidate_ref':d['candidate_head']='0'*40
 elif name=='candidate_equals_main':d['paths'][1]['candidate_sha']=d['paths'][1]['main_sha']
 for optimized in (False,True):
  p=r/'discovery'/f'{name}-'+Path('x') if False else r/'discovery'/f'{name}-{int(optimized)}'
  p.mkdir(exist_ok=False)
  (p/'RESULT.json').write_text(json.dumps(d,indent=2)+'\n')
  (p/'verify.py').write_bytes((r/'original/verify.py').read_bytes())
  cmd=[sys.executable,'-I','-B']+(['-O'] if optimized else [])+[str(p/'verify.py')]
  c=subprocess.run(cmd,capture_output=True,timeout=5)
  (p/'stdout.txt').write_bytes(c.stdout);(p/'stderr.txt').write_bytes(c.stderr)
  row={'case':name,'optimized':optimized,'command':cmd,'returncode':c.returncode,'input_sha256':hashlib.sha256((p/'RESULT.json').read_bytes()).hexdigest()}
  (p/'execution.json').write_text(json.dumps(row,indent=2)+'\n');probes.append(row)
(r/'discovery/summary.json').write_text(json.dumps(probes,indent=2)+'\n')
print(json.dumps([{'case':x['case'],'optimized':x['optimized'],'exit':x['returncode']} for x in probes],indent=2))
