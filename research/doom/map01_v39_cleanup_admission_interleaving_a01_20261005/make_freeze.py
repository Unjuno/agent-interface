import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
files=['SOURCE_LOCK.json','attempts/A01_INCONCLUSIVE_RAW.json','attempts/A02_PASS_8414805493_RAW.json','attempts/A03_PASS_39264f167f_RAW.json','attempts/A01_probe.py','attempts/A02_probe.py','attempts/A03_probe.py']
def sha(rel): return hashlib.sha256((p/rel).read_bytes()).hexdigest()
f=json.loads((p/'FREEZE.json').read_text())
f['artifact_sha256']={rel:sha(rel) for rel in files}
(p/'FREEZE.json').write_text(json.dumps(f,indent=2)+'\n')
