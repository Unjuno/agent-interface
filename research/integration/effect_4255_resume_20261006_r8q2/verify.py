#!/usr/bin/env python3
"""Restore exact retained evidence and reproduce its FAILURE, without X11.
Trusted publication and quiescent private output parent only; not a sandbox.
Requires CPython 3.13, stdlib. Never imports or invokes runner/app/invoke.
"""
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

DIGEST = 'caae7ce12282e03b7cdd410c77f42c5c0eb690c7e5cc06da046b653cf4466021'
MANIFEST = 'f9fa009724d06ccd2197a04be9c599d93ce1c1c31abeb8c8cd05cd0ff673f2fd'
PARTS = ['evidence.%03d.b64' % i for i in range(6)]

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def restore(root, out):
    require(not out.exists(), 'destination exists')
    require(sorted(p.name for p in root.glob('evidence.*.b64')) == PARTS, 'part set')
    text = ''.join((root / p).read_text(encoding='ascii') for p in PARTS)
    require(len(text) == 34760, 'encoded size')
    blob = base64.b64decode(text, validate=True)
    require(len(blob) == 26068 and digest(blob) == DIGEST, 'archive identity')
    decoder = lzma.LZMADecompressor()
    raw = decoder.decompress(blob, max_length=225281)
    require(decoder.eof and not decoder.unused_data and len(raw) == 225280, 'expansion')
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for m in archive:
            p = PurePosixPath(m.name)
            require(m.isfile() and not p.is_absolute() and str(p) == m.name and
                    all(s not in ('.', '..', '') for s in p.parts) and
                    '\\' not in m.name and m.name not in members, 'member path/type')
            require(len(members) < 101 and 0 <= m.size <= 50000, 'member budget')
            members[m.name] = archive.extractfile(m).read()
    require(len(members) == 101 and sum(map(len, members.values())) == 142652, 'member totals')
    require(digest(members['MANIFEST.json']) == MANIFEST, 'manifest identity')
    manifest = json.loads(members['MANIFEST.json'])
    require(set(manifest) == set(members) - {'MANIFEST.json'}, 'manifest set')
    for name, meta in manifest.items():
        require(len(members[name]) == meta['bytes'] and digest(members[name]) == meta['sha256'], name)
    out.mkdir(parents=False)
    for name, data in members.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return manifest

def revalidate(out, manifest):
    for name, expected in json.loads((out/'EXECUTION_FREEZE.json').read_text())['files'].items():
        require(digest((out/name).read_bytes()) == expected, 'freeze:'+name)
    for p in (out/'receipts').glob('*.process.json'):
        r = json.loads(p.read_text())
        for kind in ('stdout', 'stderr'):
            data = (out/'receipts'/(r['stage']+'.'+kind)).read_bytes()
            require(digest(data) == r[kind+'_sha256'] and len(data) == r[kind+'_bytes'], 'receipt')
    for stage in ('formal1', 'formal2'):
        r = json.loads((out/'receipts'/(stage+'.process.json')).read_text())
        require(r['returncode'] == 0 and r['timeout'] is False, 'formal process')
    require(json.loads((out/'receipts/controls.process.json').read_text())['returncode'] == 1, 'control exit')
    upstream = out/'upstream'
    raws = [str(out/f'formal{i}/RAW.jsonl') for i in (1,2)]
    with tempfile.TemporaryDirectory(prefix='effect4255-audit-') as tmp:
        newaudit = Path(tmp)/'audit.json'
        calls = [
            ('audit', [str(upstream/'audit.py'),'--phase','formal','--out',str(newaudit),*raws], 0, out/'receipts/audit.stdout'),
            ('controls', [str(upstream/'test_audit.py'),*raws], 1, out/'receipts/controls.stdout'),
            ('diagnosis', [str(out/'diagnose.py')], 0, out/'DIAGNOSIS.json')]
        for name, args, code, stdout in calls:
            p = subprocess.run([sys.executable,'-B','-S',*args], cwd=upstream,
                               capture_output=True, timeout=10)
            require(p.returncode == code and not p.stderr and p.stdout == stdout.read_bytes(), 'replay:'+name)
        require(newaudit.read_bytes() == (out/'AUDIT.json').read_bytes(), 'audit bytes')
    for name, meta in manifest.items():
        require(digest((out/name).read_bytes()) == meta['sha256'], 'changed:'+name)
    return {'verification':'VERIFIED_RETAINED_FAILURE','restored_files':101,
            'frozen_members':16,'readonly_outputs_reproduced':3,
            'scientific_reruns':0,'original_control_rejections':'11/12',
            'allocation_disposition':'FAIL_FROZEN_AUDIT_CONTROL_GATE'}

def main():
    root = Path(__file__).resolve().parent
    require(sys.version_info[:2] == (3,13), 'CPython 3.13 required for exact reproduction')
    with tempfile.TemporaryDirectory(prefix='effect4255-restore-') as tmp:
        out = Path(tmp)/'evidence'
        manifest = restore(root, out)
        result = revalidate(out, manifest)
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    main()
