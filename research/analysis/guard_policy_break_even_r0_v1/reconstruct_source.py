import base64, gzip, io, pathlib, tarfile
p=pathlib.Path(__file__).with_name("source_bundle.tar.gz.b64")
raw=base64.b64decode(p.read_text())
out=pathlib.Path(__file__).with_name("reconstructed_source")
out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode="r:gz") as tf:
    tf.extractall(out)
print(out)
