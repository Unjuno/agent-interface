#!/usr/bin/python3
"""Task command invoked by the real interactive terminal, never by controller."""
import json
import os
from pathlib import Path
import sys
import time

p = Path(os.environ['AI_TASK_JOURNAL'])
parent = Path('/proc/'+str(os.getppid())+'/stat').read_text()
row = {'argv':sys.argv[1:], 'pid':os.getpid(), 'ppid':os.getppid(),
       'parent_ppid':int(parent.rsplit(')',1)[1].split()[1]),
       'stdin_tty':os.isatty(0), 'stdout_tty':os.isatty(1),
       'term':os.environ.get('TERM'), 'display':os.environ.get('DISPLAY'),
       'started_ns':time.monotonic_ns()}
fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
try:
    os.write(fd, (json.dumps(row)+'\n').encode())
    os.fsync(fd)
finally:
    os.close(fd)
done = {'effect_committed_ns':time.monotonic_ns(), 'pid':os.getpid(), 'argv':sys.argv[1:]}
temporary = p.with_suffix('.done.tmp')
temporary.write_text(json.dumps(done)+'\n')
temporary.replace(p.with_suffix('.done.json'))
print('RECORDED', *sys.argv[1:], flush=True)
