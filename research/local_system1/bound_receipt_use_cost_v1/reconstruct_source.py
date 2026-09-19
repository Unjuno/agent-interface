import base64,hashlib,json,lzma,tarfile,io
from pathlib import Path
m=json.loads(Path('SOURCE_ARCHIVE.json').read_text())
s=''.join(Path(f'source.part{i:02d}.b64').read_text().strip() for i in range(1,m['parts']+1))
b=base64.b64decode(s)
assert len(b)==m['archive_bytes'] and hashlib.sha256(b).hexdigest()==m['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(b)),mode='r:') as tf:
    for name,d in m['member_sha256'].items(): assert hashlib.sha256(tf.extractfile(name).read()).hexdigest()==d
Path('source.tar.xz').write_bytes(b)
print('PASS_RECONSTRUCT_SOURCE',len(b),m['archive_sha256'])
