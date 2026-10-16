"""Read-only pre-freeze environment receipt; no phase cells or inputs."""
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

def digest(path):
    p = Path(path).resolve()
    return {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

packages = ["xvfb", "libx11-6", "libxext6", "libxfont2", "libxcb1"]
versions = subprocess.check_output(["dpkg-query", "-W", "-f=${Package}=${Version}\n", *packages], text=True)
ldd = subprocess.check_output(["ldd", "/usr/bin/Xvfb"], text=True)
files = {"/usr/bin/Xvfb", sys.executable, "/usr/lib/aarch64-linux-gnu/libX11.so.6"}
for line in ldd.splitlines():
    for field in line.split():
        if field.startswith("/") and Path(field).is_file():
            files.add(field)
print(json.dumps({"kind": "ENVIRONMENT_ONLY_NO_SCIENTIFIC_CELLS",
    "python": sys.version, "uname": list(os.uname()), "platform": platform.platform(),
    "uid": os.getuid(), "gid": os.getgid(), "packages": versions, "xvfb_ldd": ldd,
    "binaries": [digest(p) for p in sorted(files)],
    "cgroups": {n: Path("/sys/fs/cgroup", n).read_text().strip()
                for n in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")},
    "cpu_stat": Path("/sys/fs/cgroup/cpu.stat").read_text(),
    "input_events": 0, "model_calls": 0}, sort_keys=True))
