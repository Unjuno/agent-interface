"""Restore exact retained bytes and audit them; never execute the candidate."""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def restore(base, destination):
    require(not destination.exists(), 'destination already exists')
    manifest = json.loads((base / 'ARCHIVES.json').read_text())
    require(manifest['format'] == 'bp7822-a03-lossless-v1', 'manifest format')
    require(len(manifest['files']) == 31, 'member denominator')
    restored = {}
    for archive in manifest['archives']:
        pieces = []
        for part in archive['parts']:
            require(Path(part['path']).name == part['path'], 'part path')
            raw = (base / part['path']).read_bytes()
            require(len(raw) == part['bytes'] and hashlib.sha256(raw).hexdigest() == part['sha256'], 'part identity')
            pieces.append(raw)
        packed = b''.join(pieces)
        require(len(packed) == archive['bytes'] and hashlib.sha256(packed).hexdigest() == archive['sha256'], 'archive identity')
        decoder = lzma.LZMADecompressor()
        data = decoder.decompress(packed, max_length=4_000_001)
        require(decoder.eof and not decoder.unused_data and len(data) <= 4_000_000, 'archive expansion')
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as stream:
            members = stream.getmembers()
            require(len(members) == archive['members'], 'archive member count')
            for member in members:
                path = PurePosixPath(member.name)
                require(member.isfile() and not path.is_absolute() and '..' not in path.parts, 'regular relative member required')
                require(member.name not in restored and member.name in manifest['files'], 'unexpected/duplicate member')
                value = stream.extractfile(member).read()
                item = manifest['files'][member.name]
                require(len(value) == item['bytes'] and hashlib.sha256(value).hexdigest() == item['sha256'], 'member identity')
                restored[member.name] = value
    require(set(restored) == set(manifest['files']), 'missing members')
    destination.mkdir()
    for name, value in restored.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(value)
    return len(restored)


def verify():
    with tempfile.TemporaryDirectory(prefix='bp7822-a03-readonly-') as parent:
        path = Path(parent) / 'restored'
        count = restore(ROOT, path)
        freeze = json.loads((path / 'FREEZE.json').read_text())
        for name, digest in freeze['sha256'].items():
            require(hashlib.sha256((path / name).read_bytes()).hexdigest() == digest, 'frozen source')
        for role in ('candidate', 'auditor'):
            receipt = json.loads((path / ('results/' + role + '.execution.json')).read_text())
            require(type(receipt['returncode']) is int and receipt['returncode'] == 0, 'role exit')
            for kind in ('stdout', 'stderr'):
                require(hashlib.sha256((path / ('results/' + role + '.' + kind)).read_bytes()).hexdigest() == receipt[kind + '_sha256'], 'role bytes')
        result = subprocess.run([sys.executable, '-S', '-B', 'audit.py', 'results/RAW.jsonl.xz'], cwd=path, capture_output=True, timeout=30)
        require(result.returncode == 0 and not result.stderr, 're-audit failure')
        require(result.stdout == (path / 'results/auditor.stdout').read_bytes(), 'audit not byte-identical')
        tests = subprocess.run([sys.executable, '-S', '-B', '-m', 'unittest', '-v', 'test_oracle'], cwd=path, capture_output=True, timeout=30)
        require(tests.returncode == 0, tests.stderr.decode(errors='replace'))
        print(json.dumps({'restored_files': count, 'source_pins': len(freeze['sha256']), 'audit_byte_identical': True, 'unit_tests': 10, 'candidate_reruns': 0}, sort_keys=True))


if __name__ == '__main__':
    verify()
