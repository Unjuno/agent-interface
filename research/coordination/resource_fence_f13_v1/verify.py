"""Bounded data restoration and read-only audit; never starts scientific actors.
Trust the publication directory and temporary parent. Not an adversarial FS sandbox.
"""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

MAX_ARCHIVE = 2_000_000
MAX_EXPANDED = 40_000_000
MAX_MEMBER = 8_000_000
MAX_FILES = 1000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and str(p) == name and all(x not in ('', '.', '..') for x in p.parts) and '\\' not in name and ':' not in name


def unpack(publication, destination):
    pub, dest = Path(publication), Path(destination)
    if dest.exists():
        raise ValueError('destination must be new')
    manifest = json.loads((pub / 'CAPSULE.json').read_text())
    if not 0 < manifest['archive_bytes'] <= MAX_ARCHIVE:
        raise ValueError('archive size')
    chunks = []
    for i, entry in enumerate(manifest['parts']):
        if entry['name'] != f'evidence-{i:02}.bin':
            raise ValueError('part ordering')
        chunk = (pub / entry['name']).read_bytes()
        if len(chunk) != entry['bytes'] or digest(chunk) != entry['sha256']:
            raise ValueError('part identity')
        chunks.append(chunk)
    archive = b''.join(chunks)
    if len(archive) != manifest['archive_bytes'] or digest(archive) != manifest['archive_sha256']:
        raise ValueError('archive identity')
    decoder = lzma.LZMADecompressor(memlimit=150_000_000)
    data = decoder.decompress(archive, max_length=MAX_EXPANDED + 1)
    if not decoder.eof or decoder.unused_data or len(data) > MAX_EXPANDED or len(data) != manifest['tar_bytes']:
        raise ValueError('expansion boundary')
    content = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as tf:
        for member in tf:
            if not member.isfile() or not canonical(member.name) or member.name in content:
                raise ValueError('unsafe or duplicate member')
            if member.size > MAX_MEMBER or len(content) >= MAX_FILES:
                raise ValueError('member bound')
            fileobj = tf.extractfile(member)
            value = fileobj.read(MAX_MEMBER + 1)
            if len(value) != member.size:
                raise ValueError('member size')
            content[member.name] = value
    if len(content) != manifest['member_count'] or sum(map(len, content.values())) != manifest['member_bytes']:
        raise ValueError('member totals')
    if digest(content['MANIFEST.json']) != manifest['inner_manifest_sha256']:
        raise ValueError('manifest identity')
    expected = json.loads(content['MANIFEST.json'])
    if set(content) != set(expected) | {'MANIFEST.json'}:
        raise ValueError('file coverage')
    if any(digest(content[name]) != h for name, h in expected.items()):
        raise ValueError('member identity')
    if digest(content['RECORDS.json']) != manifest['records_sha256']:
        raise ValueError('record identity')
    dest.mkdir()
    for name, value in content.items():
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(value)
    return manifest


def verify(publication):
    pub = Path(publication)
    with tempfile.TemporaryDirectory() as temp:
        restored = Path(temp) / 'study'
        cap = unpack(pub, restored)
        parity = ['REPORT.md', 'RESULT.json', 'AUDIT.json', 'CONTROLS.json'] + [str(p.relative_to(pub)) for p in (pub / 'source').iterdir() if p.is_file()]
        for name in parity:
            if (pub / name).read_bytes() != (restored / name).read_bytes():
                raise ValueError('readable/raw mismatch:' + name)
        receipts = []
        commands = [
            ('AUDIT.json', ['source/audit.py', str(restored), str(restored / 'RECORDS.json')]),
            ('CONTROLS.json', ['source/controls.py', str(restored)])]
        for output, args in commands:
            proc = subprocess.Popen([sys.executable, '-S', '-B'] + args, cwd=restored, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                stdout, stderr = proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                raise ValueError('read-only audit timeout')
            if proc.returncode != 0 or stderr or stdout != (restored / output).read_bytes():
                raise ValueError('read-only audit mismatch:' + output)
            receipts.append({'output': output, 'exit': proc.returncode, 'byte_identical': True})
        return {'decision': 'PASS_READONLY_PUBLICATION_RECONSTRUCTION', 'files': cap['member_count'],
                'member_bytes': cap['member_bytes'], 'source_and_report_parity': len(parity),
                'audits': receipts, 'scientific_actors_started': 0}


if __name__ == '__main__':
    p = Path(__file__).resolve().parent
    if len(sys.argv) == 3 and sys.argv[1] == '--restore':
        print(json.dumps(unpack(p, sys.argv[2]), sort_keys=True, indent=2))
    elif len(sys.argv) == 1:
        print(json.dumps(verify(p), sort_keys=True, indent=2))
    else:
        raise SystemExit('usage: verify.py [--restore NEW_DIRECTORY]')
