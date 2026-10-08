#!/usr/bin/env python3
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
cmd=['gcc','-O2','-Wall','-Wextra','-fPIC','-shared',str(HERE/'native.c'),'-o',str(HERE/'native.so'),'-lX11','-Wl,--build-id=none']
subprocess.run(cmd,check=True)
print(' '.join(cmd))
