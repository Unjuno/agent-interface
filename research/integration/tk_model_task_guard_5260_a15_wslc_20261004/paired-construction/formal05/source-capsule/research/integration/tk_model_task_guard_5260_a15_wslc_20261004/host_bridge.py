"""Once-only host response custody. No native input or task authority.

The future formal host driver must supply exact frozen argv and prompt. A
container request cannot supply an executable, argv, path, or new model policy.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from model_contract import parse


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def publish(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')


class HostBridge:
    def __init__(self, directory, *, allocation, freeze_sha256, slots,
                 executable_sha256):
        if (type(allocation) is not str or not allocation
            or type(freeze_sha256) is not str
            or re.fullmatch('[0-9a-f]{64}', freeze_sha256) is None
            or type(executable_sha256) is not str
            or re.fullmatch('[0-9a-f]{64}', executable_sha256) is None
            or type(slots) is not list or not slots
            or any(type(slot) is not str or re.fullmatch('pair-[0-9]{3}-(first|recovery)', slot)
                   is None for slot in slots) or len(set(slots)) != len(slots)):
            raise ValueError('Explicit finite host custody binding required')
        self.out = Path(directory)
        # Never reopen a consumed host phase after a crash or STOP.
        self.out.mkdir(parents=True, exist_ok=False)
        self.allocation = allocation
        self.freeze_sha256 = freeze_sha256
        self.executable_sha256 = executable_sha256
        self.slots = set(slots)
        self.nonces = set()
        self.completed_slots = set()
        self.stopped = False

    def consume(self, request, *, argv, prompt, image_bytes, timeout_seconds):
        if self.stopped:
            raise ValueError('First host transport/method STOP consumed phase')
        required = {'allocation','freeze_sha256','slot','nonce',
                    'image_sha256','prompt_sha256'}
        if (type(request) is not dict or set(request) != required
            or any(type(value) is not str for value in request.values())
            or request['allocation'] != self.allocation
            or request['freeze_sha256'] != self.freeze_sha256
            or request['slot'] not in self.slots
            or not 0 < len(request['nonce']) <= 128 or request['nonce'] in self.nonces
            or type(prompt) is not bytes or type(image_bytes) is not bytes
            or request['image_sha256'] != sha(image_bytes)
            or request['prompt_sha256'] != sha(prompt)
            or type(argv) is not list or not argv
            or any(type(value) is not str or not value for value in argv)
            or type(timeout_seconds) not in (int, float)
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
            raise ValueError('Host request binding or replay denied')
        if (request['slot'].endswith('-recovery')
            and request['slot'].removesuffix('-recovery')+'-first' not in self.completed_slots):
            raise ValueError('Recovery requires retained completed first answer')
        if sha(Path(argv[0]).read_bytes()) != self.executable_sha256:
            raise ValueError('Host executable identity changed')
        output = self.out/request['slot']
        if output.exists():
            raise ValueError('Host slot already consumed')
        output.mkdir(exist_ok=False)
        # Pessimistic latch: execution, parsing and every publication must all
        # finish before the phase can accept another slot. Exceptions preserve
        # their original type and any already-retained artifacts, without retry.
        self.stopped = True
        self.nonces.add(request['nonce'])
        attempt = {'request':dict(request), 'argv':list(argv),
                   'started_utc':datetime.now(timezone.utc).isoformat(),
                   'timeout_seconds':timeout_seconds}
        publish(output/'attempt.json', attempt)
        began = time.perf_counter()
        timed_out, launch_error = False, None
        cleanup = None
        try:
            process = subprocess.Popen(argv, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=os.name != 'nt',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
            try:
                stdout, stderr = process.communicate(prompt, timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                cleanup = {'owned_pid':process.pid, 'tree_requested':True,
                           'drain_timeout_seconds':1.0}
                try:
                    if os.name == 'nt':
                        command = [str(Path(os.environ.get('SystemRoot', 'C:/Windows'))/
                                       'System32/taskkill.exe'),
                                   '/PID',str(process.pid),'/T','/F']
                        killed = subprocess.run(command, capture_output=True, timeout=2)
                        cleanup.update(argv=command, tree_exit_code=killed.returncode,
                            tree_stdout=killed.stdout.decode('utf-8', errors='replace'),
                            tree_stderr=killed.stderr.decode('utf-8', errors='replace'))
                    else:
                        # Popen created this new session/group; never a shared
                        # shell group, image, daemon or unrelated peer process.
                        os.killpg(process.pid, signal.SIGKILL)
                        cleanup['tree_signal_sent'] = True
                except (OSError, subprocess.TimeoutExpired) as exception:
                    cleanup['tree_error'] = type(exception).__name__+':'+str(exception)
                if process.poll() is None:
                    process.kill()
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    cleanup['drain_completed'] = True
                except subprocess.TimeoutExpired as exception:
                    stdout, stderr = exception.output or b'', exception.stderr or b''
                    cleanup['drain_completed'] = False
                    # No blocking pipe close/drain or another model attempt.
            exit_code = process.returncode
        except OSError as error:
            stdout, stderr, exit_code = b'', b'', None
            launch_error = type(error).__name__+':'+str(error)
        for name, blob in (('stdout.bin', stdout), ('stderr.bin', stderr)):
            with (output/name).open('xb') as stream:
                stream.write(blob)
        receipt = dict(attempt, finished_utc=datetime.now(timezone.utc).isoformat(),
            wall_seconds=time.perf_counter()-began, exit_code=exit_code,
            timed_out=timed_out, launch_error=launch_error,
            timeout_cleanup=cleanup,
            output_sha256={'stdout.bin':sha(stdout), 'stderr.bin':sha(stderr),
                          'attempt.json':sha((output/'attempt.json').read_bytes())})
        publish(output/'receipt.json', receipt)
        parsed, error = None, None
        try:
            if exit_code != 0 or timed_out or launch_error:
                raise ValueError('STOP_MODEL_PROCESS')
            events = [json.loads(line) for line in stdout.decode('utf-8').splitlines() if line]
            if any(type(row) is not dict or type(row.get('type')) is not str
                   or ('item' in row and type(row['item']) is not dict)
                   or ('usage' in row and type(row['usage']) is not dict)
                   for row in events):
                raise ValueError('STOP_MODEL_EVENT_SHAPE')
            parsed = parse(events)
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeError) as exception:
            error = type(exception).__name__+':'+str(exception)
        reply = {'status':'STOP' if error else 'returned', 'request':dict(request),
                 'parsed':parsed, 'error':error, 'process':receipt,
                 'authority_granted':False, 'replay_allowed':False}
        publish(output/'reply.json', reply)
        if error is None:
            self.completed_slots.add(request['slot'])
            self.stopped = False
        return reply
