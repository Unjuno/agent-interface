import base64, pathlib, tarfile
src=pathlib.Path(__file__).with_name('source_construction.tar.gz.b64')
out=pathlib.Path(__file__).with_name('source_construction.tar.gz')
out.write_bytes(base64.b64decode(src.read_text().strip()))
with tarfile.open(out,'r:gz') as tf: tf.extractall(pathlib.Path(__file__).with_name('reconstructed'))
print(out)
