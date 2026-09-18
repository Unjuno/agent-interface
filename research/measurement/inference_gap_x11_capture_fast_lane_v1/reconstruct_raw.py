import base64,hashlib,json,lzma,pathlib,tarfile,io
p=pathlib.Path('.')
m=json.loads((p/'RAW_ARCHIVE.json').read_text())
b=base64.b64decode(''.join((p/x).read_text().strip() for x in m['parts']))
assert len(b)==m['xz_bytes'] and hashlib.sha256(b).hexdigest()==m['xz_sha256']
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(b)),mode='r:') as t:t.extractall('reconstructed_raw')
print(m['result_sha256'])
