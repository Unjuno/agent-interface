"""Restore and verify reviewed archival evidence; never run scientific actors.

Hashes establish byte identity, not authenticity. Parent directory and checkout
must be trusted and quiescent. This is not an adversarial filesystem sandbox.
"""
from __future__ import annotations
import hashlib
import io
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent
MAX_TAR_BYTES = 8 * 1024 * 1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def canonical(name):
    if type(name) is not str or not name or '\\' in name:
        raise ValueError('invalid path')
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or str(p) != name or name == '.':
        raise ValueError('noncanonical path')
    return p

def decode(data, manifest):
    if len(data) != manifest['archive_bytes'] or digest(data) != manifest['archive_sha256']:
        raise ValueError('archive identity')
    dec = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = dec.decompress(data, max_length=MAX_TAR_BYTES + 1)
    if len(raw) > MAX_TAR_BYTES or not dec.eof or dec.unused_data:
        raise ValueError('archive expansion boundary')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as t:
        for member in t:
            canonical(member.name)
            if not member.isfile() or member.name in files or member.size < 0:
                raise ValueError('nonregular or duplicate member')
            if len(files) >= 270 or member.size > 4 * 1024 * 1024:
                raise ValueError('member bound')
            files[member.name] = t.extractfile(member).read()
    if len(files) != 270 or len(files) != manifest['original_files']:
        raise ValueError('member count')
    if sum(map(len, files.values())) != manifest['original_total_bytes']:
        raise ValueError('member byte count')
    for name, key in [('MANIFEST.json','original_manifest_sha256'),
                      ('FREEZE.json','original_freeze_sha256')]:
        if digest(files[name]) != manifest[key]:
            raise ValueError('original identity: ' + name)
    return files

def restore(checkout, destination):
    manifest = json.loads((checkout / 'ARCHIVE.json').read_text())
    if manifest['schema'] != 'deferred-effect-retained-publication-v1':
        raise ValueError('manifest schema')
    if len(manifest['parts']) != 9:
        raise ValueError('part count')
    data = []
    for i, row in enumerate(manifest['parts']):
        expected = f'evidence/part-{i:02d}.bin'
        if row['path'] != expected:
            raise ValueError('part order')
        p = checkout / expected
        if p.is_symlink() or not p.is_file():
            raise ValueError('part not regular')
        b = p.read_bytes()
        if len(b) != row['bytes'] or digest(b) != row['sha256'] or git_blob(b) != row['git_blob']:
            raise ValueError('part identity: ' + expected)
        data.append(b)
    files = decode(b''.join(data), manifest)
    for p in (checkout / 'readable').iterdir():
        if not p.is_file() or p.read_bytes() != files[p.name]:
            raise ValueError('readable parity')
    destination.mkdir(exist_ok=False)
    for name, b in files.items():
        p = destination.joinpath(*canonical(name).parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(b)
    return manifest

def main():
    try:
        with tempfile.TemporaryDirectory(prefix='deferred-evidence-') as temp:
            dest = Path(temp) / 'original'
            manifest = restore(ROOT, dest)
            env = os.environ.copy()
            for k in ('DISPLAY', 'XAUTHORITY'):
                env.pop(k, None)
            p = subprocess.run([sys.executable, '-S', '-B', 'verify.py'], cwd=dest,
                               env=env, capture_output=True, timeout=30, check=False)
            if p.returncode or p.stderr:
                raise ValueError('original read-only verifier failed')
            expected = (ROOT / 'ORIGINAL_REVALIDATION.json').read_bytes()
            if p.stdout != expected:
                raise ValueError('original reconstruction differs')
            print(json.dumps({'status':'PASS_COMPLETE_RETAINED_RECONSTRUCTION',
                              'archive_sha256':manifest['archive_sha256'],
                              'original_files':270, 'original_member_bytes':3957752,
                              'original_verifier_byte_identical':True,
                              'original_verifier':json.loads(p.stdout),
                              'new_gui_sessions':0, 'new_scientific_runs':0},
                             indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError,
            tarfile.TarError, subprocess.TimeoutExpired) as error:
        print(json.dumps({'status':'HOLD_PUBLICATION_VERIFICATION', 'error':str(error)},
                         sort_keys=True))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
