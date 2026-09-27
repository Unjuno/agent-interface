"""Offline publication verification; never runs scientific actors."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from restore import restore

root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='j2c8-review-') as parent:
    out=Path(parent)/'evidence'
    count=restore(root,out)
    frozen=json.loads((out/'FREEZE.json').read_text())['files']
    for name,digest in frozen.items():
        if (root/name).read_bytes()!=(out/name).read_bytes() or hashlib.sha256((out/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('frozen source mismatch')
    for name,args in [('AUDIT.json',[]),('CONTROLS.json',['--controls'])]:
        p=subprocess.run([sys.executable,'-B',str(out/'audit.py'),str(out),'formal',*args],capture_output=True,timeout=10)
        if p.returncode or p.stderr or p.stdout!=(out/name).read_bytes():
            raise ValueError('raw reaudit mismatch: '+name)
    print(json.dumps({'files_restored':count,'frozen_files_equal':len(frozen),'audit_byte_identical':True,'controls_byte_identical':True,'scientific_actor_runs':0},sort_keys=True))
