"""Verify archive identity and audit original exchanges; no live GUI input."""
import hashlib,json,tarfile,tempfile
from pathlib import Path
from audit_pair import audit
root=Path(__file__).resolve().parent
result=json.loads((root/'result.json').read_text())
def require(value,message):
 if not value:raise ValueError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
require(sha(root/'raw.tar.gz')==result['archive']['sha256'],'archive hash')
require(sha(root/'audit_pair.py')==result['auditor_sha256'],'auditor hash')
require(sha(root/'timing_reader.py')==result['reader_sha256'],'reader hash')
manifest=json.loads((root/'raw-manifest.json').read_text())
with tempfile.TemporaryDirectory(prefix='spine13-verify-') as temp:
 with tarfile.open(root/'raw.tar.gz') as tar:
  members=[m for m in tar.getmembers() if m.isfile()]
  require({m.name for m in members}=={'trial/'+name for name in manifest},'exact members')
  tar.extractall(temp,filter='data')
 trial=Path(temp)/'trial'
 for name,record in manifest.items():
  p=trial/name
  require(sha(p)==record['sha256'] and p.stat().st_size==record['bytes'],'member '+name)
 actual=audit(trial)
 require(all(actual[k]==result[k] for k in actual),'published claims disagree')
print('PASS: archive identity, frozen inputs, exchanges, image review order, controls and six-task denominators. No speed/token/human claim.')
