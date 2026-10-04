"""Run original saved-data auditor with fresh output; fail closed under -O."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'research/measurement/timer_diagnostic_6067_linux_20261003_root'

def main():
    if not __debug__:
        raise RuntimeError('STOP: original auditor uses assertions; optimized execution forbidden')
    lines = (PACKET / 'SHA256SUMS').read_text().splitlines()
    for line in lines:
        pin, name = line.split('  ', 1)
        if hashlib.sha256((PACKET / name).read_bytes()).hexdigest() != pin:
            raise ValueError(name)
    previous = sys.argv
    with tempfile.TemporaryDirectory(prefix='timer-saved-audit-') as temporary:
        output = Path(temporary) / 'audit.json'
        try:
            sys.argv = ['auditor_v2.py', str(PACKET / 'output/run-d02'), str(output)]
            with contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(PACKET / 'auditor_v2.py'), run_name='saved_only')
        finally:
            sys.argv = previous
        report = json.loads(output.read_bytes())
    if report != json.loads((PACKET / 'audit-v2.json').read_bytes()):
        raise ValueError('original saved report mismatch')
    print(json.dumps({'manifest_targets': len(lines), 'saved_audit': report,
                      'producer_replays': 0, 'optimized_execution': 'forbidden: original assertions',
                      'scope': 'saved construction consistency only; no native timing or policy adoption'},
                     indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
