"""Probe a built zipapp in a separate isolated interpreter, without a backend."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from probe import specification

CHILD = '''
import json,sys
sys.path.insert(0, sys.argv[1])
from runtime.core_v1 import compiled_gui
if not compiled_gui.__file__.startswith(sys.argv[1]):
    raise RuntimeError('archive import escaped')
spec=json.loads(sys.argv[2]); rows=[]
for value in (True, 1.0, 1):
    calls=[]; index=[0]
    def observe(_):
        index[0]+=1
        return dict(sequence=index[0],captured_ns=0,surface='fixture',predicates={'done':index[0]>1},evidence_ref='frame'+str(index[0]),evidence_digest='digest'+str(index[0]))
    def admit(_):
        return dict(eligible=True,status='revalidated',authorization='fixture-only',expected_sequence=value,valid_until_ns=1000)
    def execute(p):
        calls.append(p)
        return dict(status='completed',action_id='fixture',effect_ref='effect',release=dict(verified=True,keys_down=[],buttons_down=[]))
    result=None; error=None
    try:
        result=compiled_gui.run(spec,dict(observe=observe,admit=admit,execute=execute,verify_effect=lambda _:dict(status='succeeded',evidence_ref='effect'),cancelled=lambda:False),clock=lambda:0)
    except ValueError:
        error='ValueError'
    if type(value) is int:
        valid=error is None and result['outcome']=='TASK_SUCCEEDED' and len(calls)==1
    else:
        valid=error=='ValueError' and not calls
    if not valid:
        raise RuntimeError('packaged sequence boundary failed: '+repr(value))
    rows.append(dict(type=type(value).__name__,value=repr(value),execute_count=len(calls),error=error))
if any(name.startswith('research') for name in sys.modules):
    raise RuntimeError('research dependency imported')
print(json.dumps(dict(status='PASS_ARCHIVE_SEQUENCE_SCOPED',rows=rows)))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    archive = args.archive.resolve()
    result = subprocess.run([sys.executable, '-I', '-B', '-c', CHILD,
        str(archive), json.dumps(specification())], capture_output=True, timeout=20)
    if result.returncode:
        print((result.stdout + result.stderr).decode('utf-8', errors='replace'))
        raise SystemExit(result.returncode)
    report = json.loads(result.stdout)
    report['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as bundle:
        report['module_sha256'] = hashlib.sha256(bundle.read('runtime/core_v1/compiled_gui.py')).hexdigest()
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
