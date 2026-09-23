"""Recorded overflow case and adversarial byte/page boundaries."""
import copy
import json
from pathlib import Path
from report_pages_v1 import page, wire, reconstruct, digest

HERE = Path(__file__).resolve().parent


def main():
    source = HERE / 'results/recovery-pair3-01/B/build/result.json'
    cases = [source.read_bytes(), ('あ😀\\\"\n' * 1700).encode(), b'']
    results = []
    for data in cases:
        pages, cursor = [], 0
        while True:
            item = page(data, cursor, digest(data), 1024)
            assert len(wire(item)) <= 1024
            pages.append(item)
            if item['source_end']:
                break
            cursor = item['next']
        assert reconstruct(pages) == data
        results.append({'source_bytes': len(data), 'sha256': digest(data), 'pages': len(pages), 'largest_wire_bytes': max(map(lambda p: len(wire(p)), pages))})
        if data == cases[0]:
            original = pages
    bad = []
    bad.append(original[1:])
    bad.append(original[:-1])
    bad.append([original[0], original[0]] + original[1:])
    bad.append(list(reversed(original)))
    for field, value in [('text', 'corrupt'), ('sha256', '0' * 64), ('source_end', True), ('next', True)]:
        changed = copy.deepcopy(original)
        changed[0][field] = value
        bad.append(changed)
    for pages in bad:
        try:
            reconstruct(pages)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid pages accepted')
    invalid_calls = [lambda: page(b'abc', 1), lambda: page(b'abc', 1, 'wrong'),
                     lambda: page('あ'.encode(), 1, digest('あ'.encode())),
                     lambda: page(b'abc', True), lambda: page(b'abc', limit=100)]
    for call in invalid_calls:
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError('invalid cursor/limit accepted')
    result = {'sources': {p.name: digest(p.read_bytes()) for p in (Path(__file__), HERE / 'report_pages_v1.py')},
              'cases': results, 'negative_controls': len(bad) + len(invalid_calls),
              'scope': 'Offline exact byte reconstruction and wire-byte bound; not model receipt, tokens, latency or black-image repair.'}
    out = HERE / 'results/report-pages-01'
    out.mkdir(exist_ok=True)
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
