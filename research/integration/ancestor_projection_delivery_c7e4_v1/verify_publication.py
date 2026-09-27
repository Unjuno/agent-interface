"""Restore byte-exact evidence; re-audit, never rerun the consumed GUI pilot."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
from unpack import restore


def main() -> int:
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='ancestor4317-review-') as temp:
        target = Path(temp) / 'study'
        restoration = restore(source, target)
        for name in ('REPORT.md', 'PROOF.md', 'ancestry_policy.py', 'LOCAL_FREEZE.json'):
            if (source / 'original' / name).read_bytes() != (target / name).read_bytes():
                raise AssertionError('readable original copy mismatch: ' + name)
        process = subprocess.run([sys.executable, '-B', str(target / 'verify_readonly.py')],
                                 cwd=target, capture_output=True, timeout=120)
        if process.returncode != 0 or process.stderr or process.stdout != (source / 'READONLY_CHECK.json').read_bytes():
            raise AssertionError('read-only reconstruction mismatch: ' + process.stderr.decode(errors='replace'))
        report = json.loads(process.stdout)
        if report['allocation_verdict'] != 'HOLD_INCOMPLETE_30_CASE_LOCAL_PILOT':
            raise AssertionError('historical HOLD changed')
        print(json.dumps({'decision': 'PASS_COMPLETE_STOP_EVIDENCE_RECONSTRUCTION',
                          'scientific_verdict': report['allocation_verdict'],
                          'restoration': restoration, 'byte_identical_audit_outputs': True,
                          'new_gui_cases': 0, 'new_policy_workers': 0, 'scientific_reruns': 0},
                         indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
