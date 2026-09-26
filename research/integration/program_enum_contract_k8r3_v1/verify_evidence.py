"""Restore and audit retained k8r3 evidence; never run measure.py or a backend."""
import argparse
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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def restore(source, destination):
    meta = json.loads((source / 'EVIDENCE.json').read_text())
    parts = []
    for name, expected in sorted(meta['parts'].items()):
        raw = (source / name).read_bytes()
        if sha(raw) != expected:
            raise ValueError('part identity mismatch: ' + name)
        parts.append(raw.strip())
    packed = base64.b64decode(b''.join(parts), validate=True)
    if len(packed) != meta['bytes'] or sha(packed) != meta['sha256']:
        raise ValueError('archive identity mismatch')
    decoder = lzma.LZMADecompressor()
    unpacked = decoder.decompress(packed, max_length=8_388_609)
    if len(unpacked) > 8_388_608 or not decoder.eof or decoder.unused_data:
        raise ValueError('archive expansion mismatch')
    with tarfile.open(fileobj=io.BytesIO(unpacked)) as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(names) != meta['members'] or len(set(names)) != len(names):
            raise ValueError('member cardinality mismatch')
        payloads = {}
        for member in members:
            name = PurePosixPath(member.name)
            if not member.isfile() or name.is_absolute() or '..' in name.parts:
                raise ValueError('only relative regular members are accepted')
            payloads[member.name] = archive.extractfile(member).read()
    manifest = json.loads(payloads['MANIFEST.json'])
    if set(payloads) != set(manifest) | {'MANIFEST.json'}:
        raise ValueError('manifest membership mismatch')
    for name, expected in manifest.items():
        if sha(payloads[name]) != expected:
            raise ValueError('member digest mismatch: ' + name)
    destination.mkdir(exist_ok=False)
    for name, raw in payloads.items():
        out = destination / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
    return len(manifest)


def verify(root):
    freeze = json.loads((root / 'study/FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError('frozen source mismatch: ' + name)
    for name in ('audit', 'controls'):
        run = subprocess.run([sys.executable, '-S', '-B', str(root/'study'/f'{name}.py'),
                              str(root/'retained-01')], capture_output=True, timeout=15)
        if run.returncode or run.stderr or run.stdout != (root/f'{name.upper()}.json').read_bytes():
            raise ValueError('retained audit mismatch: ' + name)
    launcher = json.loads((root/'LAUNCHER.json').read_text())
    if type(launcher['exit']) is not int or launcher['exit'] != 0 or launcher['timeout'] is not False:
        raise ValueError('original launcher did not complete')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='k8r3-verify-') as temp:
        out = args.out.resolve() if args.out else Path(temp)/'restored'
        count = restore(source, out)
        verify(out)
    print(json.dumps({'status':'PASS_RETAINED_RECONSTRUCTION','members':count,
                      'measurement_reruns':0}, sort_keys=True))


if __name__ == '__main__':
    main()
