"""Restore and re-audit saved bytes only. Never invokes probe or run_matrix."""
from __future__ import annotations
import argparse,base64,hashlib,io,json,subprocess,sys,tarfile,tempfile
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent
EXPECTED_ARCHIVE='ff4305159cbe58cb946bb2e9664683293df7797b95f1990e8f34e13acff29dc3'

def payload(folder:Path)->dict[str,bytes]:
    m=json.loads((folder/'EVIDENCE_PARTS.json').read_text())
    pieces=[]
    for part in m['parts']:
        name=part['file']
        if Path(name).name!=name:raise ValueError('BAD_PART_PATH')
        b=(folder/name).read_bytes()
        if hashlib.sha256(b).hexdigest()!=part['sha256']:raise ValueError('PART_DIGEST')
        pieces.append(base64.b64decode(b.strip(),validate=True))
    b=b''.join(pieces)
    if len(b)!=29644 or hashlib.sha256(b).hexdigest()!=EXPECTED_ARCHIVE:raise ValueError('ARCHIVE_IDENTITY')
    files={}
    with tarfile.open(fileobj=io.BytesIO(b),mode='r:xz') as t:
        for item in t:
            name=PurePosixPath(item.name)
            if not item.isfile() or name.is_absolute() or '..' in name.parts or item.name in files:raise ValueError('BAD_MEMBER')
            if item.size>2_000_000:raise ValueError('MEMBER_TOO_LARGE')
            f=t.extractfile(item)
            if f is None:raise ValueError('MISSING_MEMBER_DATA')
            files[item.name]=f.read()
    if len(files)!=255:raise ValueError('MEMBER_COUNT')
    manifest=json.loads(files['MANIFEST.json'])
    if set(manifest)!=set(files)-{'MANIFEST.json'}:raise ValueError('MANIFEST_COVERAGE')
    for name,digest in manifest.items():
        if hashlib.sha256(files[name]).hexdigest()!=digest:raise ValueError('MEMBER_DIGEST:'+name)
    return files

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('OUTPUT_EXISTS')
    files=payload(HERE)
    a.output.mkdir(parents=True,exist_ok=False)
    for name,b in files.items():
        path=a.output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    root=a.output.resolve()
    freeze=json.loads((root/'FREEZE.json').read_text())
    for name,digest in freeze['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('FREEZE:'+name)
    audit=subprocess.run([sys.executable,'-S','-B',str(root/'audit.py'),str(root)],capture_output=True,timeout=15)
    if audit.returncode or audit.stderr or audit.stdout!=(root/'AUDIT.json').read_bytes():raise ValueError('AUDIT_MISMATCH')
    # Controls regenerate only mutated copies from already saved records.
    # Use a separate tree without the retained mutation-output directory.
    with tempfile.TemporaryDirectory(prefix='j6q8-saved-controls-') as tmp:
        controlroot=Path(tmp)/'evidence';controlroot.mkdir()
        for name,b in files.items():
            if name.startswith('controls/'):continue
            path=controlroot/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
        controls=subprocess.run([sys.executable,'-S','-B',str(controlroot/'controls.py'),str(controlroot)],capture_output=True,timeout=15)
        if controls.returncode or controls.stderr or controls.stdout!=(root/'CONTROLS.json').read_bytes():raise ValueError('CONTROLS_MISMATCH')
    result={'saved_members':len(files),'manifest_entries':len(files)-1,'frozen_files':len(freeze['files']),'audit_stdout_identical':True,'controls_stdout_identical':True,'subject_invocations':0,'native_servers_started':0}
    (root/'RESTORATION_CHECK.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
