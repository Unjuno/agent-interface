"""Frozen ordinary construction matrix, exclusive output, no retries."""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import candidate

HERE = Path(__file__).resolve().parent

if __name__ == '__main__':
    freeze_bytes = (HERE / 'FREEZE.json').read_bytes()
    freeze = json.loads(freeze_bytes)
    for path, expected in freeze['sha256'].items():
        if hashlib.sha256((HERE / path).read_bytes()).hexdigest() != expected:
            raise SystemExit('frozen source mismatch: ' + path)
    libs = {name: hashlib.sha256((Path(asyncio.__file__).parent / name).read_bytes()).hexdigest()
            for name in freeze['stdlib_sha256']}
    if platform.python_version() != freeze['python'] or libs != freeze['stdlib_sha256']:
        raise SystemExit('runtime identity mismatch')
    if candidate.WAIT_NS < 2 * time.get_clock_info('monotonic').resolution * 1_000_000_000:
        raise SystemExit('construction timer not eligible on this host')
    output = Path(sys.argv[1])
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        started = datetime.now(timezone.utc).isoformat()
        rows = asyncio.run(candidate.matrix())
        result = {'schema': 'singleflight-waiter-deadline-construction-v1',
                  'python': platform.python_version(), 'started_utc': started,
                  'ended_utc': datetime.now(timezone.utc).isoformat(),
                  'source_sha256': freeze['sha256']['candidate.py'],
                  'stdlib_sha256': libs, 'freeze_sha256': hashlib.sha256(freeze_bytes).hexdigest(),
                  'backend_opened': False, 'input_dispatched': False,
                  'clock': {n: {'resolution': time.get_clock_info(n).resolution,
                               'implementation': time.get_clock_info(n).implementation}
                            for n in ('perf_counter', 'monotonic')}, 'rows': rows}
        text = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n'
        if len(text.encode()) > 1024 * 1024:
            raise SystemExit('output budget exceeded')
        stream.write(text)
    print(json.dumps({'rows': len(rows), 'raw_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
