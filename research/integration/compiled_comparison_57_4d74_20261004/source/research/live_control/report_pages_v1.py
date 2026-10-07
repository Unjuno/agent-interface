"""Bounded UTF-8 evidence pages. Offline only; no receipt or input authority."""
import argparse
import hashlib
import json
from pathlib import Path

MAX_SOURCE = 8 * 1024 * 1024
FORMAT = 'report-page-v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def wire(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def page(data, after=0, expected_digest=None, limit=4096):
    if not isinstance(data, bytes) or len(data) > MAX_SOURCE:
        raise ValueError('source must be bytes within 8 MiB')
    if type(after) is not int or not 0 <= after <= len(data):
        raise ValueError('invalid byte cursor')
    if type(limit) is not int or not 1024 <= limit <= 65536:
        raise ValueError('wire limit must be 1024..65536 bytes')
    identity = digest(data)
    if (after != 0 and expected_digest is None) or (expected_digest is not None and expected_digest != identity):
        raise ValueError('source digest required/mismatched')
    data.decode('utf-8')
    data[:after].decode('utf-8')
    remaining = data[after:].decode('utf-8')

    def candidate(count):
        text = remaining[:count]
        end = after + len(text.encode('utf-8'))
        return {'format': FORMAT, 'sha256': identity, 'total_bytes': len(data),
                'after': after, 'next': end, 'source_end': end == len(data),
                'coverage': 'this byte slice only; prior pages and model receipt unverified',
                'authority': 'none; fragment is not a runtime receipt or input approval',
                'text': text}

    low, high = 0, min(len(remaining), limit)
    while low < high:
        middle = (low + high + 1) // 2
        if len(wire(candidate(middle))) <= limit:
            low = middle
        else:
            high = middle - 1
    result = candidate(low)
    if len(wire(result)) > limit or (after < len(data) and result['next'] == after):
        raise ValueError('page cannot make progress within limit')
    return result


def reconstruct(pages):
    if not pages:
        raise ValueError('no pages')
    identity, total = pages[0]['sha256'], pages[0]['total_bytes']
    if type(total) is not int or not 0 <= total <= MAX_SOURCE:
        raise ValueError('invalid source size')
    cursor, parts = 0, []
    for index, item in enumerate(pages):
        if item['format'] != FORMAT or item['sha256'] != identity or item['total_bytes'] != total:
            raise ValueError('mixed sources')
        if type(item['after']) is not int or type(item['next']) is not int or item['after'] != cursor:
            raise ValueError('missing, duplicate or reordered page')
        piece = item['text'].encode('utf-8')
        cursor += len(piece)
        if cursor != item['next'] or cursor > total or (not piece and total != 0):
            raise ValueError('invalid slice length')
        if type(item['source_end']) is not bool or item['source_end'] != (cursor == total):
            raise ValueError('invalid end marker')
        if cursor == total and index != len(pages) - 1:
            raise ValueError('pages after end')
        parts.append(piece)
    data = b''.join(parts)
    if cursor != total or digest(data) != identity:
        raise ValueError('incomplete or corrupt evidence')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--after', type=int, default=0)
    parser.add_argument('--sha256')
    parser.add_argument('--limit', type=int, default=4096)
    args = parser.parse_args()
    with args.source.open('rb') as stream:
        data = stream.read(MAX_SOURCE + 1)
    import sys
    sys.stdout.buffer.write(wire(page(data, args.after, args.sha256, args.limit)))


if __name__ == '__main__':
    main()
