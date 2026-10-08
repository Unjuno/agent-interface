import argparse,hashlib,json,pathlib
ap=argparse.ArgumentParser(); ap.add_argument('root'); a=ap.parse_args(); root=pathlib.Path(a.root)
rows=[]
for p in sorted(x for x in root.rglob('*') if x.is_file() and x.name!='MANIFEST.json'):
 b=p.read_bytes(); rows.append({'path':str(p.relative_to(root)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
out={'files':rows,'file_count':len(rows)}
(root/'MANIFEST.json').write_text(json.dumps(out,indent=2,sort_keys=True))
print(json.dumps({'file_count':len(rows)},sort_keys=True))
