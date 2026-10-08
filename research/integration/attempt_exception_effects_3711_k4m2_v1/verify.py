"""Restore exact saved bytes and audit them; never launch worker.py or run.py."""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
PINNED = {'SOURCE_ARCHIVE.json': '84b52713652b20ea6e1ba3fe2ff20627d2622e8ecb348dcd6045f5beb10fd268',
          'RESULTS_ARCHIVE.json': '384ca9d805a5f3d8efe458c682a1d280e67473337761f65c2872ea9c64145cf7'}
FREEZE = '39ab6d2837419af77ed04ba7fcc0a58b74e90f1c04ff16cf52aa5e219cab527a'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unpack(manifest_name):
    meta = json.loads((HERE / manifest_name).read_bytes())
    pieces = []
    for row in meta['parts']:
        name = PurePosixPath(row['path'])
        if name.is_absolute() or '..' in name.parts:
            raise ValueError('unsafe fragment path')
        data = (HERE / str(name)).read_bytes()
        git = hashlib.sha1(('blob %d\0' % len(data)).encode() + data).hexdigest()
        if len(data) != row['bytes'] or digest(data) != row['sha256'] or git != row['git']:
            raise ValueError('fragment identity mismatch')
        pieces.append(data)
    packed = b''.join(pieces)
    if len(packed) != meta['archive_bytes'] or digest(packed) != PINNED[manifest_name] or meta['archive_sha256'] != PINNED[manifest_name]:
        raise ValueError('archive identity mismatch')
    dec = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = dec.decompress(packed, max_length=16 * 1024 * 1024)
    if not dec.eof or dec.unused_data:
        raise ValueError('oversize or nonterminal archive')
    records = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or str(path) != member.name or member.name in records):
                raise ValueError('unsafe or duplicate archive member')
            records[member.name] = archive.extractfile(member).read()
    if len(records) != meta['members'] or sum(map(len, records.values())) != meta['member_bytes']:
        raise ValueError('member denominator mismatch')
    return records


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -S -B verify.py NEW_OUTPUT_DIRECTORY')
    records = unpack('SOURCE_ARCHIVE.json')
    additional = unpack('RESULTS_ARCHIVE.json')
    if set(records) & set(additional):
        raise ValueError('source/result overlap')
    records.update(additional)
    if digest(records['FREEZE.json']) != FREEZE:
        raise ValueError('freeze identity mismatch')
    frozen = json.loads(records['FREEZE.json'])['files']
    if any(digest(records[name]) != sha for name, sha in frozen.items()):
        raise ValueError('frozen source mismatch')
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=False, exist_ok=False)
    for name, data in records.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    if any((output / name).read_bytes() != data for name, data in records.items()):
        raise ValueError('restored bytes differ')
    invocations = []
    with tempfile.TemporaryDirectory(prefix='k4m2-audit-') as temporary:
        commands = [
            ([sys.executable, '-I', '-B', str(output / 'audit.py'), str(output / 'formal')], 'AUDIT.json'),
            ([sys.executable, '-S', '-B', str(output / 'controls.py'), str(output / 'formal'), str(Path(temporary) / 'mutations')], 'CONTROLS.json'),
            ([sys.executable, '-S', '-B', '-m', 'unittest', '-v', 'test_audit'], None),
        ]
        for command, reference in commands:
            result = subprocess.run(command, cwd=output, capture_output=True, timeout=20)
            if result.returncode != 0 or (reference and result.stdout != records[reference]):
                raise ValueError('saved-data check failed: ' + repr(command))
            invocations.append({'check': reference or 'five_units', 'exit': result.returncode,
                                'stdout_sha256': digest(result.stdout), 'stderr_sha256': digest(result.stderr)})
    if any((output / name).read_bytes() != data for name, data in records.items()):
        raise ValueError('saved bytes changed during audit')
    print(json.dumps({'decision': 'PASS_READONLY_RESTORATION', 'members': len(records),
                      'frozen_files': len(frozen), 'original_outputs_identical': 2,
                      'scientific_reruns': 0, 'checks': invocations}, sort_keys=True))


if __name__ == '__main__':
    main()
