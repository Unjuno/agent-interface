import base64,hashlib,json,lzma,pathlib,tarfile,io
p=pathlib.Path('.')
m=json.loads((p/'SOURCE_ARCHIVE.json').read_text())
b=base64.b64decode(''.join((p/x).read_text().strip() for x in m['parts']))
assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(b)),mode='r:') as t: t.extractall('reconstructed')
print(m['sha256'])
