import base64,hashlib,json,lzma,pathlib
p=pathlib.Path(__file__).parent
m=json.loads((p/'FORMAL_ARCHIVE.json').read_text())
s=''.join((p/f).read_text().strip() for f in m['parts'])
x=base64.b64decode(s)
assert len(x)==m['xz_bytes'] and hashlib.sha256(x).hexdigest()==m['xz_sha256']
r=lzma.decompress(x)
assert len(r)==m['raw_bytes'] and hashlib.sha256(r).hexdigest()==m['raw_sha256']
(p/'FORMAL_RESULT.json').write_bytes(r)
print(m['raw_sha256'])
