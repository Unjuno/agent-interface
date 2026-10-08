import base64,hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parent; run=json.loads((root/'RUN.json').read_text(encoding='utf-8-sig')); man=json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig')); checks={}; roots=run['roots']
listing=subprocess.run(['git','ls-tree','-r','-z','--full-tree',run['tree'],'--',*roots],check=True,stdout=subprocess.PIPE).stdout; expected=[]
for rec in listing.split(b'\0'):
 if not rec: continue
 meta,path=rec.split(b'\t',1); _,kind,_=meta.decode().split(); name=path.decode()
 if kind=='blob' and name.endswith('.py') and name.count('/')==2 and any(name.startswith(x+'/') for x in roots): expected.append(name)
checks['source-file-set']=sorted(expected)==sorted(x['path'] for x in man['files']) and len(expected)==2013
blobs=subprocess.run(['git','cat-file','--batch'],input=b''.join(x['blob'].encode()+b'\n' for x in man['files']),check=True,stdout=subprocess.PIPE).stdout; pos=0; valid=True
for x in man['files']:
 e=blobs.index(b'\n',pos); h=blobs[pos:e].split(); n=int(h[2]); s=e+1; b=blobs[s:s+n]; valid &= h[0].decode()==x['blob'] and h[1]==b'blob' and len(b)==n and hashlib.sha256(b).hexdigest()==x['sha256'] and n==x['bytes']; pos=s+n+1
checks['source-blob-hashes']=valid and pos==len(blobs)
base_item=next(x for x in man['files'] if x['path']==run['patched_path']); base=subprocess.run(['git','cat-file','blob',base_item['blob']],check=True,stdout=subprocess.PIPE).stdout; out=[]; moved=inserted=False
for line in base.splitlines(keepends=True):
 if line.lstrip().startswith(b'from PIL import ImageGrab'):
  if moved: raise RuntimeError('duplicate top-level import')
  moved=True; continue
 if b'ImageGrab.grab(xdisplay=self.session.name)' in line:
  if not moved or inserted: raise RuntimeError('capture anchor mismatch')
  nl=b'\r\n' if line.endswith(b'\r\n') else b'\n'; out.append(line[:len(line)-len(line.lstrip())]+b'from PIL import ImageGrab'+nl); inserted=True
 out.append(line)
checks['single-import-relocation']=moved and inserted and hashlib.sha256(base).hexdigest()==run['base_sha256'] and hashlib.sha256(b''.join(out)).hexdigest()==run['patched_sha256']
for mode in ('normal','optimized'):
 for stream in ('stdout','stderr'):
  m=run['modes'][mode][stream]; b=base64.b64decode((root/m['path']).read_text(encoding='ascii'),validate=True); checks[f'{mode}-{stream}-raw']=len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
 err=base64.b64decode((root/run['modes'][mode]['stderr']['path']).read_text(encoding='ascii'),validate=True).decode('utf-8','replace'); checks[f'{mode}-pass-classification']=run['modes'][mode]['exit_code']==0 and run['modes'][mode]['tests']==47 and run['modes'][mode]['failures']==0 and run['modes'][mode]['errors']==0 and 'Ran 47 tests' in err and 'OK' in err and 'FAILED' not in err
result={'schema':'v15-cleanup-lazy-pil-a04-audit-v1','disposition':'PASS_AUDIT_SYNTHETIC_REGRESSION_WITH_PILLOW_PRESENT' if all(checks.values()) else 'AUDIT_FAIL','checks':checks,'check_count':len(checks),'source_blobs_checked':len(man['files']),'scope':'read-only Git object/raw audit; no candidate import or test execution'}; (root/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if all(checks.values()) else 1)
