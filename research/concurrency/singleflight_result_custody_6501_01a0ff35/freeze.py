"""Prospective exact source/runtime freeze; never runs the comparison."""
import _asyncio
import asyncio
import asyncio.base_events
import asyncio.events
import asyncio.futures
import asyncio.tasks
import copy
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_pins():
    modules={'_asyncio':_asyncio,'copy':copy,'asyncio':asyncio,
             'asyncio.base_events':asyncio.base_events,'asyncio.events':asyncio.events,
             'asyncio.futures':asyncio.futures,'asyncio.tasks':asyncio.tasks}
    return {'python':platform.python_version(),'implementation':sys.implementation.name,
            'platform':platform.platform(),'machine':platform.machine(),
            'Future_class':asyncio.Future.__module__+'.'+asyncio.Future.__qualname__,
            'Task_class':asyncio.Task.__module__+'.'+asyncio.Task.__qualname__,
            'module_sha256':{name:sha(Path(module.__file__)) for name,module in modules.items()}}


def main():
    root=Path(__file__).resolve().parent
    if (root/'FREEZE.json').exists():raise SystemExit('freeze exists; no replacement')
    git=r'C:\Program Files\Git\cmd\git.exe'
    repo=root.parents[2]
    head=subprocess.check_output([git,'rev-parse','HEAD'],cwd=repo).decode().strip()
    names=['PLAN.md','fixtures.json','candidate.py','audit.py','construction.py','run.py','freeze.py']
    record={'schema':'result-custody-freeze-v1',
            'allocation':'6501-RESULT-CUSTODY-NATIVE-20261003-01a0ff35-A01',
            'worker':'01a0ff35-2ef3-7911-9911-f31862ad642f','policy':'FINAL-v5',
            'source_commit':head,'source_sha256':{name:sha(root/name) for name in names},
            'runtime':runtime_pins(),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'comparative_invocations':0,'audit_invocations':0,'caps':{'candidate':1,'audit':1},
            'retries':0,'outer_timeout_s':10,'max_raw_bytes':1048576,
            'scope':'actual inert JSON/Future custody construction; no prior allocation replay',
            'shared_resources':[],'fleet_deadline':'unavailable; unextended'}
    with (root/'FREEZE.json').open('xb') as file:
        file.write((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps({'source_commit':head,'source_pins':len(names),'runtime':record['runtime']},sort_keys=True))


if __name__=='__main__':main()
