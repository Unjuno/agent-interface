import json,shutil,subprocess
from pathlib import Path
root=Path('/state'); root.mkdir(exist_ok=True); out=Path('/out'); out.mkdir(exist_ok=True); rows=[]
for run in range(1,4):
    shutil.rmtree(root,ignore_errors=True); root.mkdir()
    a=subprocess.run(['python3','/fixture/orch.py','A'],capture_output=True,text=True,timeout=30)
    b=subprocess.run(['python3','/fixture/orch.py','B'],capture_output=True,text=True,timeout=30)
    row=json.loads((root/'result-B.json').read_text()); row['run']=run; row['a_exit']=a.returncode; row['b_exit']=b.returncode; rows.append(row)
(out/'raw.jsonl').write_text('\n'.join(json.dumps(r,sort_keys=True) for r in rows)+'\n')
print(json.dumps({'rows':len(rows)}))