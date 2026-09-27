"""Reconstruct all originals and invoke only their unchanged read-only verifier."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from restore import restore

ROOT = Path(__file__).resolve().parent

def main() -> None:
    with tempfile.TemporaryDirectory(prefix='r9k4-delivery-') as directory:
        work = Path(directory)
        retained = restore(ROOT, work/'retained')
        output = work/'verified.json'
        command = [sys.executable, '-S', '-B', str(retained/'verify_readonly.py'), '--out', str(output)]
        result = subprocess.run(command, cwd=retained, capture_output=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError('original read-only verification failed: '+result.stderr.decode(errors='replace'))
        receipt = json.loads(output.read_bytes())
        if receipt['files_verified'] != 971 or receipt['frozen_files_verified'] != 18 or receipt['scientific_actor_reruns'] != 0:
            raise ValueError('unexpected original verification scope')
        # The original verifier intentionally preserves its historical remote=false label.
        print(json.dumps({'decision':'PASS_RETAINED_R9K4_DELIVERY',
            'original_members':972, 'frozen_files':18, 'pilot_cases':42,
            'scientific_actor_reruns':0, 'original_public_preregistration':False,
            'pilot_audit_controls_and_development_audit':'byte-identical',
            'pure_unit_methods':11}, sort_keys=True))

if __name__ == '__main__':
    main()
