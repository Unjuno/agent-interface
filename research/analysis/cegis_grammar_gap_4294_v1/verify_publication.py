import base64, hashlib, io, json, tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
errors=[]
sm=json.loads((root/'SOURCE_BUNDLE.json').read_text())
sb=base64.b64decode((root/'SOURCE_BUNDLE.b64').read_text())
if hashlib.sha256(sb).hexdigest()!=sm['archive_sha256']: errors.append('source_archive')
rm=json.loads((root/'RESULT_BUNDLE.json').read_text())
parts=[]
for c in rm['chunks']:
    p=root/c['name']; b=p.read_bytes()
    if hashlib.sha256(b).hexdigest()!=c['sha256']: errors.append('chunk:'+c['name'])
    parts.append(p.read_text().strip())
rb=base64.b64decode(''.join(parts))
if hashlib.sha256(rb).hexdigest()!=rm['archive_sha256']: errors.append('result_archive')
with tarfile.open(fileobj=io.BytesIO(rb),mode='r:xz') as tf:
    audit=json.load(tf.extractfile('formal/AUDIT.json'))
    controls=json.load(tf.extractfile('formal/CONTROLS.json'))
    raw=tf.extractfile('formal/FORMAL_RESULT.json').read()
if audit['decision']!='PASS_CEGIS_GRAMMAR_GAP_DETECTION_SCOPED' or audit['errors']!=[]: errors.append('audit')
if len(controls)!=13 or not all(controls.values()): errors.append('controls')
if hashlib.sha256(raw).hexdigest()!=audit['formal_sha256']: errors.append('formal_raw')
print(json.dumps({'checks':len(rm['chunks'])+6,'errors':errors,'formal_sha256':audit['formal_sha256']},sort_keys=True,indent=2))
raise SystemExit(bool(errors))
