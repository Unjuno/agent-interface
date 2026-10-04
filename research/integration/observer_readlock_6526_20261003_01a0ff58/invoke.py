"""Exclusive native command receipt. Exit/stdout/stderr/UTC survive failures."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('id')
    parser.add_argument('argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
    root = Path('commands') / args.id
    root.mkdir(parents=True, exist_ok=False)
    receipt = {'argv': argv, 'cwd_role': 'study_root', 'started_utc': utc(), 'state': 'sent'}
    (root / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    try:
        result = subprocess.run(argv, capture_output=True, timeout=60)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
        receipt['state'] = 'completed'
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code = error.stdout or b'', error.stderr or b'', 124
        receipt['state'] = 'timeout; direct child killed by subprocess; descendants require reconciliation'
    (root / 'stdout.bin').write_bytes(stdout)
    (root / 'stderr.bin').write_bytes(stderr)
    receipt.update(finished_utc=utc(), exit_code=code,
                   stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                   stderr_sha256=hashlib.sha256(stderr).hexdigest())
    (root / 'receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))
    sys.stdout.flush()
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    sys.exit(code)


if __name__ == '__main__':
    main()
