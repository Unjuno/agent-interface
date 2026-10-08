import base64,hashlib,json,pathlib
p=pathlib.Path(__file__).parent;m=json.loads((p/'SOURCE_ARCHIVE.json').read_text());x=base64.b64decode(''.join((p/f).read_text().strip() for f in m['parts']));assert len(x)==m['archive_bytes'] and hashlib.sha256(x).hexdigest()==m['archive_sha256'];(p/'SOURCE.tar.xz').write_bytes(x);print(m['archive_sha256'])

