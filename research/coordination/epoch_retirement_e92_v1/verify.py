"""Bounded data-only restoration followed by audits; never reruns scientific actors."""
from __future__ import annotations
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile


def restore(publication: Path, destination: Path) -> dict:
    if destination.exists():
        raise ValueError('destination must be new')
    meta = json.loads((publication / 'CAPSULE.json').read_text())
    chunks = []
    for item in meta['parts']:
        path = PurePosixPath(item['name'])
        if len(path.parts) != 1 or path.name != item['name']:
            raise ValueError('noncanonical segment name')
        data = (publication / item['name']).read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('segment integrity')
        chunks.append(data)
    packed = b''.join(chunks)
    if len(packed) > 65536 or len(packed) != meta['archive_bytes']:
        raise ValueError('archive size')
    if hashlib.sha256(packed).hexdigest() != meta['archive_sha256']:
        raise ValueError('archive hash')
    decoder = lzma.LZMADecompressor(memlimit=67108864)
    expanded = decoder.decompress(packed, max_length=10485761)
    if len(expanded) > 10485760 or not decoder.eof or decoder.unused_data:
        raise ValueError('expansion bound or trailing data')
    if len(expanded) != meta['expanded_tar_bytes']:
        raise ValueError('expanded size')
    members = {}
    with tarfile.open(fileobj=io.BytesIO(expanded), mode='r:') as archive:
        for item in archive:
            name = PurePosixPath(item.name)
            if (not item.isfile() or name.is_absolute() or '..' in name.parts
                    or str(name) != item.name or '\\' in item.name or item.name in members):
                raise ValueError('unsafe or duplicate member')
            if item.size > 1048576 or len(members) >= 256:
                raise ValueError('member bound')
            members[item.name] = archive.extractfile(item).read()
    if len(members) != meta['members'] or sum(map(len, members.values())) != meta['member_bytes']:
        raise ValueError('membership size')
    manifest_bytes = members['MANIFEST.json']
    if hashlib.sha256(manifest_bytes).hexdigest() != meta['manifest_sha256']:
        raise ValueError('manifest hash')
    manifest = json.loads(manifest_bytes)
    if set(manifest) != set(members) - {'MANIFEST.json'}:
        raise ValueError('member coverage')
    for name, item in manifest.items():
        data = members[name]
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('member integrity')
    destination.mkdir(parents=True)
    for name, data in members.items():
        output = destination / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    return {'members': len(members), 'archive_sha256': meta['archive_sha256']}


def execute_audit(root: Path, phase: str, data: Path) -> bytes:
    indices = '0,1,2,3,4,5' if phase == 'formal' else '0,2,4'
    result = subprocess.run([sys.executable, '-S', '-B', str(root / 'audit.py'),
                             str(root), str(data), indices, phase],
                            capture_output=True, timeout=30)
    if result.stderr or result.returncode not in (0, 1):
        raise ValueError('audit process failure')
    return result.stdout


def verify(publication: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix='e92-verify-') as temporary:
        root = Path(temporary) / 'restored'
        result = restore(publication, root)
        # Published readable sources must match the actual archived frozen sources.
        frozen = json.loads((root / 'FREEZE.json').read_text())
        for name in list(frozen['sha256']) + ['FREEZE.json', 'REPORT.md', 'AUDIT.json', 'RESULT.json']:
            if (publication / name).read_bytes() != (root / name).read_bytes():
                raise ValueError('published source mismatch: ' + name)
        for phase, expected in (('formal', 'AUDIT.json'), ('construction', 'CONSTRUCTION_AUDIT.json')):
            output = execute_audit(root, phase, root / phase)
            if output != (root / expected).read_bytes() or json.loads(output)['errors']:
                raise ValueError('baseline audit mismatch')
            summary = json.loads((root / (phase + '_controls') / 'SUMMARY.json').read_text())
            if not summary['passed'] or len(summary['controls']) != 12:
                raise ValueError('control summary')
            for item in summary['controls']:
                with tempfile.TemporaryDirectory(prefix='e92-mutation-') as directory:
                    copied = Path(directory)
                    for path in (root / phase).glob('*.json'):
                        shutil.copyfile(path, copied / path.name)
                    changed = root / (phase + '_controls') / (item['name'] + '.case.json')
                    shutil.copyfile(changed, copied / (item['case'] + '.json'))
                    output = execute_audit(root, phase, copied)
                expected = root / (phase + '_controls') / (item['name'] + '.audit.json')
                if output != expected.read_bytes() or not json.loads(output)['errors']:
                    raise ValueError('saved mutation mismatch')
        result.update({'baseline_audits': 2, 'saved_controls': 24,
                       'scientific_actor_reruns': 0, 'errors': []})
        return result


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True, indent=2))
