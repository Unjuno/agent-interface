"""Reconstruct frozen sources only. This command never runs a GUI or experiment."""
import base64, hashlib, json, lzma, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE_XZ_SHA256='62ab47f22332550c6fb0ee5b25c59b2d2d0382759eb20112e0da3e1362522c5c'
SOURCE_BLOBS=['eb9e1a6e3ec996a39708999fe7d676d72b875110','9c7fb9441b2e368d55fea6525bf35a050f8798e5','09fe61400f08d2a7378c0a22147b839bf77d7c88','fc4e1577d99cdd1e66ea883f4c64dcc6110e9a33']
def unpack(destination):
    chunks=[]
    for i,expected in enumerate(SOURCE_BLOBS):
        b=(ROOT/f'source.part{i:02}.b64').read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        if actual!=expected:raise ValueError('source chunk identity')
        chunks.append(b.strip())
    packed=base64.b64decode(b''.join(chunks),validate=True)
    if hashlib.sha256(packed).hexdigest()!=SOURCE_XZ_SHA256:raise ValueError('source archive identity')
    files=json.loads(lzma.decompress(packed));freeze=json.loads(files['freeze.json'])
    for name,text in files.items():
        if Path(name).name!=name or not isinstance(text,str):raise ValueError('unsafe source name/type')
        expected=freeze['sources'].get(name)
        if expected and hashlib.sha256(text.encode()).hexdigest()!=expected:raise ValueError('source content identity')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    for name,text in files.items():(destination/name).write_text(text,encoding='utf-8')
    return {'source_files':len(files),'source_hashes_verified':len(freeze['sources']),'task':freeze['task']}
if __name__=='__main__':print(json.dumps(unpack(sys.argv[1]),sort_keys=True))
