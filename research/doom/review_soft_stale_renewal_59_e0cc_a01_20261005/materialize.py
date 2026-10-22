"""Reconstruct the exact pinned source export without rerunning any tests."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--out', type=Path, default=HERE / 'view')
    args = p.parse_args()
    manifest = json.loads((HERE / 'source-manifest.json').read_text())
    args.out.mkdir(parents=True, exist_ok=False)
    for name, pin in manifest['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('source path escapes export')
        ref = manifest['head'] + ':' + name
        blob = subprocess.check_output(['git', '-C', str(args.repo), 'rev-parse', ref], text=True).strip()
        data = subprocess.check_output(['git', '-C', str(args.repo), 'show', ref])
        if blob != pin['git_blob'] or len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise ValueError('pinned source mismatch: ' + name)
        dest = args.out / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as f:
            f.write(data)
    print(json.dumps({'materialization': 'PASS', 'files': len(manifest['files']),
                      'head': manifest['head'], 'candidate_executions': 0}))

if __name__ == '__main__':
    main()
