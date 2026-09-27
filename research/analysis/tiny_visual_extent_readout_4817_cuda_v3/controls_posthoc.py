import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
audit=Path(sys.argv[1]); root=Path(sys.argv[2]); original=json.loads((root/'RAW.json').read_text())
mutations=('alter_logit','drop_center','change_allocation','change_seed','change_step_count','negative_fit_time','change_source_hash','corrupt_input_bytes')
rows=[]
for name in mutations:
 with tempfile.TemporaryDirectory(prefix='mctrl-',dir='/tmp') as td:
  p=Path(td)
  for f in ('RAW.json','INPUTS.npz','WEIGHTS.npz','INITIAL_WEIGHTS.npz'): shutil.copy2(root/f,p/f)
  raw=copy.deepcopy(original)
  if name=='alter_logit': raw['logits']['max_mean']['held_0'][0]+=0.01
  elif name=='drop_center': raw['logits']['max_mean'].pop('held_7')
  elif name=='change_allocation': raw['allocation']='wrong'
  elif name=='change_seed': raw['data_seed']+=1
  elif name=='change_step_count': raw['steps']-=1
  elif name=='negative_fit_time': raw['fit_seconds']['max_mean']=-1
  elif name=='change_source_hash': raw['source_sha256']={'run_cuda.py':'0'*64}
  elif name=='corrupt_input_bytes': (p/'INPUTS.npz').write_bytes((p/'INPUTS.npz').read_bytes()+b'x')
  (p/'RAW.json').write_text(json.dumps(raw,sort_keys=True,separators=(',',':'))+'\n')
  q=subprocess.run([sys.executable,str(audit),str(p)],capture_output=True,text=True)
  rows.append({'mutation':name,'rejected':q.returncode!=0,'exit':q.returncode})
out={'rejected':sum(r['rejected'] for r in rows),'total':len(rows),'pass_all':all(r['rejected'] for r in rows),'controls':rows}
Path('/out/CONTROL_RESULTS.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps(out,sort_keys=True))

