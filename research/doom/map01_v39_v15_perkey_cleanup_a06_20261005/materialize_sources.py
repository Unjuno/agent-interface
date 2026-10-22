import base64,hashlib,json,pathlib,sys,shutil
pkg=pathlib.Path(__file__).parent
out=pathlib.Path(sys.argv[1]); manifest=json.loads((pkg/'source-manifest.json').read_text(encoding='utf-8'))
for rel,pin in manifest['files'].items():
 data=base64.b64decode((pkg/pin['snapshot']).read_bytes().strip(),validate=True)
 if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']: raise SystemExit(f'snapshot mismatch: {rel}')
 dest=out/rel; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
name='map01_v39_v15_perkey_cleanup_a06_20261005'; mirror=out/'research/doom'/name; mirror.mkdir(parents=True,exist_ok=True)
for f in ['candidate.py','audit.py','source-manifest.json','FREEZE.json']:(mirror/f).write_bytes((pkg/f).read_bytes())
shutil.copytree(pkg/'source-snapshots',mirror/'source-snapshots',dirs_exist_ok=True)
print(json.dumps({'source_count':len(manifest['files']),'materialized_root':str(out)}))
