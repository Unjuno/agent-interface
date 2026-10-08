"""Setup/scorer/readonly controls only; does not execute comparative deck."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'construction'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


OUT.mkdir()
records = []
for mode in ('DELETE', 'WAL'):
    db = OUT / (mode.lower() + '.db')
    setup = sqlite3.connect(db, isolation_level=None, timeout=0)
    require(setup.execute('PRAGMA journal_mode=' + mode).fetchone()[0] == mode.lower(), 'journal unsupported')
    setup.executescript((ROOT / 'fixture.sql').read_text(encoding='utf-8'))
    setup.close()
    reader = sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True, isolation_level=None, timeout=0)
    try:
        try:
            reader.execute("UPDATE task SET value='forbidden' WHERE task_id=1")
        except sqlite3.OperationalError as error:
            require(error.sqlite_errorcode == sqlite3.SQLITE_READONLY, 'unexpected read-only error')
            error_code = error.sqlite_errorcode
        else:
            raise RuntimeError('mode=ro allowed mutation')
        require(reader.total_changes == 0, 'read-only changed rows')
    finally:
        reader.close()
    child = subprocess.run([sys.executable, 'endpoint.py', str(db)], cwd=ROOT, capture_output=True, timeout=5)
    require(child.returncode == 0 and child.stderr == b'', 'scorer process failed')
    scored = json.loads(child.stdout)
    require(scored['rows'] == [[1, 'old', 0]] and scored['query_only'] == 1 and scored['total_changes'] == 0 and scored['closed'], 'scorer primitive')
    records.append({'journal': mode, 'readonly_mutation_error': error_code, 'scorer': scored, 'child_exit': child.returncode})
(OUT / 'result.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'two_journal_fixtures': 'valid', 'two_readonly_mutations': 'rejected',
                  'two_fresh_process_endpoints': 'old/0', 'comparative_deck_run': False}))
