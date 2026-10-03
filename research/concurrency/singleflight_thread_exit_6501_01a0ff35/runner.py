"""Execute the new eight-condition construction exactly once per output path."""
import asyncio
import hashlib
import json
from pathlib import Path
import platform
import sys
from datetime import datetime, timezone
from mechanism import run_case

async def produce():
    rows = []
    for policy in ('wrapper_terminal', 'future_ack'):
        for schedule in ('stable_pair', 'one_detach', 'early_rejoin', 'post_exit_rejoin'):
            rows.append(await run_case(policy, schedule))
    return rows

def main():
    root = Path(__file__).resolve().parent
    freeze_bytes = (root / 'FREEZE.json').read_bytes()
    freeze = json.loads(freeze_bytes)
    for path, digest in freeze['files'].items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
            raise RuntimeError('source differs from freeze: ' + path)
    if platform.python_version() != freeze['python']:
        raise RuntimeError('interpreter differs from freeze')
    output = Path(sys.argv[1])
    # Reserve before executing: an uncertain outcome cannot be blindly replayed.
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        start = datetime.now(timezone.utc).isoformat()
        rows = asyncio.run(produce())
        end = datetime.now(timezone.utc).isoformat()
        raw = dict(schema='singleflight-thread-exit-v1', freeze_sha256=hashlib.sha256(freeze_bytes).hexdigest(),
            start_utc=start, end_utc=end, python=platform.python_version(), platform=platform.platform(),
            rows=rows, formal_allocation=False)
        json.dump(raw, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'rows': len(rows), 'raw_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))

if __name__ == '__main__':
    main()
