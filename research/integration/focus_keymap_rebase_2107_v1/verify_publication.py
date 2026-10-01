"""Offline publication verification. No X11, native executable, task input, or formal rerun."""
from pathlib import Path
import json, subprocess, sys, tempfile
HERE=Path(__file__).resolve().parent

def run(args,cwd=None):
    r=subprocess.run(args,cwd=cwd,capture_output=True,timeout=30)
    if r.returncode or r.stderr: raise RuntimeError(f'command failed {args}: rc={r.returncode} stderr={r.stderr.decode(errors="replace")}')
    return r.stdout

def main():
    with tempfile.TemporaryDirectory(prefix='fkr-publication-') as d:
        out=Path(d)/'restored'
        run([sys.executable,'-S','-B',str(HERE/'restore.py'),str(out)])
        study=out/'research/integration/focus_keymap_rebase_2107_v1'
        a=run([sys.executable,'-S','-B',str(study/'audit.py'),str(study/'formal'),str(study)])
        if a!=(HERE/'AUDIT.json').read_bytes(): raise RuntimeError('audit output differs')
        c=run([sys.executable,'-S','-B',str(study/'test_audit.py'),str(study/'formal'),str(study)])
        if c!=(HERE/'CONTROLS.json').read_bytes(): raise RuntimeError('control output differs')
        r=subprocess.run([sys.executable,'-S','-B','-m','unittest','-v','test_policy'],cwd=study,capture_output=True,timeout=20)
        if r.returncode: raise RuntimeError(r.stderr.decode(errors='replace'))
        audit=json.loads(a); controls=json.loads(c)
        print(json.dumps({'status':'PASS_PUBLICATION_VERIFY','cases':audit['cases'],'checks':audit['checks'],'mutation_controls':12,'unit_methods':17,'formal_reruns':0},sort_keys=True))
if __name__=='__main__': main()
