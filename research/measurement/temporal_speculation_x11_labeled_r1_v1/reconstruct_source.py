import base64,hashlib,json,pathlib
p=pathlib.Path(__file__).parent
m=json.loads((p/'SOURCE_ARCHIVE.json').read_text())
s=''.join((p/f).read_text().strip() for f in m['parts'])
b=base64.b64decode(s)
assert len(b)==m['archive_bytes']
assert hashlib.sha256(b).hexdigest()==m['archive_sha256']
(p/'SOURCE.tar.xz').write_bytes(b)
print(m['archive_sha256'])
