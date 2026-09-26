"""Read-only re-audit of archived observations; starts no scientific receivers."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import restore


def main():
    pub = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='e5d7-readback-') as temp:
        root = Path(temp) / 'study'
        result = restore.unpack(pub, root)
        parity = []
        for name in ('receiver.py', 'run.py', 'audit.py', 'controls.py', 'test_contract.py',
                     'supervise.py', 'PLAN.md', 'ENVIRONMENT.json', 'FREEZE.json',
                     'REPORT.md', 'AUDIT.json', 'CONTROLS.json', 'POST_EXECUTION.json', 'PREFORMAL_READBACK.json'):
            if (pub / name).read_bytes() != (root / name).read_bytes():
                raise ValueError('readable source/evidence parity:' + name)
            parity.append(name)
        result['readable_parity'] = parity
        for script, saved in (('audit.py', 'AUDIT.json'), ('controls.py', 'CONTROLS.json')):
            run = subprocess.run([sys.executable, '-S', '-B', str(root / script), str(root)],
                                 capture_output=True, timeout=25)
            if run.returncode or run.stderr or run.stdout != (root / saved).read_bytes():
                raise ValueError('saved evidence audit mismatch:' + script)
            result[script] = {'returncode': run.returncode, 'byte_identical': True,
                              'sha256': hashlib.sha256(run.stdout).hexdigest()}
        units = subprocess.run([sys.executable, '-S', '-B', str(root / 'test_contract.py')],
                               capture_output=True, timeout=10)
        if units.returncode or b'Ran 8 tests' not in units.stderr or b'OK' not in units.stderr:
            raise ValueError('pure unit regression failure')
        result['pure_unit_methods'] = 8
        exits = []
        for batch in range(6):
            rec = json.loads((root / 'receipts' / f'formal-{batch:02d}.json').read_text())
            if type(rec['returncode']) is not int or rec['returncode'] != 0 or rec['ended_ns'] < rec['started_ns']:
                raise ValueError('batch process receipt')
            output = json.loads((root / 'receipts' / f'formal-{batch:02d}.stdout').read_text())
            if output['status'] != 'COMPLETE' or output['cases'] != 4:
                raise ValueError('outer batch completion')
            exits.append(rec['returncode'])
        result['batch_exits'] = exits
        result['scientific_receiver_runs_started'] = 0
        result['status'] = 'PASS_READONLY_RECONSTRUCTION'
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
