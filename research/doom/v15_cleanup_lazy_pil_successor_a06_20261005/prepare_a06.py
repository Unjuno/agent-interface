from pathlib import Path
import hashlib,json,subprocess
REPO=Path.cwd(); PACKAGE=REPO/'research/doom/v15_cleanup_lazy_pil_successor_a06_20261005'; OUT=Path(r'C:\s15e'); TREE='78b8636f08bef691944da8bb536437586f0d116a'
if OUT.exists(): raise SystemExit('REFUSE: frozen A06 scratch root already exists')
source=json.loads((REPO/'research/doom/v15_cleanup_lazy_pil_successor_a04_20261005/SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig'))
if source['tree']!=TREE or len(source['files'])!=2013: raise SystemExit('A04 source manifest identity mismatch')
OUT.mkdir(parents=True)
items=source['files']; request=b''.join(x['blob'].encode()+b'\n' for x in items)
raw=subprocess.run(['git','cat-file','--batch'],input=request,check=True,stdout=subprocess.PIPE).stdout; pos=0; staged=[]
for x in items:
 end=raw.index(b'\n',pos); head=raw[pos:end].split(); size=int(head[2]); start=end+1; blob=raw[start:start+size]
 if head[0].decode()!=x['blob'] or head[1]!=b'blob' or size!=x['bytes'] or hashlib.sha256(blob).hexdigest()!=x['sha256'] or len(blob)!=size: raise SystemExit('Git source verification failed: '+x['path'])
 path=OUT/x['path']; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(blob); staged.append(x); pos=start+size+1
if pos!=len(raw): raise SystemExit('unconsumed Git object output')
target=OUT/'research/doom/doom_typed_coast_backend_v1.py'; base=target.read_bytes(); lines=base.splitlines(keepends=True); new=[]; removed=inserted=False
for line in lines:
 if line.lstrip().startswith(b'from PIL import ImageGrab'):
  if removed: raise SystemExit('duplicate top-level PIL import')
  removed=True; continue
 if b'ImageGrab.grab(xdisplay=self.session.name)' in line:
  if not removed or inserted: raise SystemExit('frozen snapshot anchor mismatch')
  nl=b'\r\n' if line.endswith(b'\r\n') else b'\n'; new.append(line[:len(line)-len(line.lstrip())]+b'from PIL import ImageGrab'+nl); inserted=True
 new.append(line)
if not removed or not inserted: raise SystemExit('frozen import relocation absent')
patched=b''.join(new); target.write_bytes(patched)
expected='8570b509576994746edbac46848d3b6f7e1827d9b918d06b433588222c817329'
if hashlib.sha256(base).hexdigest()!='fda541e12414d6c77b41787eaf208e8dae6b462846ad401d4c7b235b8ae2b079' or hashlib.sha256(patched).hexdigest()!=expected: raise SystemExit('candidate base/overlay digest mismatch')
helper=(REPO/'research/doom/v15_cleanup_lazy_pil_successor_a05_20261005/NO_PIL_SITECUSTOMIZE.py').read_bytes(); plan=json.loads((REPO/'research/doom/v15_cleanup_lazy_pil_successor_a05_20261005/RUN_PLAN.json').read_text(encoding='utf-8-sig'))
if hashlib.sha256(helper).hexdigest()!=plan['blocker_sha256']: raise SystemExit('PIL blocker digest mismatch')
(OUT/'sitecustomize.py').write_bytes(helper)
record={'tree':TREE,'manifest_files_verified':len(staged),'source_bytes_verified':sum(x['bytes'] for x in staged),'base_sha256':hashlib.sha256(base).hexdigest(),'patched_sha256':hashlib.sha256(patched).hexdigest(),'helper_sha256':hashlib.sha256(helper).hexdigest(),'candidate_imported':False}
(OUT/'PREPARED.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8'); print(json.dumps(record))
