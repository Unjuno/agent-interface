"""Isolated owner/reader actors for a one-message anonymous pipe study."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import select
import sys
import time
from protocol import validate, disposition

clock = time.monotonic_ns

def wait_until(target):
    while (remaining := target - clock()) > 0:
        time.sleep(remaining / 1_000_000_000)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('role', choices=('owner', 'reader'))
    ap.add_argument('fd', type=int)
    ap.add_argument('out')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(exist_ok=False)
    log = (out / 'events.jsonl').open('x', encoding='utf8')
    def event(kind, **kw):
        row = {'kind': kind, 'at_ns': clock(), 'pid': os.getpid(), **kw}
        log.write(json.dumps(row, sort_keys=True) + '\n')
        log.flush()
    ready = {'type': 'READY', 'pid': os.getpid(), 'at_ns': clock(),
             'clock': 'CLOCK_MONOTONIC', 'role': args.role}
    print(json.dumps(ready), flush=True)
    raw_request = sys.stdin.buffer.readline(8193)
    (out / 'request.jsonl').write_bytes(raw_request)
    req = json.loads(raw_request)
    start = req['start_ns']
    event('START', request=req)
    if args.role == 'owner':
        wait_until(start + 60_000_000)
        payload = bytes.fromhex(req['payload_hex'])
        with (out / 'effect.bin').open('xb') as f:
            f.write(payload)
            f.flush()
            before = clock()
            os.fsync(f.fileno())
            after = clock()
        event('EFFECT', before_ns=before, after_ns=after,
              payload_sha256=hashlib.sha256(payload).hexdigest())
        wait_until(start + 80_000_000)
        stamp = clock()
        msg = {k: req[k] for k in ('schema', 'session', 'request', 'clock',
                                   'owner_pid', 'payload_sha256')}
        msg.update(commit_before_ns=before, commit_after_ns=after, producer_stamp_ns=stamp)
        frame = (json.dumps(msg, sort_keys=True, separators=(',', ':')) + '\n').encode()
        (out / 'frame.bin').write_bytes(frame)
        # Kernel short writes are fully accounted rather than assumed impossible.
        pieces = [frame]
        if req['schedule'] == 'SPLIT_FRAME':
            pieces = [frame[:len(frame)//2], frame[len(frame)//2:]]
        for index, piece in enumerate(pieces):
            if index:
                wait_until(start + 320_000_000)
            cursor = 0
            while cursor < len(piece):
                begin = clock()
                n = os.write(args.fd, piece[cursor:])
                end = clock()
                if n <= 0:
                    raise RuntimeError('zero_write')
                event('WRITE', begin_ns=begin, end_ns=end,
                      data=base64.b64encode(piece[cursor:cursor+n]).decode())
                cursor += n
        if req['schedule'] == 'WRITER_HELD_OPEN':
            wait_until(start + 320_000_000)
        begin = clock()
        os.close(args.fd)
        end = clock()
        event('CLOSE', begin_ns=begin, end_ns=end)
        result = {'role': 'owner', 'pid': os.getpid(), 'frame_bytes': len(frame)}
    else:
        if req['schedule'] == 'READER_PAUSE':
            wait_until(start + 320_000_000)
        raw = bytearray()
        eof = False
        while True:
            remaining = (start + 2_000_000_000 - clock()) / 1_000_000_000
            if remaining <= 0 or not select.select([args.fd], [], [], remaining)[0]:
                raise TimeoutError('reader_bound')
            begin = clock()
            data = os.read(args.fd, 4096)
            end = clock()
            event('READ', begin_ns=begin, end_ns=end, data=base64.b64encode(data).decode())
            if not data:
                eof = True
                break
            raw.extend(data)
            if len(raw) > 4096:
                raise ValueError('frame_limit')
            if req['mode'] == 'COMPLETE_FRAME' and b'\n' in raw:
                break
        validate_begin = clock()
        packet = validate(bytes(raw), req)
        observed = clock()
        report = disposition(observed, req['deadline_ns'])
        event('VALIDATED', begin_ns=validate_begin, observed_ns=observed,
              packet=packet, eof=eof, disposition=report)
        (out / 'received.bin').write_bytes(bytes(raw))
        os.close(args.fd)
        result = {'role': 'reader', 'pid': os.getpid(), 'observed_ns': observed,
                  'eof': eof, 'disposition': report,
                  'producer_comparator': 'ON_TIME' if packet['producer_stamp_ns'] <= req['deadline_ns'] else 'LATE'}
    event('END', result=result)
    log.close()
    print(json.dumps(result, sort_keys=True), flush=True)

if __name__ == '__main__':
    main()
