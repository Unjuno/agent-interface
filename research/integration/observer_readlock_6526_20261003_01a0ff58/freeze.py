"""Prospective source/native freeze after separate setup controls, before comparison."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import _sqlite3
import sqlite3.dbapi2
import sys


ROOT = Path(__file__).resolve().parent
sources = ['README.md', 'plan.json', 'fixture.sql', 'endpoint.py', 'assay.py',
           'audit.py', 'invoke.py', 'construction_check.py', 'freeze.py', '.gitattributes', 'conftest.py']
native = {'python_exe': Path(sys.executable), 'sqlite_extension': Path(_sqlite3.__file__),
          'sqlite_dll': Path(_sqlite3.__file__).with_name('sqlite3.dll'),
          'python_dll': Path(sys.base_prefix) / f'python{sys.version_info.major}{sys.version_info.minor}.dll',
          'sqlite_module': Path(sqlite3.__file__), 'sqlite_dbapi2': Path(sqlite3.dbapi2.__file__)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


construction = json.loads((ROOT / 'commands/construction/receipt.json').read_bytes())
if construction['state'] != 'completed' or construction['exit_code'] != 0:
    raise RuntimeError('setup/scorer controls did not finish successfully')
obj = {'id': 'observer-readlock-6526-20261003-01a0ff58-C01',
       'created_utc': datetime.now(timezone.utc).isoformat(),
       'worker': '01a0ff58-8f42-73c3-857d-35a2636e7bd3',
       'python_version': sys.version, 'sqlite_version': sqlite3.sqlite_version,
       'platform': platform.platform(), 'backend': 'native Windows sqlite3; private local files',
       'source_sha256': {name: sha(ROOT / name) for name in sources},
       'native_sha256': {name: sha(path) for name, path in native.items()},
       'construction_receipt_sha256': sha(ROOT / 'commands/construction/receipt.json'),
       'comparison_invocations': 1, 'retained_raw_audit_invocations': 1,
       'comparison_retries': 0, 'formal_gui_allocation_used': False,
       'output': 'first', 'source_commit': 'recorded outside source tree after publication',
       'producer_argv': ['python', 'assay.py', '--freeze', 'freeze.json', '--out', 'first'],
       'auditor_argv': ['python', 'audit.py', '--freeze', 'freeze.json', '--out', 'first']}
with (ROOT / 'freeze.json').open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(obj, sort_keys=True, indent=2) + '\n')
print(json.dumps({'freeze_sha256': sha(ROOT / 'freeze.json'), 'source_files': len(sources),
       'native_binary_or_module_pins': len(native), 'comparison_executed': False}))
