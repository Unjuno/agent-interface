import base64,hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parent; run=json.loads((root/'RUN.json').read_text(encoding='utf-8-sig')); man=json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig')); checks={}; roots=['research/live_control','research/doom','research/observation_tiles','research/observation_gating','research/real_apps_v1']
listing=subprocess.run(['git','ls-tree','-r','-z','--full-tree',run['tree'],'--',*roots],check=True,stdout=subprocess.PIPE).stdout; expected=[]
for rec in listing.split(b'\0'):
 if not rec: continue
 meta,path=rec.split(b'\t',1); _,kind,_=meta.decode().split(); name=path.decode()
 if kind=='blob' and name.endswith('.py') and name.count('/')==2 and any(name.startswith(r+'/') for r in roots): expected.append(name)
checks['source-file-set']=sorted(expected)==sorted(x['path'] for x in man['files']) and len(expected)==2013
raw=subprocess.run(['git','cat-file','--batch'],input=b''.join(x['blob'].encode()+b'\n' for x in man['files']),check=True,stdout=subprocess.PIPE).stdout; pos=0; valid=True
for x in man['files']:
 e=raw.index(b'\n',pos); h=raw[pos:e].split(); n=int(h[2]); s=e+1; b=raw[s:s+n]; valid &= h[0].decode()==x['blob'] and h[1]==b'blob' and len(b)==n and hashlib.sha256(b).hexdigest()==x['sha256'] and n==x['bytes']; pos=s+n+1
checks['source-blob-hashes']=valid and pos==len(raw)
baseitem=next(x for x in man['files'] if x['path']=='research/doom/doom_typed_coast_backend_v1.py'); base=subprocess.run(['git','cat-file','blob',baseitem['blob']],check=True,stdout=subprocess.PIPE).stdout; out=[]; moved=inserted=False
for line in base.splitlines(keepends=True):
 if line.lstrip().startswith(b'from PIL import ImageGrab'):
  if moved: raise RuntimeError('duplicate top-level import')
  moved=True; continue
 if b'ImageGrab.grab(xdisplay=self.session.name)' in line:
  if not moved or inserted: raise RuntimeError('capture anchor mismatch')
  nl=b'\r\n' if line.endswith(b'\r\n') else b'\n'; out.append(line[:len(line)-len(line.lstrip())]+b'from PIL import ImageGrab'+nl); inserted=True
 out.append(line)
checks['single-import-relocation']=moved and inserted and hashlib.sha256(base).hexdigest()=='fda541e12414d6c77b41787eaf208e8dae6b462846ad401d4c7b235b8ae2b079' and hashlib.sha256(b''.join(out)).hexdigest()=='8570b509576994746edbac46848d3b6f7e1827d9b918d06b433588222c817329'
helper=(root.parent/'v15_cleanup_lazy_pil_successor_a05_20261005'/'NO_PIL_SITECUSTOMIZE.py').read_bytes(); a05=json.loads((root.parent/'v15_cleanup_lazy_pil_successor_a05_20261005'/'RUN_PLAN.json').read_text(encoding='utf-8-sig')); checks['frozen-blocker-hash']=hashlib.sha256(helper).hexdigest()==a05['blocker_sha256'] and base64.b64decode((root/'BLOCKER.b64').read_text(encoding='ascii'),validate=True)==helper
prep=json.loads((root/'PREPARED.json').read_text()); checks['staging-provenance']=prep['manifest_files_verified']==2013 and prep['candidate_imported'] is False and prep['patched_sha256']=='8570b509576994746edbac46848d3b6f7e1827d9b918d06b433588222c817329'
for mode in ('normal','optimized'):
 for stream in ('stdout','stderr'):
  m=run['modes'][mode][stream]; b=base64.b64decode((root/m['path']).read_text(encoding='ascii'),validate=True); checks[f'{mode}-{stream}-raw']=len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
 err=base64.b64decode((root/run['modes'][mode]['stderr']['path']).read_text(encoding='ascii'),validate=True).decode('utf-8','replace'); checks[f'{mode}-fail-classification']=run['modes'][mode]['exit_code']==1 and run['modes'][mode]['blocker_marker_seen'] and err.count('A05_NO_PIL_BLOCKER_ACTIVE')==1 and err.count('ModuleNotFoundError: PIL blocked by frozen A05 import probe')==8 and err.count('session_v9.py')==8 and 'Ran 47 tests' in err and 'FAILED (errors=8)' in err
result={'schema':'v15-cleanup-lazy-pil-a06-audit-v1','disposition':'PASS_AUDIT_FAIL_SINGLE_IMPORT_RELOCATION_INSUFFICIENT' if all(checks.values()) else 'AUDIT_FAIL','checks':checks,'check_count':len(checks),'source_blobs_checked':len(man['files']),'scope':'read-only Git object, blocker and retained-raw audit; no candidate code imported or rerun'}; (root/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if all(checks.values()) else 1)
