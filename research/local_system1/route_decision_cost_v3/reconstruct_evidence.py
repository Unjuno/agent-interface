import hashlib, io, json, lzma, tarfile
from pathlib import Path
EXPECTED='7fe175f9b4983dd21767745c6b23efc4405938ee48652ea15421d17ca8c35a2f'
MANIFEST='MANIFEST.json'
def main():
    m=json.loads(Path(MANIFEST).read_text())
    for x in m['files']:
        b=Path(x['path']).read_bytes()
        if len(b)!=x['bytes'] or hashlib.sha256(b).hexdigest()!=x['sha256']:
            raise SystemExit('manifest mismatch: '+x['path'])
    files=[x['path'] for x in m['files']]+[MANIFEST]
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w',format=tarfile.PAX_FORMAT) as tf:
        for f in sorted(files):
            b=Path(f).read_bytes(); ti=tarfile.TarInfo(f); ti.size=len(b); ti.mtime=0; ti.uid=0; ti.gid=0; ti.uname=''; ti.gname=''; ti.mode=0o644
            tf.addfile(ti,io.BytesIO(b))
    comp=lzma.compress(buf.getvalue(),format=lzma.FORMAT_XZ,preset=9|lzma.PRESET_EXTREME)
    got=hashlib.sha256(comp).hexdigest()
    if got!=EXPECTED: raise SystemExit(f'archive SHA mismatch: {got}')
    Path('route_decision_cost_v3_evidence.tar.xz').write_bytes(comp)
    print(f'PASS_RECONSTRUCT {len(comp)} {got}')
if __name__=='__main__': main()
