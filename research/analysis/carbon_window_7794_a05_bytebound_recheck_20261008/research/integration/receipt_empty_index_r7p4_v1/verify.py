"""Restore bounded exact evidence and re-audit saved rows; never run the subject.

Use a trusted, quiescent publication directory and temporary-directory parent.
Hashes provide integrity, not producer authentication or an adversarial sandbox.
"""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import lzma

ROOT = Path(__file__).resolve().parent


def unpack(data, destination, expected_members):
    if len(data) > 1_000_000:
        raise ValueError('archive size')
    dec = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = dec.decompress(data, max_length=4_000_001)
    if len(raw) > 4_000_000 or not dec.eof or dec.unused_data:
        raise ValueError('archive expansion or trailing data')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if (len(members) != expected_members or len(set(names)) != len(names)
                or any(not m.isfile() or '/' in m.name or '\\' in m.name
                       or m.name in ('', '.', '..') or m.size > 2_000_000
                       for m in members)
                or sum(m.size for m in members) > 3_000_000):
            raise ValueError('members')
        if any((destination / name).exists() for name in names):
            raise ValueError('refuse overwrite')
        for member in members:
            data = archive.extractfile(member).read()
            with (destination / member.name).open('xb') as handle:
                handle.write(data)
    return len(members)


def restore(root, destination):
    destination.mkdir(exist_ok=False)
    total = 0
    for name in ('SOURCE_MANIFEST.json', 'RESULT_MANIFEST.json'):
        manifest = json.loads((root / name).read_text())
        pieces = []
        for part in manifest['parts']:
            if '/' in part['path'] or '\\' in part['path'] or part['path'] in ('.', '..'):
                raise ValueError('part path')
            data = (root / part['path']).read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if (len(data) != part['bytes'] or blob != part['git_blob']
                    or hashlib.sha256(data).hexdigest() != part['sha256']):
                raise ValueError('part identity')
            pieces.append(data)
        data = b''.join(pieces)
        if (len(data) != manifest['archive_bytes']
                or hashlib.sha256(data).hexdigest() != manifest['archive_sha256']):
            raise ValueError('archive identity')
        total += unpack(data, destination, manifest['members'])
    source = json.loads((root / 'SOURCE_MANIFEST.json').read_text())
    if hashlib.sha256((destination / 'FREEZE.json').read_bytes()).hexdigest() != source['freeze_sha256']:
        raise ValueError('freeze identity')
    return total


def main():
    with tempfile.TemporaryDirectory(prefix='receipt-r7p4-') as temp:
        out = Path(temp) / 'restored'
        count = restore(ROOT, out)
        completed = subprocess.run([sys.executable, '-S', '-B', str(out / 'audit.py')],
                                   cwd=out, capture_output=True, timeout=20)
        if (completed.returncode != 0 or completed.stderr
                or completed.stdout != (out / 'AUDIT.json').read_bytes()):
            raise ValueError('saved-data audit differs')
        print(json.dumps({'restored_files': count, 'saved_audit_exact': True,
                          'audit': json.loads(completed.stdout), 'subject_invocations': 0},
                         indent=2))


if __name__ == '__main__':
    main()
