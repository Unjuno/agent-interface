import base64,lzma,tarfile,io,sys
from pathlib import Path
src=Path(__file__).with_name('SOURCE.tar.xz.b64')
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False)
raw=lzma.decompress(base64.b64decode(src.read_text().strip()))
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
    for m in tf.getmembers():
        if not m.isfile() or '/' in m.name or m.name in ('','.','..'): raise SystemExit('unsafe member')
        (out/m.name).write_bytes(tf.extractfile(m).read())
