"""Read-only reproduction; never start the scientific runner."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
from restore import restore


def verify():
    root = Path(__file__).resolve().parent
    if not (root/'RESULT_PACK.json').is_file():
        raise ValueError('complete results not published')
    with tempfile.TemporaryDirectory(prefix='g8m2-review-') as temp:
        dest = Path(temp)/'retained'
        count = restore(dest)
        for script, saved, args in [('audit.py','AUDIT.json',[]),
                                    ('audit.py','CONTROLS.json',['--controls'])]:
            proc = subprocess.run([sys.executable,'-B','-S',script,'.',*args],
                                  cwd=dest,capture_output=True,timeout=30)
            if proc.returncode != 0 or proc.stderr or proc.stdout != (dest/saved).read_bytes():
                raise ValueError('reproduction mismatch '+saved)
        tests = subprocess.run([sys.executable,'-B','-S','-m','unittest','-v','test_solver'],
                               cwd=dest,capture_output=True,timeout=10)
        if tests.returncode != 0:
            raise ValueError('unit failure '+tests.stderr.decode())
        result = json.loads((dest/'AUDIT.json').read_text())
    return {'restored_files':count,'audit_byte_identical':True,'controls_byte_identical':True,
            'unit_methods':8,'unit_exit':tests.returncode,'outcome':result['outcome'],
            'scientific_reruns':0}


if __name__ == '__main__':
    print(json.dumps(verify(),sort_keys=True,indent=2))
