import base64, gzip, io, pathlib, tarfile
root=pathlib.Path(__file__).parent
parts=sorted((root/"source").glob("part*.b64"))
b64="".join(p.read_text() for p in parts)
raw=base64.b64decode(b64)
out=root/"reconstructed_source"
out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode="r:gz") as tf:
    tf.extractall(out)
print(out)
