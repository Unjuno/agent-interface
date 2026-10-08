import base64,hashlib,json,pathlib
p=pathlib.Path('research/doom/map01_v39_v15_perkey_cleanup_a05_20261005')
m=json.loads((p/'source-manifest.json').read_text(encoding='utf-8'))
for rel,pin in m['files'].items():
 d=base64.b64decode((p/pin['snapshot']).read_bytes().strip(),validate=True)
 dest=pathlib.Path('run/src')/rel
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_bytes(d)
assert all(hashlib.sha256((pathlib.Path('run/src')/rel).read_bytes()).hexdigest()==v['sha256'] for rel,v in m['files'].items())
print(f"materialized {len(m['files'])} pinned modules")
