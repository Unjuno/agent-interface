"""Launch one explicitly configured private research harness, never auto-restart."""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from native_exchange_v1 import owner_state


class NativeAllocation:
    def __init__(self, directory, app, *, seed=991116, max_stages=4, python=None, text_gap_ms=0, owner_lifetime=False):
        if app not in ('calc','inkscape','calc-inkscape'):
            raise ValueError('explicit supported research app required')
        if type(seed) is not int or type(max_stages) is not int or not 2 <= max_stages <= 64:
            raise ValueError('integer seed and max_stages 2..64 required')
        if type(text_gap_ms) is not int or text_gap_ms not in (0, 2, 10):
            raise ValueError('supported text gaps are 0, 2, 10 ms')
        if type(owner_lifetime) is not bool or (owner_lifetime and os.name != 'posix'):
            raise ValueError('owner lifetime requires an explicit boolean and POSIX')
        self.owner_lifetime = owner_lifetime
        self._owner_writer = None
        self.directory = Path(directory).resolve()
        self.run_directory = self.directory/'run'
        self.app, self.seed, self.max_stages = app, seed, max_stages
        self.python = python or sys.executable
        self.text_gap_ms = text_gap_ms
        self.process = None
        self.attempted = False
        self.error = None

    def _close_owner_writer(self):
        if self._owner_writer is not None:
            os.close(self._owner_writer)
            self._owner_writer = None

    def _terminal_status(self, base, code):
        self._close_owner_writer()
        result = dict(base, status='terminal', pid=self.process.pid, returncode=code,
                      task_success=None, cleanup_verified=False, restart_allowed=False)
        if code != 0:
            path = self.directory/'stderr.log'
            diagnostic = {'kind':'process_stderr', 'authority':'none',
                          'path':str(path), 'byte_limit':2048}
            try:
                with path.open('rb') as stream:
                    size = stream.seek(0, os.SEEK_END)
                    stream.seek(max(0, size-2048))
                    tail = stream.read(2048)
                diagnostic.update(status='read', tail=tail.decode('utf-8', errors='replace'),
                                  truncated=size > 2048)
            except OSError:
                diagnostic.update(status='unavailable')
            result['diagnostic'] = diagnostic
        return result

    def status(self):
        base = {'authority':'none', 'run_directory':str(self.run_directory),
                'app':self.app, 'seed':self.seed, 'max_stages':self.max_stages,
                'text_gap_ms':self.text_gap_ms}
        if self.error is not None:
            return dict(base, status='needs_review', error=self.error, restart_allowed=False)
        if self.process is None:
            if self.directory.exists():
                return dict(base, status='needs_review', error='allocation directory already exists; attach explicitly, do not relaunch',
                            restart_allowed=False)
            return dict(base, status='not_started')
        code = self.process.poll()
        if code is not None:
            return self._terminal_status(base, code)
        owner = owner_state(self.run_directory)
        if owner is not None and owner['state'] == 'terminal':
            # Exit may become visible between poll and the owner-state read.
            # Reap only if already available: no wait, restart, or guessed code.
            code = self.process.poll()
            if code is not None:
                return self._terminal_status(base, code)
        if owner is not None and owner['state'] != 'live':
            return dict(base, status='needs_review', pid=self.process.pid, owner=owner,
                        restart_allowed=False)
        if (self.run_directory/'source-1.json').exists():
            try:
                recorded = json.loads((self.run_directory/'owner.json').read_bytes())
                if recorded['pid'] != self.process.pid or owner is None:
                    raise ValueError('source owner does not match launched process')
            except (OSError, ValueError, KeyError, TypeError) as error:
                return dict(base, status='needs_review', error=str(error), restart_allowed=False)
            return dict(base, status='ready', pid=self.process.pid, source_stage=1)
        return dict(base, status='starting', pid=self.process.pid, restart_allowed=False)

    def start(self, *, timeout=5):
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0 <= timeout <= 30:
            raise ValueError('startup wait 0..30 required')
        if not self.attempted:
            self.attempted = True
            owner_reader = None
            try:
                # Atomic claim before Popen. Existing/partial allocations never launch again.
                self.directory.mkdir(exist_ok=False)
                repo = Path(__file__).resolve().parents[2]
                args = [self.python, str(Path(__file__).with_name('run_native_calc_self_use_v1.py')),
                        '--out', str(self.run_directory), '--app', self.app,
                        '--seed', str(self.seed), '--max-stages', str(self.max_stages),
                        '--text-gap-ms', str(self.text_gap_ms)]
                owner_reader = None
                if self.owner_lifetime:
                    owner_reader, self._owner_writer = os.pipe()
                    args.extend(['--owner-lifetime-fd', str(owner_reader)])
                (self.directory/'launch.json').write_text(json.dumps({'argv':args},indent=2)+'\n')
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                           PYTHONPATH=os.pathsep.join([str(repo),str(Path(__file__).parent)]))
                with (self.directory/'stdout.log').open('xb') as stdout, (self.directory/'stderr.log').open('xb') as stderr:
                    try:
                        options = {'pass_fds': (owner_reader,)} if owner_reader is not None else {}
                        self.process = subprocess.Popen(args, cwd=repo, env=env, stdin=subprocess.DEVNULL,
                                                        stdout=stdout, stderr=stderr, **options)
                    finally:
                        if owner_reader is not None:
                            os.close(owner_reader)
                            owner_reader = None
            except Exception as error:
                self._close_owner_writer()
                self.error = str(error)
            finally:
                if owner_reader is not None:
                    os.close(owner_reader)
        deadline = time.monotonic()+timeout
        while True:
            state = self.status()
            if state['status'] != 'starting' or time.monotonic() >= deadline:
                return state
            time.sleep(min(.05, max(0,deadline-time.monotonic())))
