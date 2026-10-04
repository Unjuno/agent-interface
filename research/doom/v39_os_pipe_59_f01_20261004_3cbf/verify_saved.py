"""Saved F01 record only; never repeat consumed producer."""
import hashlib
import json
from pathlib import Path


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate(record):
    require(type(record['retries']) is int and record['retries'] == 0
            and type(record['model_calls']) is int and record['model_calls'] == 0, 'counts')
    names = ['original_fault', 'candidate_fault', 'candidate_healthy', 'candidate_eof_alive']
    require([row['case'] for row in record['rows']] == names, 'case ordering')
    expectations = [('TimeoutError', None, [{'thread': 'f01-exact-reader', 'type': 'JSONDecodeError'}]),
                    ('_SessionReaderFailure', 'JSONDecodeError', []), ('ready', None, []), ('TimeoutError', None, [])]
    for index, row in enumerate(record['rows']):
        require((row['outcome'], row['cause'], row['unhandled']) == expectations[index], 'reader outcome')
        require(row['child_alive'] is True and row['reader_alive'] is False
                and type(row['cleanup_child_exit']) is int and row['cleanup_child_exit'] == -15, 'child boundary')
        source = ('a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e' if index == 0 else
                  'dca770e5e0c532b301b12032c9532bd5fae602947caff4fff21bde60634a57f1')
        require(row['source_sha256'] == source, 'source identity')
        clocks = [row[key] for key in ('start_ns', 'wait_start_ns', 'wait_end_ns', 'end_ns')]
        require(all(type(value) is int and value > 0 for value in clocks)
                and clocks == sorted(clocks) and clocks[1] < clocks[2], 'clock identity')
        require(row['events'] == ([{'event': 'ready'}] if index == 2 else []), 'events')
    return 'PASS_PARSER_NOTIFICATION_EOF_UNRESOLVED'


def check(root):
    summary_bytes = (root / 'raw/SUMMARY.json').read_bytes()
    require(hashlib.sha256(summary_bytes).hexdigest() ==
            '34fdba812b19709beb5ec9c3baa889bc9d2a489740399dfb43db9db429877c55', 'first summary anchor')
    record = json.loads(summary_bytes)
    require({path.name for path in (root / 'raw').iterdir()} ==
            {'SUMMARY.json'} | {row['case'] + '.json' for row in record['rows']}, 'file inventory')
    for row in record['rows']:
        require(json.loads((root / 'raw' / (row['case'] + '.json')).read_text()) == row, 'cell copy')
    return validate(record)


if __name__ == '__main__':
    print(check(Path(__file__).resolve().parent))
