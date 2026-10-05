import json
import os
import pathlib
import select
import sys
import time

payloads = {'healthy': b'{"event":"ready","fixture":"synthetic"}\n',
            'malformed': b'not-json\n', 'array': b'[]\n'}
payload = payloads[sys.argv[1]]
written=os.write(1, payload)
pathlib.Path(sys.argv[2]).write_text(json.dumps(dict(pid=os.getpid(), ppid=os.getppid(),
    emitted_hex=payload.hex(), written=written, monotonic_ns=time.monotonic_ns()))+'\n')
if select.select([sys.stdin], [], [], 4)[0]:
    sys.stdin.buffer.read()
    sys.exit(0)
sys.exit(2)
