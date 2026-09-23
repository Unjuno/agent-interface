import base64,gzip,hashlib,io,pathlib,tarfile
root=pathlib.Path(__file__).parent
encoded=(root/'SOURCE_BUNDLE.tar.gz.b64').read_bytes()
gz=base64.b64decode(encoded)
expected_gz='8926e9ca0771578bcae1d30ba8d6dc5a7608d55aa86bda63503f7a3885c364d5'
if hashlib.sha256(gz).hexdigest()!=expected_gz: raise SystemExit('source gzip sha mismatch')
tar=gzip.decompress(gz)
with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
    for m in tf.getmembers():
        if pathlib.PurePosixPath(m.name).is_absolute() or '..' in pathlib.PurePosixPath(m.name).parts: raise SystemExit('unsafe path')
    tf.extractall(root/'restored_source')
print(expected_gz)
