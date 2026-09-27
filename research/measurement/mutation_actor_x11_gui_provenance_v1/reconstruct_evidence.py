import base64,gzip,hashlib,io,json,tarfile,pathlib
root=pathlib.Path(__file__).resolve().parent
man=json.loads((root/"EVIDENCE_MANIFEST.json").read_text())
chunks=[]
for p in man["parts"]:
    b=(root/p["name"]).read_bytes()
    assert len(b)==p["bytes"]
    assert hashlib.sha256(b).hexdigest()==p["sha256"]
    chunks.append(b.decode("ascii").strip())
combined=("".join(chunks)+"\n").encode("ascii")
assert hashlib.sha256(combined).hexdigest()==man["archive_base64_sha256"]
gz=base64.b64decode(combined)
assert hashlib.sha256(gz).hexdigest()==man["archive_gzip_sha256"]
raw=gzip.decompress(gz)
with tarfile.open(fileobj=io.BytesIO(raw),mode="r:") as tf:
    for m in tf.getmembers():
        b=tf.extractfile(m).read(); exp=man["files"][m.name]
        assert len(b)==exp["bytes"] and hashlib.sha256(b).hexdigest()==exp["sha256"]
        p=root/m.name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
print("PASS",len(man["parts"]),len(man["files"]))
