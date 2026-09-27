import base64,hashlib,json,pathlib
p=pathlib.Path(__file__).parent;m=json.loads((p/'SOURCE_ARCHIVE.json').read_text());b=base64.b64decode(''.join((p/f).read_text().strip() for f in m['parts']));assert len(b)==m['archive_bytes'] and hashlib.sha256(b).hexdigest()==m['archive_sha256'];(p/'SOURCE.tar.xz').write_bytes(b);print(m['archive_sha256'])
