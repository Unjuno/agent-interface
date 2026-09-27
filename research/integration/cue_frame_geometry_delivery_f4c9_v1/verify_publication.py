"""Verify this delivery using only the frozen read-only study verifier."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from restore import restore

HERE = Path(__file__).resolve().parent


def main():
    meta = json.loads((HERE / 'CAPSULE.json').read_bytes())
    with tempfile.TemporaryDirectory(prefix='geometry4323-review-') as tmp:
        destination = Path(tmp) / 'study'
        result = restore(destination)
        for name in meta['readable_originals']:
            if (HERE / 'original' / name).read_bytes() != (destination / name).read_bytes():
                raise ValueError('readable original mismatch: ' + name)
        process = subprocess.run([sys.executable, '-B', str(destination / 'verify.py')],
                                 capture_output=True, timeout=30)
        if process.returncode != 0 or process.stderr:
            raise RuntimeError('frozen verifier failed: ' + process.stdout.decode(errors='replace'))
        audit = json.loads(process.stdout)
        if (audit['status'] != 'PASS_READONLY_RECONSTRUCTION' or audit['errors']
                or audit['files'] != 472 or audit['controls_replayed'] != 12
                or audit['audit_byte_identical'] is not True):
            raise ValueError('frozen verification result')
    print(json.dumps({'status': 'PASS_COMPLETE_GEOMETRY_DELIVERY', 'restore': result,
                      'frozen_verification': audit, 'gui_runs': 0,
                      'scientific_reruns': 0}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
