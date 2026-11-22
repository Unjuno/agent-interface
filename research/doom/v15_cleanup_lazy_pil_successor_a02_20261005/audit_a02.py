import base64,hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parent; run=json.loads((root/'RUN.json').read_text(encoding='utf-8-sig')); man=json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig')); checks={}
req=b''.join(x['blob'].encode()+b'\n' for x in man['files']); raw=subprocess.run(['git','cat-file','--batch'],input=req,check=True,stdout=subprocess.PIPE).stdout; pos=0; valid=True
for x in man['files']:
 e=raw.index(b'\n',pos); h=raw[pos:e].split(); n=int(h[2]); s=e+1; b=raw[s:s+n]; valid &= h[0].decode()==x['blob'] and h[1]==b'blob' and len(b)==n and hashlib.sha256(b).hexdigest()==x['sha256'] and n==x['bytes']; pos=s+n+1
checks['source-blob-hashes']=valid and pos==len(raw) and len(man['files'])==1998
base_item=next(x for x in man['files'] if x['path']=='research/doom/doom_typed_coast_backend_v1.py'); base=subprocess.run(['git','cat-file','blob',base_item['blob']],check=True,stdout=subprocess.PIPE).stdout; lines=base.splitlines(keepends=True); out=[]; moved=inserted=False
for line in lines:
 if line.lstrip().startswith(b'from PIL import ImageGrab'):
  if moved: raise RuntimeError('duplicate import')
  moved=True; continue
 if b'ImageGrab.grab(xdisplay=self.session.name)' in line:
  if not moved or inserted: raise RuntimeError('anchor mismatch')
  nl=b'\r\n' if line.endswith(b'\r\n') else b'\n'; out.append(line[:len(line)-len(line.lstrip())]+b'from PIL import ImageGrab'+nl); inserted=True
 out.append(line)
checks['single-import-relocation']=moved and inserted and hashlib.sha256(base).hexdigest()==run['patch_base_sha256'] and hashlib.sha256(b''.join(out)).hexdigest()==run['patch_overlay_sha256']
checks['expanded-closure-files']=all(any(x['path']==p for x in man['files']) for p in ('research/observation_tiles/tile_transport.py','research/observation_gating/exact_gate.py'))
for mode in ('normal','optimized'):
 for stream in ('stdout','stderr'):
  m=run[mode][stream]; b=base64.b64decode((root/m['path']).read_text(encoding='ascii'),validate=True); checks[f'{mode}-{stream}-raw']=len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
 err=base64.b64decode((root/run[mode]['stderr']['path']).read_text(encoding='ascii'),validate=True).decode('utf-8','replace'); checks[f'{mode}-stop-classification']=run[mode]['exit_code']==1 and run[mode]['tests']==47 and run[mode]['errors']==8 and err.count("ModuleNotFoundError: No module named 'image_artifact'")==8
result={'schema':'v15-cleanup-lazy-pil-a02-audit-v1','disposition':'PASS_AUDIT_STOP_INCOMPLETE_IMPORT_CLOSURE' if all(checks.values()) else 'AUDIT_FAIL','checks':checks,'check_count':len(checks),'source_blobs_checked':len(man['files']),'scope':'read-only Git object/raw audit; no candidate import or test execution'}; (root/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if all(checks.values()) else 1)
