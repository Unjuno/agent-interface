"""Foreground parent retaining the actual exit of one bounded batch, no retries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from batch import ROOT, encoded, exclusive, load, verify_freeze


def launch(out, index, mode, freeze):
    freeze_hash = verify_freeze(freeze)
    if index == 0:
        out.mkdir(parents=True, exist_ok=False)
    if (out/'STOP.json').exists():
        raise ValueError('ALLOCATION_ALREADY_STOPPED')
    command = [sys.executable, '-B', str(ROOT/'batch.py'), '--out', str(out),
               '--index', str(index), '--mode', mode, '--freeze', str(freeze)]
    exclusive(out/f'LAUNCH-{index:02d}.json', {'batch': index, 'command': command,
                                            'timeout_s': 25, 'freeze_sha256': freeze_hash})
    receipt = {'batch': index, 'command': command, 'exit': None, 'timed_out': False,
               'started_ns': time.monotonic_ns()}
    stdout = stderr = b''
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=25)
        stdout, stderr = result.stdout, result.stderr
        receipt['exit'] = result.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or b'', error.stderr or b''
        receipt['timed_out'] = True
    receipt['finished_ns'] = time.monotonic_ns()
    receipt['stdout_sha256'] = hashlib.sha256(stdout).hexdigest()
    receipt['stderr_sha256'] = hashlib.sha256(stderr).hexdigest()
    (out/f'BATCH-{index:02d}.stdout').write_bytes(stdout)
    (out/f'BATCH-{index:02d}.stderr').write_bytes(stderr)
    exclusive(out/f'BATCH-{index:02d}.EXECUTION.json', receipt)
    if receipt['exit'] != 0 or receipt['timed_out']:
        if not (out/'STOP.json').exists():
            exclusive(out/'STOP.json', {'batch': index, 'type': 'BATCH_PROCESS_STOP',
                                        'exit': receipt['exit'], 'timed_out': receipt['timed_out']})
        print(json.dumps(receipt, sort_keys=True), flush=True)
        return 2
    batch_count = 1 if mode == 'construction' else 6
    if index == batch_count-1:
        for i in range(batch_count):
            external = load(out/f'BATCH-{i:02d}.EXECUTION.json')
            if external['exit'] != 0 or external['timed_out']:
                raise ValueError('INCOMPLETE_EXTERNAL_EXITS')
        manifest = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}
        exclusive(out/'MANIFEST.json', manifest)
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--index', type=int, required=True)
    parser.add_argument('--mode', choices=('construction', 'formal'), required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(launch(args.out.resolve(), args.index, args.mode, args.freeze.resolve()))
