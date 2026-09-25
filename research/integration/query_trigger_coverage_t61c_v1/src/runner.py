"""Bounded first-outcome batches; all actors are local private database processes."""
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
MODES = ('REVISION_ONLY', 'CURRENT_DDL', 'SCHEMA_COOKIE')
SCENARIOS = ('STABLE', 'NORMAL_INSERT', 'OTHER_TENANT_INSERT', 'MISSING_AT_PREPARE',
             'DROP_THEN_INSERT', 'RESTORE_AFTER_INSERT', 'RESTORE_NO_DATA',
             'UNRELATED_DDL', 'ROLLED_BACK_MIGRATION')
STEPS = ([], ['insert_a'], ['insert_b'], ['insert_a'], ['drop', 'insert_a'],
         ['drop', 'insert_a', 'restore'], ['drop', 'restore'], ['unrelated'],
         ['drop', 'insert_a', 'restore'])


def write(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + '\n')


def observe(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        return {'identity': db.execute('SELECT identity FROM meta').fetchone()[0],
                'cookie': db.execute('PRAGMA main.schema_version').fetchone()[0],
                'scopes': db.execute('SELECT * FROM scopes ORDER BY tenant').fetchall(),
                'items': db.execute('SELECT * FROM items ORDER BY id').fetchall(),
                'effects': db.execute('SELECT * FROM effects ORDER BY request_id').fetchall(),
                'triggers': db.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger' AND tbl_name='items' ORDER BY name").fetchall()}
    finally:
        db.close()


class Channel:
    def __init__(self, role, path, mode, config, directory):
        self.log = []
        self.buffer = b''
        self.errpath = directory / (role + '.stderr')
        self.err = self.errpath.open('xb')
        self.argv = [sys.executable, '-S', '-B', str(ROOT / 'actor.py'), role,
                     str(path), mode, str(config)]
        self.p = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=self.err)
        self.boot = self.line()

    def line(self):
        deadline = time.monotonic() + 3
        while b'\n' not in self.buffer:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self.p.stdout], [], [], left)[0]:
                raise TimeoutError('ACTOR_RESPONSE_TIMEOUT')
            data = os.read(self.p.stdout.fileno(), 65536)
            if not data:
                raise RuntimeError('ACTOR_EOF')
            self.buffer += data
            if len(self.buffer) > 1048576:
                raise ValueError('RESPONSE_BOUND')
        line, self.buffer = self.buffer.split(b'\n', 1)
        return (line + b'\n').decode()

    def call(self, obj):
        request = json.dumps(obj, separators=(',', ':')) + '\n'
        before = time.monotonic_ns()
        self.p.stdin.write(request.encode()); self.p.stdin.flush()
        response = self.line()
        self.log.append({'request': request, 'response': response,
                         'before_ns': before, 'after_ns': time.monotonic_ns()})
        return json.loads(response)['value']

    def finish(self):
        if self.p.poll() is None:
            self.call({'op': 'stop'})
        code = self.p.wait(timeout=3)
        self.p.stdin.close(); self.p.stdout.close(); self.err.close()
        if code != 0:
            raise RuntimeError('NONZERO_ACTOR_EXIT')
        return {'argv': self.argv, 'pid': self.p.pid, 'boot': self.boot,
                'exit': code, 'stderr': self.errpath.read_text(), 'calls': self.log}

    def cleanup(self):
        if self.p.poll() is None:
            self.p.kill()
        self.p.wait(timeout=3)
        self.err.close()


def case(destination, condition, mode, identity):
    destination.mkdir(parents=True, exist_ok=False)
    path = destination / 'state.sqlite'
    db = sqlite3.connect(path, isolation_level=None)
    db.executescript((ROOT / 'schema.sql').read_text())
    db.execute('INSERT INTO meta VALUES(?)', (identity,))
    db.close()
    observations = {}
    def snapshot(name):
        observations[name] = observe(path)
        shutil.copyfile(path, destination / (name + '.sqlite'))
    snapshot('initial')
    expected = {'identity': identity, 'triggers': observations['initial']['triggers']}
    config = destination / 'config.json'; write(config, expected)
    actors = {}
    try:
        actors['writer'] = Channel('writer', path, mode, config, destination)
        actors['reader'] = Channel('reader', path, mode, config, destination)
        if condition == 'MISSING_AT_PREPARE':
            actors['writer'].call({'op': 'change', 'steps': ['drop'], 'rollback': False})
        snapshot('before_prepare')
        preparation = actors['reader'].call({'op': 'prepare'})
        snapshot('prepared')
        index = SCENARIOS.index(condition)
        actors['writer'].call({'op': 'change', 'steps': STEPS[index],
                               'rollback': condition == 'ROLLED_BACK_MIGRATION'})
        snapshot('changed')
        decision = actors['reader'].call({'op': 'commit'})
        snapshot('final')
        processes = {role: ch.finish() for role, ch in actors.items()}
        out = {'id': identity, 'condition': condition, 'mode': mode,
               'preparation': preparation, 'decision': decision,
               'observations': observations, 'processes': processes}
        write(destination / 'row.json', out)
        return out
    finally:
        for channel in actors.values():
            channel.cleanup()


def main():
    out = Path(sys.argv[1]).resolve(); batch = int(sys.argv[2]); reps = int(sys.argv[3])
    if not 0 <= batch < 9 or reps not in (1, 2):
        raise ValueError('INVALID_BATCH')
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    rows = []
    start = time.monotonic_ns()
    for repeat in range(reps):
        modes = MODES if repeat % 2 == 0 else tuple(reversed(MODES))
        for mode in modes:
            identity = f't61c-{batch}-{repeat}-{MODES.index(mode)}'
            row = case(out / identity, SCENARIOS[batch], mode, identity)
            rows.append(row)
    result = {'batch': batch, 'repetitions': reps, 'start_ns': start,
              'end_ns': time.monotonic_ns(), 'rows': rows}
    write(out / 'RAW.json', result)
    print(json.dumps({'batch': batch, 'rows': len(rows),
                      'raw_sha256': hashlib.sha256((out / 'RAW.json').read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
