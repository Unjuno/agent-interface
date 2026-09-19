import base64,hashlib,io,json,lzma,pathlib,tarfile
p=pathlib.Path('.')
m=json.loads((p/'SOURCE_ARCHIVE.json').read_text())
xz=base64.b64decode(''.join((p/n).read_text().strip() for n in m['parts']))
assert len(xz)==m['xz_bytes'] and hashlib.sha256(xz).hexdigest()==m['xz_sha256']
tar=lzma.decompress(xz);assert len(tar)==m['tar_bytes'] and hashlib.sha256(tar).hexdigest()==m['tar_sha256']
with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as t:t.extractall('reconstructed_source')
print(m['xz_sha256'])
