#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).parent.resolve()
for cmd in (["git","fetch","origin","main"],[sys.executable,"-B",str(ROOT/"prepare_freeze.py")],[sys.executable,"-B",str(ROOT/"run_formal.py")]):
    r=subprocess.run(cmd,cwd=ROOT)
    if r.returncode:raise SystemExit(r.returncode)
