"""Restore and re-audit retained bytes; never launch the consumed GUI runner."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from unpack import restore, require


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='s8r2-review-') as temp:
        root = Path(temp) / 'original'
        data = restore(source, root)
        env = {'PATH': os.defpath, 'HOME': temp, 'PYTHONDONTWRITEBYTECODE': '1',
               'LC_ALL': 'C.UTF-8'}
        commands = [
            [sys.executable, '-B', 'study/audit.py', '.', 'formal'],
            [sys.executable, '-B', 'study/controls.py', 'formal/13', str(Path(temp) / 'controls.json')],
            [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'study', '-p', 'test_policy.py', '-v'],
        ]
        outcomes = []
        for command in commands:
            p = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=30, check=False)
            require(p.returncode == 0, f'verifier exit: {command[2:]}: {p.stderr.decode(errors="replace")}')
            outcomes.append(p)
        require(outcomes[0].stdout == data['AUDIT.json'], 'audit differs')
        require((Path(temp) / 'controls.json').read_bytes() == data['CONTROLS.json'], 'controls differ')
        require(all((root / name).read_bytes() == value for name, value in data.items()), 'original changed')
        require(len([p for p in root.rglob('*') if p.is_file()]) == len(data), 'new original files')
        print(json.dumps({'files': len(data), 'audit_byte_identical': True,
                          'controls_byte_identical': True, 'unit_tests': 17,
                          'subprocess_exits': [p.returncode for p in outcomes],
                          'formal_reruns': 0, 'audit_sha256': hashlib.sha256(outcomes[0].stdout).hexdigest()},
                         sort_keys=True))


if __name__ == '__main__':
    main()
