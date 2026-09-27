"""One retained CLI-review matrix. Never run from CI or to restore old evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from io_data import inputs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODES = ((), ('--compact',), ('--compact', '--report-refs'))


def identities():
    frozen = json.loads((HERE / 'FREEZE.json').read_text())['files']
    found = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in frozen}
    if found != frozen:
        raise ValueError('source/input freeze mismatch')
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--construction', action='store_true')
    args = parser.parse_args()
    # The directory is the exclusive allocation marker; partials remain on failure.
    args.output.mkdir(parents=True, exist_ok=False)
    before = identities()
    env = dict(os.environ)
    for name in ('DISPLAY', 'WAYLAND_DISPLAY', 'PYTHONPATH', 'PYTHONHOME'):
        env.pop(name, None)
    env['PYTHONPATH'] = str(ROOT)
    started = time.monotonic_ns()
    with (args.output / 'rows.jsonl').open('x') as journal:
        for case in inputs(HERE):
            if args.construction and case['id'] not in ('h02', 'h04', 'image_missing'):
                continue
            raw = case['raw'].encode('utf-8')
            for route in ('file', 'stdin'):
                for mode, flags in enumerate(MODES):
                    with tempfile.TemporaryDirectory(prefix='review-r4k6-') as td:
                        path = Path(td) / 'report.json'
                        path.write_bytes(raw)
                        argv = [sys.executable, '-S', '-B', '-m', 'runtime.cli_v1',
                                'review', '--report', str(path) if route == 'file' else '-',
                                '--run-directory', td, *flags]
                        begin = time.monotonic_ns()
                        with subprocess.Popen(argv, cwd=td, env=env, stdin=subprocess.PIPE,
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as child:
                            try:
                                stdout, stderr = child.communicate(raw if route == 'stdin' else b'', timeout=5)
                            except BaseException:
                                child.kill()
                                stdout, stderr = child.communicate()
                                (args.output / 'STOP.json').write_text(json.dumps({
                                    'case': case['id'], 'route': route, 'mode': mode,
                                    'pid': child.pid, 'exit': child.returncode,
                                    'stdout': stdout.decode('utf-8', 'replace'),
                                    'stderr': stderr.decode('utf-8', 'replace')}))
                                raise
                            end = time.monotonic_ns()
                            row = {'case': case['id'], 'route': route, 'mode': mode,
                                   'argv': argv, 'cwd': td, 'pid': child.pid,
                                   'started_ns': begin, 'ended_ns': end, 'exit': child.returncode,
                                   'stdin': raw.decode() if route == 'stdin' else '',
                                   'stdout': stdout.decode('utf-8'), 'stderr': stderr.decode('utf-8'),
                                   'input_sha256': hashlib.sha256(raw).hexdigest(),
                                   'input_unchanged': path.read_bytes() == raw,
                                   'directory_files': sorted(p.name for p in Path(td).iterdir())}
                            journal.write(json.dumps(row, sort_keys=True) + '\n')
                            journal.flush()
    rows = [json.loads(line) for line in (args.output / 'rows.jsonl').read_text().splitlines()]
    result = {'schema': 'review-compilation-matrix-r4k6', 'count': len(rows),
              'started_ns': started, 'ended_ns': time.monotonic_ns(),
              'source_before': before, 'source_after': identities(), 'rows': rows}
    (args.output / 'RECORDS.json').write_text(json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n')
    print(json.dumps({'records': len(rows), 'new_native_dispatches': 0}))


if __name__ == '__main__':
    main()
