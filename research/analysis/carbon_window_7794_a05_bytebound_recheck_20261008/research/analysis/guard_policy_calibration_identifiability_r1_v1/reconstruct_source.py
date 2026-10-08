import base64, pathlib, tarfile
p=pathlib.Path(__file__).with_name("source_bundle.tar.gz.b64")
archive=pathlib.Path(__file__).with_name("source_bundle.tar.gz")
archive.write_bytes(base64.b64decode(p.read_text().strip()))
out=pathlib.Path(__file__).with_name("reconstructed_source")
out.mkdir(exist_ok=True)
with tarfile.open(archive,"r:gz") as tf:
    tf.extractall(out)
print(out)
