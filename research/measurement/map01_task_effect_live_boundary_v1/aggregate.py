import argparse,hashlib,json,pathlib,shutil
ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); root=pathlib.Path(a.root); out=pathlib.Path(a.out)
if out.exists(): raise SystemExit('output exists')
out.mkdir(parents=True); rows=[]
for rep in range(3):
 b=root/f'batch-{rep}'; br=json.load(open(b/'RAW.json'))
 if len(br)!=4: raise SystemExit(f'batch {rep} denominator')
 rows.extend(br)
 for r in br:
  src=b/r['case_id']; dst=out/r['case_id']; shutil.copytree(src,dst)
json.dump(rows,open(out/'RAW.json','w'),sort_keys=True,indent=2)
def sh(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files={str(p.relative_to(out)):sh(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
json.dump({'files':files,'count':len(files)},open(out/'MANIFEST.json','w'),sort_keys=True,indent=2)
print(json.dumps({'cases':len(rows),'out':str(out)}))
