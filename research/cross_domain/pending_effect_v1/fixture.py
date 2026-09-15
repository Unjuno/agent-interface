"""Real terminal input; synthetic asynchronous append-only effects.

Public feedback is a trusted, deliberately app-aware adapter. The private ledger
is a post-control scorer, never an input to the policy. No network or model.
"""
import argparse
import json
import os
from pathlib import Path
import select
import sys
import time

MODES = ('immediate', 'delayed', 'lost_feedback', 'stale_feedback', 'reject_once', 'silent')


def append(path: Path, row: dict) -> None:
    data = (json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode()
    with path.open('ab', buffering=0) as stream:
        if stream.write(data) != len(data):
            raise OSError('short evidence write')
        os.fsync(stream.fileno())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--session', required=True)
    p.add_argument('--mode', choices=MODES, required=True)
    a = p.parse_args()
    public, private = a.root/'public', a.root/'private'
    public.mkdir(); private.mkdir()
    def receipt(attempt, status, **extra):
        row = dict(schema='application-effect-receipt-v1', session=a.session,
                   operation='append-token', attempt=attempt, observed_ns=time.perf_counter_ns(),
                   status=status, **extra)
        append(public/'feedback.jsonl', row)
        print(json.dumps(row), flush=True)
    print('Append-only save fixture. Return requests one append; no server deduplication.', flush=True)
    (public/'ready').write_text('ready')
    pending, buffer, received = [], b'', 0
    deadline = time.monotonic() + 8
    while not (public/'stop').exists() and time.monotonic() < deadline:
        if select.select([sys.stdin.fileno()], [], [], .002)[0]:
            chunk = os.read(sys.stdin.fileno(), 4096)
            if not chunk:
                break
            buffer += chunk
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                if line or received >= 2:
                    raise ValueError('only two empty Return commands permitted')
                received += 1
                now = time.perf_counter_ns()
                append(private/'received.jsonl', dict(attempt=received, received_ns=now))
                receipt(received, 'PENDING')
                if a.mode == 'reject_once' and received == 1:
                    pending.append((now + 20_000_000, received, 'reject'))
                elif a.mode != 'silent':
                    delay = 240_000_000 if a.mode in ('delayed', 'stale_feedback') else 30_000_000
                    pending.append((now + delay, received, 'commit'))
                if a.mode == 'stale_feedback':
                    pending.append((now + 25_000_000, 0, 'stale'))
        for task in list(pending):
            due, attempt, kind = task
            if time.perf_counter_ns() < due:
                continue
            pending.remove(task)
            if kind == 'reject':
                receipt(attempt, 'REJECTED_NO_EFFECT', no_effect_final=True)
            elif kind == 'stale':
                receipt(attempt, 'REJECTED_NO_EFFECT', no_effect_final=True)
            else:
                # Each input creates a NEW file. Overwrite-based scoring could hide duplicates.
                path = private/f'effect-{attempt}.txt'
                with path.open('x') as stream:
                    stream.write(a.session); stream.flush(); os.fsync(stream.fileno())
                append(private/'commits.jsonl', dict(attempt=attempt, token=a.session,
                       commit_ns=time.perf_counter_ns(), file=path.name))
                if a.mode != 'lost_feedback':
                    receipt(attempt, 'COMMITTED')
    append(private/'closed.jsonl', dict(received=received, pending=len(pending), closed_ns=time.perf_counter_ns()))


if __name__ == '__main__':
    main()
