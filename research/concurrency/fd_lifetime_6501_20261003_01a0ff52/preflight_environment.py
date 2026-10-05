"""Environment-only construction; no FD/cancellation comparison or formal call."""
import hashlib
import json
import pathlib
import platform
import sys
import threading

exe = pathlib.Path(sys.executable).resolve()
module = pathlib.Path(threading.__file__)
print(json.dumps({'python':platform.python_version(),'machine':platform.machine(),
                  'system':platform.system(),'kernel':platform.release(),
                  'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
                  'threading_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),
                  'cpu_max':pathlib.Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
                  'memory_max':pathlib.Path('/sys/fs/cgroup/memory.max').read_text().strip()}))
