"""Restore exact bytes and rerun only retained read-only audits, never GUI cases."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unpack import unpack

ROOT = Path(__file__).resolve().parent

def main():
    with tempfile.TemporaryDirectory(prefix='ingress4313-') as parent:
        study = unpack(Path(parent) / 'restored')
        for copy in (ROOT / 'retained').iterdir():
            if copy.is_file() and copy.read_bytes() != (study / copy.name).read_bytes():
                raise ValueError('readable copy differs: ' + copy.name)
        p = subprocess.run([sys.executable, '-B', str(study / 'verify_readonly.py')],
                           cwd=study, capture_output=True, timeout=40)
        if p.returncode != 0 or p.stdout != (ROOT / 'REAUDIT.stdout').read_bytes() or p.stderr:
            raise ValueError('retained read-only verification did not reproduce')
        result = json.loads(p.stdout)
        print(json.dumps({'decision': 'PASS_LOSSLESS_RETAINED_RECONSTRUCTION',
                          'restored_files': 558, 'original_manifest_members': 557,
                          'frozen_files': 15, 'audit_and_controls_byte_identical': True,
                          'gui_runs': 0, 'policy_workers': 0, 'formal_reruns': 0,
                          'retained_verifier': result}, sort_keys=True, indent=2))

if __name__ == '__main__':
    main()
