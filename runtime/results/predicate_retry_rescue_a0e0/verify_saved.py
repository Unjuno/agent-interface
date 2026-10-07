"""Verify retained bytes and run the original saved-only oracle, never producers."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'research/concurrency/predicate_retry_deadline_17_20261003_b64b'

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def main():
    count = 0
    for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        target = PACKET / name
        require(target.resolve().is_relative_to(PACKET.resolve()), 'unsafe manifest path')
        require(hashlib.sha256(target.read_bytes()).hexdigest() == digest, name)
        count += 1
    oracle = runpy.run_path(str(PACKET / 'audit_saved.py.txt'), run_name='saved_only')
    with tempfile.TemporaryDirectory(prefix='predicate-retry-saved-') as scratch:
        sources = Path(scratch)
        for name in ('baseline.py', 'outside.py', 'deadline_first.py', 'source_controls.py'):
            shutil.copyfile(PACKET / (name + '.txt'), sources / name)
        for name in ('SPEC.json', 'source-pins.json'):
            shutil.copyfile(PACKET / name, sources / name)
        model = json.loads((PACKET / 'raw/MODEL.json').read_text())
        construction = json.loads((PACKET / 'construction.json').read_text())
        report = oracle['audit_document'](model, construction, sources)
    historical = json.loads((PACKET / 'raw/AUDIT.json').read_text())
    for key, value in report.items():
        require(historical.get(key) == value, 'historical audit mismatch: ' + key)
    require(report['passed'] is True, 'oracle rejected retained data')
    print(json.dumps({'manifest_targets': count, 'saved_only_report': report,
                      'scope': 'saved consistency only; no producers, native run or current product certificate'},
                     indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
