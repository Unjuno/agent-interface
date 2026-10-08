import base64,gzip,io,pathlib,tarfile
p=pathlib.Path(__file__).with_name("SOURCE_BUNDLE.tar.gz.b64")
gz=base64.b64decode(p.read_text().strip())
out=pathlib.Path(__file__).with_name("reconstructed_source");out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(gzip.decompress(gz)),mode="r:") as tf: tf.extractall(out)
print(out)
