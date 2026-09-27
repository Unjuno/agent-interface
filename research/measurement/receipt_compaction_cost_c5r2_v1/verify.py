"""Restore saved text evidence and rerun only raw auditors, never measurements."""
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
LIMIT = 8 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or str(p) != name or any(x in ('', '.', '..') for x in p.parts):
        raise ValueError('noncanonical member name')
    return p


def restore(root, destination):
    manifest = json.loads((root / 'EVIDENCE.json').read_bytes())
    if manifest['format'] != 'c5r2-json-files-xz-v1':
        raise ValueError('format')
    if not 0 < manifest['decoded_bytes'] <= LIMIT or len(manifest['members']) > 200:
        raise ValueError('extent')
    chunks = []
    for part in manifest['parts']:
        name = safe_name(part['path'])
        data = (root / name).read_bytes()
        if len(data) != part['bytes'] or sha(data) != part['sha256']:
            raise ValueError('part identity')
        chunks.append(data)
    blob = b''.join(chunks)
    if len(blob) != manifest['archive_bytes'] or sha(blob) != manifest['archive_sha256']:
        raise ValueError('archive identity')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    data = decoder.decompress(blob, max_length=LIMIT + 1)
    if not decoder.eof or decoder.unused_data or len(data) != manifest['decoded_bytes']:
        raise ValueError('decoded extent')
    members = json.loads(data)
    if set(members) != set(manifest['members']) or set(members) & set(manifest['sources']):
        raise ValueError('member inventory')
    output = {}
    for name, text in members.items():
        safe_name(name)
        raw = text.encode('utf-8')
        record = manifest['members'][name]
        if len(raw) != record['bytes'] or sha(raw) != record['sha256']:
            raise ValueError('member identity')
        output[name] = raw
    for name, wanted in manifest['sources'].items():
        safe_name(name)
        raw = (root / name).read_bytes()
        if sha(raw) != wanted:
            raise ValueError('source identity')
        output[name] = raw
    destination.mkdir(exist_ok=False)
    for name, raw in output.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(raw)
    return len(output)


def verify():
    with tempfile.TemporaryDirectory(prefix='c5r2-verify-') as tmp:
        out = Path(tmp) / 'restored'
        count = restore(ROOT, out)
        checks = []
        for script, retained in (('audit.py', 'AUDIT'), ('controls.py', 'CONTROLS')):
            p = subprocess.run([sys.executable, '-S', '-B', script, 'formal'], cwd=out,
                               capture_output=True, timeout=20)
            if (p.returncode != 0 or p.stdout != (out / (retained + '.json')).read_bytes()
                    or p.stderr != (out / (retained + '.stderr')).read_bytes()):
                raise ValueError('read-only reproduction:' + script)
            checks.append({'script': script, 'exit': p.returncode, 'stdout_sha256': sha(p.stdout)})
        for i in range(6):
            if (out / ('outer-' + str(i) + '.exit')).read_text() != '0\n':
                raise ValueError('original runner exit')
        print(json.dumps({'restored_files': count, 'checks': checks, 'measurement_workers_started': 0}, indent=2))


if __name__ == '__main__':
    verify()
