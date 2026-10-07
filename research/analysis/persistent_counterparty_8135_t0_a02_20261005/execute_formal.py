#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
for command in (["git", "fetch", "origin", "main"], [sys.executable, "-B", str(ROOT/"prepare_freeze.py")], [sys.executable, "-B", str(ROOT/"run_formal.py")]):
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
