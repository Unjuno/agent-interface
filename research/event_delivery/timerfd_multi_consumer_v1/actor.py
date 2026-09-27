"""Bounded, input-free timerfd actor. Stdout is the raw JSONL control protocol."""
from __future__ import annotations
import errno
import fcntl
import json
import os
import select
import sys
import time
from pathlib import Path


def main() -> int:
    fd = int(sys.argv[1])
    actor, case_id = sys.argv[2:4]
    owned = os.dup(fd)
    os.close(fd)
    identity = {
        'actor': actor, 'case_id': case_id, 'pid': os.getpid(),
        'received_fd': fd, 'owned_fd': owned,
        'nonblocking': bool(fcntl.fcntl(owned, fcntl.F_GETFL) & os.O_NONBLOCK),
        'fdinfo': Path(f'/proc/self/fdinfo/{owned}').read_text(),
    }
    print(json.dumps({'ready': identity}, sort_keys=True), flush=True)
    last_seq = 0
    try:
        while True:
            raw = sys.stdin.buffer.readline(16385)
            if not raw:
                return 0
            if len(raw) > 16384 or not raw.endswith(b'\n'):
                raise ValueError('unframed/oversized request')
            request = json.loads(raw)
            if (request.get('actor') != actor or request.get('case_id') != case_id
                    or type(request.get('seq')) is not int
                    or request['seq'] != last_seq + 1):
                raise ValueError('request identity/order')
            last_seq = request['seq']
            op = request['op']
            start = time.monotonic_ns()
            result: dict = {}
            if op == 'arm':
                deadline = request['deadline_ns']
                if type(deadline) is not int or deadline <= start or owned is None:
                    raise ValueError('invalid future deadline')
                os.timerfd_settime_ns(owned, flags=os.TFD_TIMER_ABSTIME,
                                     initial=deadline, interval=0)
                result = {'deadline_ns': deadline}
            elif op == 'wait_ready':
                ready, _, _ = select.select([owned], [], [], 1.0)
                result = {'readable': bool(ready)}
            elif op == 'poll':
                ready, _, _ = select.select([owned], [], [], 0)
                result = {'readable': bool(ready)}
            elif op == 'read':
                try:
                    data = os.read(owned, 8)
                    result = {'data_hex': data.hex(), 'errno': None,
                              'count': int.from_bytes(data, sys.byteorder)}
                except BlockingIOError as exc:
                    result = {'data_hex': '', 'errno': exc.errno, 'count': None}
            elif op == 'disarm':
                os.timerfd_settime_ns(owned, initial=0, interval=0)
                result = {'disarmed': True}
            elif op in ('close', 'quit'):
                closed_fd = owned
                if owned is not None:
                    os.close(owned)
                    owned = None
                    try:
                        fcntl.fcntl(closed_fd, fcntl.F_GETFD)
                        probe_errno = None
                    except OSError as exc:
                        probe_errno = exc.errno
                    result = {'closed_fd': closed_fd, 'probe_errno': probe_errno}
                else:
                    result = {'closed_fd': None, 'probe_errno': None}
            else:
                raise ValueError('unknown op')
            response = {'actor': actor, 'case_id': case_id, 'pid': os.getpid(),
                        'seq': last_seq, 'op': op, 'start_ns': start,
                        'end_ns': time.monotonic_ns(), 'result': result,
                        'authority': False, 'input_dispatched': False}
            print(json.dumps(response, sort_keys=True), flush=True)
            if op == 'quit':
                return 0
    finally:
        if owned is not None:
            os.close(owned)


if __name__ == '__main__':
    raise SystemExit(main())
