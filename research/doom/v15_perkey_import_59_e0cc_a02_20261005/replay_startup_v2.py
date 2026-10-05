"""Materialize retained sources, then rerun the finite startup-selection check."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path, help='new directory; must not exist')
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    manifest = json.loads((package / 'source-manifest.json').read_text())
    payloads = {}
    for path, record in manifest['files'].items():
        relative = Path(path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('invalid source path')
        data = (package / 'source-snapshots' / (path + '.txt')).read_bytes()
        if hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('source hash mismatch: ' + path)
        payloads[path] = data
    args.output.mkdir(parents=True, exist_ok=False)
    source = (args.output / 'source').resolve()
    for path, data in payloads.items():
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    outcomes = []
    for route in ('v12-perkey', 'v15-default', 'v15-perkey'):
        command = [sys.executable, '-B', str(package / 'probe_startup_v2.py'),
                   str(source), str((args.output / route).resolve()), route]
        result = subprocess.run(command, capture_output=True, timeout=20)
        (args.output / (route + '.stdout.txt')).write_bytes(result.stdout)
        (args.output / (route + '.stderr.txt')).write_bytes(result.stderr)
        outcomes.append({'route': route, 'exit_code': result.returncode})
        if result.returncode:
            break
    (args.output / 'run-status.json').write_text(json.dumps(outcomes, indent=2) + '\n')
    return int(any(row['exit_code'] for row in outcomes))


if __name__ == '__main__':
    raise SystemExit(main())
