import base64,gzip,hashlib,io,json,pathlib,tarfile,sys
root=pathlib.Path(__file__).parent
manifest=json.loads((root/'MANIFEST.json').read_text())
raw=base64.b64decode((root/'FORMAL_BUNDLE.tar.gz.b64').read_text())
assert len(raw)==manifest['bundle']['decoded_size']
assert hashlib.sha256(raw).hexdigest()==manifest['bundle']['decoded_sha256']
data=gzip.decompress(raw)
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else root/'restored')
out.mkdir(parents=True,exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(data),mode='r:') as t:t.extractall(out)
for name,spec in manifest['files'].items():
 b=(out/name).read_bytes()
 assert len(b)==spec['bytes']
 assert hashlib.sha256(b).hexdigest()==spec['sha256']
print(json.dumps({'restored':sorted(manifest['files']),'pass':True},indent=2))
