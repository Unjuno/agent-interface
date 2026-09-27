"""Restore exact retained JSON in a temporary directory and audit, never rerun trials."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical-only', action='store_true',
                        help='report current runtime/workflow drift without changing historical evidence')
    args = parser.parse_args()
    runtime_drift = []
    freeze = json.loads((HERE / 'FREEZE.json').read_text())
    for path, expected in freeze['sources'].items():
        current = ROOT / path
        matches = current.is_file() and sha(current.read_bytes()) == expected
        if not matches:
            if args.historical_only and path.startswith(('runtime/', '.github/')):
                runtime_drift.append(path)
            else:
                raise ValueError('frozen evidence source mismatch: ' + path)
    manifest = json.loads((HERE / 'RECORD_ARCHIVES.json').read_text())
    outputs = {}
    with tempfile.TemporaryDirectory(prefix='static-validation-review-') as td:
        for label in ['engineering']:
            entry = manifest[label]
            encoded = b''.join((HERE / part).read_bytes().strip() for part in entry['parts']) + b'\n'
            if sha(encoded) != entry['encoded_sha256']:
                raise ValueError('encoded record mismatch')
            raw_compressed = base64.b64decode(encoded.strip(), validate=True)
            dec = zlib.decompressobj()
            raw = dec.decompress(raw_compressed, 1048577)
            if len(raw) > 1048576 or not dec.eof or dec.unused_data or dec.unconsumed_tail:
                raise ValueError('invalid or oversized record archive')
            if len(raw) != entry['raw_bytes'] or sha(raw) != entry['raw_sha256']:
                raise ValueError('raw record mismatch')
            path = Path(td) / (label + '.json')
            path.write_bytes(raw)
            for script, name in [('audit.py', 'AUDIT.json'), ('controls.py', 'CONTROLS.json')]:
                result = subprocess.run([sys.executable, '-S', '-B', str(HERE / script), str(path)],
                                        capture_output=True, timeout=10)
                expected = (HERE if label == 'engineering' else HERE / 'development') / name
                if result.returncode or result.stderr or result.stdout != expected.read_bytes():
                    raise ValueError(label + ' failed exact ' + name + ' reproduction')
            outputs[label] = {'raw_sha256': sha(raw), 'exact_audit_and_controls': True}
    print(json.dumps({'status': 'PASS_READONLY_RECONSTRUCTION', 'frozen_sources': len(freeze['sources']),
                      'new_engineering_trials': 0, 'records': outputs,
                      'current_runtime_drift': runtime_drift}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
