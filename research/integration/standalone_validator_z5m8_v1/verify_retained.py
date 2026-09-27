"""Restore exact observations and deterministic artifact; never run the matrix."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    encoded = b''.join((HERE / 'raw_parts' / f'{i:02d}.txt').read_bytes() for i in range(8))
    record = json.loads((HERE / 'RECORDS.json').read_text())
    if hashlib.sha256(encoded).hexdigest() != record['encoded_sha256']:
        raise ValueError('encoded record identity differs')
    inflater = zlib.decompressobj()
    raw = inflater.decompress(base64.b64decode(encoded.strip(), validate=True), 34289)
    if (not inflater.eof or inflater.unused_data or inflater.unconsumed_tail or
            len(raw) != record['raw_bytes'] or len(raw) != 34288 or
            hashlib.sha256(raw).hexdigest() != record['raw_sha256']):
        raise ValueError('original raw records cannot be reconstructed')
    baseline = json.loads((HERE / 'BASELINE.json').read_text())
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = base / 'source'
        for row in baseline['sources']:
            src = ROOT / row['path']
            data = src.read_bytes()
            if hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('upstream source identity differs')
            target = source / row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        # Build from a no-Git snapshot to reproduce the ORIGINAL local artifact.
        # This is archive reconstruction, not execution of the validator.
        builder = runpy.run_path(str(ROOT / 'runtime/distribution_v2/build_validator.py'))
        out = base / 'records'
        out.mkdir()
        builder['build'](source, out / 'validator.pyz', out / 'artifact.json', out / 'artifact.sha256')
        if (out / 'artifact.json').read_bytes() != (HERE / 'artifact.json').read_bytes():
            raise ValueError('artifact manifest differs')
        shutil.copyfile(out / 'validator.pyz', out / 'replica.pyz')
        (out / 'RAW.jsonl').write_bytes(raw)
        shutil.copyfile(HERE / 'LAUNCHER.json', out / 'LAUNCHER.json')
        audit = load_module('retained_audit', HERE / 'audit.py').audit(out)
        actual = (json.dumps(audit, indent=2, sort_keys=True) + '\n').encode()
        if actual != (HERE / 'AUDIT.json').read_bytes() or audit['errors']:
            raise ValueError('original frozen audit differs')
        print(json.dumps({'decision': 'PASS_READONLY_RECONSTRUCTION',
                          'records': 32, 'raw_bytes': len(raw),
                          'audit_checks': audit['checks'],
                          'artifact_bytes': (out / 'validator.pyz').stat().st_size,
                          'artifact_sha256': hashlib.sha256((out / 'validator.pyz').read_bytes()).hexdigest(),
                          'validation_matrix_reruns': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
