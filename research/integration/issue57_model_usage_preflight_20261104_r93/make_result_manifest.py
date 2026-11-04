import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
files=[]
for p in sorted((root/'r93-a01').rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:
        files.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,
                      'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
manifest={'schema':'agent-interface/attempt-evidence-sha256-v1','attempt_id':'issue57-r93-a01','files':files}
out=root/'RESULTS-SHA256.json'
out.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'bytes':sum(f['bytes'] for f in files),'manifest_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
