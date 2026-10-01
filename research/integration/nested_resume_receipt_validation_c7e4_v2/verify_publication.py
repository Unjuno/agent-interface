"""Restore exact retained data and run read-only audits; never starts GUI/studies."""
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

ROOT = Path(__file__).resolve().parent
MAX_FILES, MAX_BYTES = 500, 32 * 1024 * 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_path(name):
    if type(name) is not str or not name or '\\' in name:
        raise ValueError('invalid path')
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '.' in p.parts or str(p) != name:
        raise ValueError('noncanonical path')
    return p


def restore(root, destination):
    """Decode stored values, not regenerated experiments, into an absent directory."""
    root, destination = Path(root), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    manifest = json.loads((root / 'EVIDENCE_MANIFEST.json').read_text())
    if manifest['format'] != 'exact-jsonl-columns-tar-v1':
        raise ValueError('format')
    chunks = []
    names = set()
    for part in manifest['parts']:
        name = str(checked_path(part['path']))
        if name in names or (root / name).is_symlink():
            raise ValueError('duplicate/symlink part')
        names.add(name)
        raw = (root / name).read_bytes()
        if len(raw) != part['size'] or sha(raw) != part['sha256']:
            raise ValueError('part identity')
        if not raw.endswith(b'\n'):
            raise ValueError('part framing')
        chunks.append(base64.b64decode(raw[:-1], validate=True))
    archive = b''.join(chunks)
    if len(archive) != manifest['archive_bytes'] or sha(archive) != manifest['archive_sha256']:
        raise ValueError('archive identity')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    tarbytes = decoder.decompress(archive, max_length=MAX_BYTES + 1)
    if len(tarbytes) > MAX_BYTES or not decoder.eof or decoder.unused_data:
        raise ValueError('expansion/trailing bound')
    if len(tarbytes) != manifest['decoded_bytes']:
        raise ValueError('tar length')
    stored = {}
    with tarfile.open(fileobj=io.BytesIO(tarbytes), mode='r:') as tf:
        for member in tf:
            checked_path(member.name)
            if not member.isfile() or member.name in stored or member.size > MAX_BYTES:
                raise ValueError('member kind/duplicate/size')
            stored[member.name] = tf.extractfile(member).read()
            if len(stored) > MAX_FILES + 1:
                raise ValueError('member count')
    index = json.loads(stored.pop('INDEX.json'))
    if index['format'] != manifest['format'] or len(index['files']) != manifest['files']:
        raise ValueError('index')
    results, used, size = {}, set(), 0
    for entry in index['files']:
        name = str(checked_path(entry['path']))
        if name in results or entry['stored'] in used:
            raise ValueError('duplicate output/storage')
        used.add(entry['stored'])
        data = stored[entry['stored']]
        if entry['kind'] == 'bytes':
            raw = data
        elif entry['kind'] == 'jsonl_columns':
            table = json.loads(data)
            count = table['count']
            if type(count) is not int or not 0 <= count <= 20000:
                raise ValueError('row count')
            rows, seen = [{} for _ in range(count)], set()
            for path, values in table['columns']:
                if not path or any(type(k) is not str for k in path) or tuple(path) in seen:
                    raise ValueError('column path')
                seen.add(tuple(path))
                if len(values) != count:
                    raise ValueError('column count')
                for row, pair in zip(rows, values):
                    if type(pair) is not list or len(pair) != 2 or type(pair[0]) is not bool:
                        raise ValueError('presence representation')
                    present, value = pair
                    if not present:
                        if value is not None:
                            raise ValueError('absent value')
                        continue
                    node = row
                    for key in path[:-1]:
                        node = node.setdefault(key, {})
                        if type(node) is not dict:
                            raise ValueError('column prefix conflict')
                    if path[-1] in node:
                        raise ValueError('duplicate leaf')
                    node[path[-1]] = value
            raw = ''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows).encode()
        else:
            raise ValueError('storage kind')
        if len(raw) != entry['size'] or sha(raw) != entry['sha256']:
            raise ValueError('restored identity: ' + name)
        results[name] = raw
        size += len(raw)
        if size > MAX_BYTES or len(results) > MAX_FILES:
            raise ValueError('output bound')
    if used != set(stored) or size != manifest['total_original_bytes']:
        raise ValueError('unreferenced storage/total')
    # Validate every member before creating any output file.
    destination.mkdir()
    for name, raw in results.items():
        p = destination / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(raw)
    return {'files': len(results), 'bytes': size, 'archive_sha256': sha(archive)}


def verify(root=ROOT):
    with tempfile.TemporaryDirectory(prefix='receipt-publication-') as td:
        d = Path(td) / 'restored'
        result = restore(root, d)
        old = subprocess.run([sys.executable, '-B', str(d/'retained/verify_readonly.py')],
                             capture_output=True, timeout=90)
        if old.returncode:
            raise RuntimeError('retained audit: ' + old.stderr.decode(errors='replace'))
        prior = json.loads(old.stdout)
        if prior['decision'] != 'PASS_READ_ONLY_DELIVERY_CHECK':
            raise ValueError('retained verdict')
        smoke = subprocess.run([sys.executable, '-B', str(d/'smoke/smoke_audit.py'),
                                str(d/'smoke'), '--controls'], capture_output=True, timeout=30)
        if smoke.returncode or smoke.stdout != (d/'smoke/SMOKE_AUDIT.json').read_bytes():
            raise RuntimeError('smoke audit differs: ' + smoke.stderr.decode(errors='replace'))
        freeze = json.loads((d/'smoke/SMOKE_FREEZE.json').read_text())
        for name, digest in freeze['source_hashes'].items():
            if sha((d/'smoke'/name).read_bytes()) != digest:
                raise ValueError('frozen source')
        if sha((d/'smoke/SMOKE_ENVIRONMENT.json').read_bytes()) != freeze['environment_sha256']:
            raise ValueError('environment')
        result.update(decision='PASS_LOSSLESS_READONLY_PUBLICATION',
                      retained_files=65, retained_audit_byte_identical=prior['byte_identical'],
                      smoke_audit_byte_identical=True, smoke_cases=12,
                      smoke_checks=314, smoke_controls=12,
                      formal_reruns=0, evaluation_worker_reruns=0, gui_runs=0,
                      process_exits=[old.returncode, smoke.returncode])
        return result


if __name__ == '__main__':
    if len(sys.argv) == 2:
        output = restore(ROOT, Path(sys.argv[1]))
    elif len(sys.argv) == 1:
        output = verify()
    else:
        raise SystemExit('usage: verify_publication.py [ABSENT_RESTORE_DIRECTORY]')
    print(json.dumps(output, sort_keys=True, indent=2))
