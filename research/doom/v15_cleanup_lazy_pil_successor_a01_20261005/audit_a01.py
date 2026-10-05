import base64, hashlib, json, pathlib, subprocess, sys
root=pathlib.Path(__file__).resolve().parent
run=json.loads((root/'RUN.json').read_text(encoding='utf-8-sig'))
man=json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig'))
checks={}
expected=subprocess.run(['git','ls-tree','-r','-z','--full-tree',run['tree'],'--','research/live_control','research/doom'],check=True,stdout=subprocess.PIPE).stdout
expected_paths=[]
for rec in expected.split(b'\0'):
 if not rec: continue
 meta,path=rec.split(b'\t',1); _,kind,_oid=meta.decode().split(); name=path.decode()
 if kind=='blob' and name.endswith('.py') and name.count('/')==2: expected_paths.append(name)
checks['materialized-file-set']=sorted(expected_paths)==sorted(x['path'] for x in man['files']) and man['tree']==run['tree']
requests=b''.join(x['blob'].encode()+b'\n' for x in man['files'])
blobs=subprocess.run(['git','cat-file','--batch'],input=requests,check=True,stdout=subprocess.PIPE).stdout
pos=0; good=True
for item in man['files']:
 end=blobs.index(b'\n',pos); header=blobs[pos:end].split(); size=int(header[2]); start=end+1; data=blobs[start:start+size]
 good &= header[0].decode()==item['blob'] and header[1]==b'blob' and len(data)==size and hashlib.sha256(data).hexdigest()==item['sha256'] and size==item['bytes']
 pos=start+size+1
checks['source-blob-hashes']=good and pos==len(blobs)
base_item=next(x for x in man['files'] if x['path']==run['patched_path'])
base=subprocess.run(['git','cat-file','blob',base_item['blob']],check=True,stdout=subprocess.PIPE).stdout
lines=base.splitlines(keepends=True); patched=[]; moved=inserted=False
for line in lines:
 if line.lstrip().startswith(b'from PIL import ImageGrab'):
  if moved: raise RuntimeError('duplicate top-level PIL import')
  moved=True; continue
 if b'ImageGrab.grab(xdisplay=self.session.name)' in line:
  if not moved or inserted: raise RuntimeError('capture insertion anchor mismatch')
  nl=b'\r\n' if line.endswith(b'\r\n') else b'\n'; patched.append(line[:len(line)-len(line.lstrip())]+b'from PIL import ImageGrab'+nl); inserted=True
 patched.append(line)
checks['single-import-relocation']=moved and inserted and hashlib.sha256(base).hexdigest()==run['base_sha256'] and hashlib.sha256(b''.join(patched)).hexdigest()==run['patched_sha256']
for mode in ('normal','optimized'):
 for stream in ('stdout','stderr'):
  meta=run[mode][stream]; data=base64.b64decode((root/meta['path']).read_text(encoding='ascii'),validate=True)
  checks[f'{mode}-{stream}-raw']=len(data)==meta['bytes'] and hashlib.sha256(data).hexdigest()==meta['sha256']
 stderr=base64.b64decode((root/run[mode]['stderr']['path']).read_text(encoding='ascii'),validate=True).decode('utf-8','replace')
 checks[f'{mode}-stop-classification']=run[mode]['exit_code']==1 and run[mode]['tests']==47 and run[mode]['errors']==8 and stderr.count("ModuleNotFoundError: No module named 'research.observation_tiles'")==8 and 'No module named \'PIL\'' not in stderr
result={'schema':'v15-cleanup-lazy-pil-successor-a01-audit-v1','disposition':'PASS_AUDIT_STOP_INCOMPLETE_SOURCE_CLOSURE' if all(checks.values()) else 'AUDIT_FAIL','checks':checks,'check_count':len(checks),'source_blobs_checked':len(man['files']),'scope':'read-only Git object and captured raw audit; no candidate module imported or test executed'}
(root/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
if not all(checks.values()): sys.exit(1)
