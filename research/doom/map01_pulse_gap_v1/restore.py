"""Restore retained source and JSON; never launches a game or formal allocation."""
from pathlib import Path, PurePosixPath
import argparse, base64, gzip, hashlib, io, json, lzma, tarfile

PARTS = (
    ('raw-json.part00.b64', '3e1c6ef762e44b353713a7521206a965e3c9d0eab614a7af60f850c017180dac'),
    ('raw-json.part01.b64', '83a7a2576f75877c4475c6831e5fee2a784e38f9477a5eff9a5c13e6756b708d'),
    ('raw-json.part02.b64', '530f984954162e2b1c7c34d6625a8ef4ef83f2d941d066e7d5083b9ec348c940'),
)
XZ_SHA = 'f6195f737c57cda745bd1ce1b847daa86f8d278eb8a3b6f6b61873d918b085ed'
RAW_SHA = '90cc295c0be64c79b7b3efffac8a484acd40ebcb42cc56320a8ddf4c4c55507d'
SOURCE_SHA = '93b1c0a205c8f2a051a9fb4e7b0800933e0c97ca19789dc33f439140d9e5e5c9'
SOURCES = {'audit.py', 'closure.json', 'common.py', 'dispatch_one.py', 'environment.json',
           'prereg.json', 'run_case.py', 'schedule.json', 'test_audit.py'}


def checked(data: bytes, expected: str) -> bytes:
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('retained digest mismatch')
    return data


def restore(package: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError('refuse existing output')
    encoded = ''.join(checked((package/name).read_bytes(), h).decode('ascii').strip()
                      for name, h in PARTS)
    compressed = checked(base64.b64decode(encoded, validate=True), XZ_SHA)
    records = json.loads(checked(lzma.decompress(compressed), RAW_SHA))
    expected = {f'formal/case-{i:02d}/{name}' for i in range(14)
                for name in ('STARTED.json', 'result.json', 'cleanup.json')}
    expected |= {f'formal/case-{i:02d}.invocation.json' for i in range(14)}
    if set(records) != expected or not all(isinstance(v, str) for v in records.values()):
        raise ValueError('JSON closure mismatch')
    source = checked(base64.b64decode((package/'source.tar.gz.b64').read_bytes().strip(),
                                     validate=True), SOURCE_SHA)
    files = dict(records)
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(source)), mode='r:') as archive:
        members = archive.getmembers()
        if len(members) != 9 or {m.name for m in members} != SOURCES:
            raise ValueError('source closure mismatch')
        for member in members:
            if not member.isfile():
                raise ValueError('source is not a regular file')
            files['source/'+member.name] = archive.extractfile(member).read().decode('utf-8')
    for name in files:
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name:
            raise ValueError('unsafe path')
    output.mkdir(parents=True, exist_ok=False)
    for name, text in files.items():
        target = output/name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(text.encode('utf-8'))
    return {'source_files': 9, 'formal_json_files': 56,
            'pngs_present': False, 'full_png_audit': 'requires separate full evidence archive'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    try:
        print(json.dumps(restore(Path(__file__).resolve().parent, a.output), sort_keys=True))
    except (ValueError, OSError, EOFError, tarfile.TarError, lzma.LZMAError) as exc:
        raise SystemExit(str(exc))
