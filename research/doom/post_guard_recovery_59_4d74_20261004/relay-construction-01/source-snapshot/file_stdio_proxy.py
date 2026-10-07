"""Preparation-only JSONL file relay; no input or model authority."""
from pathlib import Path
import sys, threading, time

root = Path(sys.argv[1])
def send():
    for i, line in enumerate(sys.stdin.buffer):
        if len(line) > 1048576 or not line.endswith(b'\n'):
            raise ValueError('bounded complete JSONL required')
        path = root / f'request-{i:06d}.jsonl'
        path.with_suffix('.tmp').write_bytes(line)
        path.with_suffix('.tmp').rename(path)
threading.Thread(target=send, daemon=True).start()
index = 0
end = time.monotonic() + 40
while time.monotonic() < end:
    path = root / f'response-{index:06d}.jsonl'
    if path.exists():
        line = path.read_bytes()
        if len(line) > 1048576 or not line.endswith(b'\n'):
            raise ValueError('bounded complete JSONL required')
        sys.stdout.buffer.write(line); sys.stdout.buffer.flush(); index += 1
    else:
        time.sleep(.005)
raise TimeoutError('preparation relay lifetime exceeded')
