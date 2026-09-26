"""Publication-only verification; never invokes a measurement runner."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
from restore import restore

root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='m7q3-readonly-') as tmp:
    out = Path(tmp) / 'original'
    result = restore(root, out)
    cmd = [sys.executable, '-S', '-B', str(out / 'verify_readonly.py')]
    process = subprocess.run(cmd, capture_output=True, timeout=40)
    if process.returncode != 0 or process.stderr:
        raise RuntimeError('RETAINED_AUDIT_FAILED:' + process.stderr.decode(errors='replace'))
    report = json.loads(process.stdout)
    if not (report['audit_byte_identical'] and report['controls_rejected'] == 12
            and report['new_measurement_workers'] == 0):
        raise RuntimeError('RETAINED_AUDIT_DISAGREEMENT')
    result.update(audit=report, readonly_exit=process.returncode,
                  original_manifest_sha256=hashlib.sha256((out/'SHA256SUMS.json').read_bytes()).hexdigest())
    print(json.dumps(result, indent=2, sort_keys=True))
