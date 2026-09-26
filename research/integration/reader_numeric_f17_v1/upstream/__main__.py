"""Explicit experimental host boundary. Never saves a cursor or acknowledges."""
import argparse
import json
from pathlib import Path
import sys

from .reader import read_pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stream', required=True)
    parser.add_argument('--stream-id', required=True)
    parser.add_argument('--cursor', help='caller-saved next_cursor JSON; omitted for first read')
    parser.add_argument('--max-records', type=int, default=32)
    parser.add_argument('--max-bytes', type=int, default=1048576)
    args = parser.parse_args()
    try:
        cursor = None
        if args.cursor:
            with Path(args.cursor).open('rb') as source:
                data = source.read(4097)
            if len(data) > 4096:
                raise ValueError('CURSOR_READ_BOUND_EXCEEDED')
            cursor = json.loads(data)
            if cursor is None:
                raise ValueError('INVALID_CURSOR')
        result = read_pending(args.stream, stream_id=args.stream_id, cursor=cursor,
                              max_records=args.max_records, max_bytes=args.max_bytes)
        exit_code = 2 if result['problem'] else 0
    except (OSError, ValueError) as error:
        result = {'schema': 'agent-interface/experimental-inbox-read-v1',
                  'status': 'read_failed', 'error': str(error),
                  'authority': 'none', 'acknowledged': False, 'input_dispatched': False}
        exit_code = 2
    encoded = json.dumps(result, allow_nan=False) + '\n'
    if sys.stdout.write(encoded) != len(encoded):
        raise OSError('INCOMPLETE_STDOUT_WRITE')
    sys.stdout.flush()
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
