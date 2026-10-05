#!/usr/bin/env python3
"""Fetch, freeze, recheck exact main, then run the one-shot formal allocation."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).parent.resolve()
for cmd in (["git","fetch","origin","main"],[sys.executable,"-B",str(ROOT/"prepare_freeze.py")],[sys.executable,"-B",str(ROOT/"run_formal.py")]):
    result=subprocess.run(cmd,cwd=ROOT)
    if result.returncode: raise SystemExit(result.returncode)
