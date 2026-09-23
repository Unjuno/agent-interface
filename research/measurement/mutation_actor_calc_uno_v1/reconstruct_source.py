import base64,gzip,hashlib,io,json,tarfile,pathlib
root=pathlib.Path(__file__).resolve().parent
man=json.loads((root/"SOURCE_MANIFEST.json").read_text())
b64=(root/"source_bundle.b64").read_bytes()
assert hashlib.sha256(b64).hexdigest()==man["archive_base64_sha256"]
gz=base64.b64decode(b64)
assert hashlib.sha256(gz).hexdigest()==man["archive_gzip_sha256"]
raw=gzip.decompress(gz)
with tarfile.open(fileobj=io.BytesIO(raw),mode="r:") as tf:
 for m in tf.getmembers():
  b=tf.extractfile(m).read(); exp=man["source_files"][m.name]
  assert len(b)==exp["bytes"] and hashlib.sha256(b).hexdigest()==exp["sha256"]
  (root/m.name).write_bytes(b)
print("PASS",len(man["source_files"]))
