"""Verify and safely unpack the retained local evidence; no GUI/model execution."""
import argparse
import io
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def unpack(destination: str) -> None:
    here = Path(__file__).resolve().parent
    manifest = json.loads((here / 'EVIDENCE_MANIFEST.json').read_text())
    chunks = []
    for name, spec in sorted(manifest['parts'].items()):
        chunk = (here / name).read_bytes()
        if len(chunk) != spec['size'] or hashlib.sha256(chunk).hexdigest() != spec['sha256']:
            raise ValueError('archive part digest mismatch')
        chunks.append(chunk)
    archive = b''.join(chunks)
    if hashlib.sha256(archive).hexdigest() != manifest['archive_sha256']:
        raise ValueError('archive digest mismatch')
    dest = Path(destination).resolve()
    if dest.exists():
        raise FileExistsError('destination must not exist')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:xz') as src:
        for member in src.getmembers():
            name = PurePosixPath(member.name)
            if not member.isfile() or name.is_absolute() or '..' in name.parts or str(name) != member.name:
                raise ValueError('unsafe archive member')
            if member.name in files or member.size > 4_000_000:
                raise ValueError('duplicate or oversized member')
            content = src.extractfile(member).read()
            if len(content) != member.size:
                raise ValueError('member size mismatch')
            files[member.name] = content
    actual = {n: {'size': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for n, b in files.items()}
    if actual != manifest['members'] or sum(len(b) for b in files.values()) > 8_000_000:
        raise ValueError('member manifest mismatch or total size exceeded')
    dest.mkdir()
    for name, content in files.items():
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as out:
            out.write(content)
    print(json.dumps({'decision': 'PASS_EVIDENCE_EXTRACTION', 'files': len(files),
                      'bytes': sum(len(b) for b in files.values())}, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    unpack(parser.parse_args().out)
