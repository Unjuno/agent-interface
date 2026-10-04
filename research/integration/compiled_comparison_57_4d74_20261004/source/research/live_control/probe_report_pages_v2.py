"""Compare page boundaries on observed failure and adversarial lines."""
import copy
import json
from pathlib import Path
import report_pages_v1 as v1
import report_pages_v2 as v2

HERE = Path(__file__).resolve().parent


def collect(module, data, limit):
    pages, cursor = [], 0
    while True:
        item = module.page(data, cursor, module.digest(data), limit)
        assert len(module.wire(item)) <= limit
        pages.append(item)
        if item['source_end']:
            break
        assert item['next'] > cursor
        cursor = item['next']
    assert module.reconstruct(pages) == data
    return pages


def main():
    data = (HERE / 'results/recovery-pair3-01/B/build/result.json').read_bytes()
    rows = []
    cases = {'recorded': data, 'oversize_unicode': ('あ😀\\\"' * 2000 + '\nend').encode(),
             'crlf': ('x\r\ny\n' * 700).encode(), 'empty': b'',
             'no_final_newline': b'641', 'many_empty_lines': b'\n' * 4000}
    for name, source in cases.items():
        for limit in (1024, 4096):
            old, new = collect(v1, source, limit), collect(v2, source, limit)
            if name == 'recorded':
                assert not any(p['starts_mid_line'] or p['ends_mid_line'] for p in new)
            if name == 'oversize_unicode':
                assert any(p['ends_mid_line'] for p in new)
            rows.append({'case': name, 'limit': limit, 'source_bytes': len(source),
                         'v1_pages': len(old), 'v2_pages': len(new),
                         'v1_wire_bytes': sum(len(v1.wire(p)) for p in old),
                         'v2_wire_bytes': sum(len(v2.wire(p)) for p in new),
                         'v2_partial_ends': sum(p['ends_mid_line'] for p in new)})
    pages = collect(v2, data, 4096)
    bad = [pages[1:], pages[:-1], [pages[0]] + pages, list(reversed(pages))]
    for key, value in [('starts_mid_line', True), ('ends_mid_line', True), ('source_end', True),
                       ('text', 'bad'), ('sha256', 'bad'), ('next', True)]:
        altered = copy.deepcopy(pages)
        altered[0][key] = value
        bad.append(altered)
    for items in bad:
        try:
            v2.reconstruct(items)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid pages accepted')
    report = {'sources': {p.name: v2.digest(p.read_bytes()) for p in (Path(__file__), HERE / 'report_pages_v1.py', HERE / 'report_pages_v2.py')},
              'rows': rows, 'negative_controls': len(bad),
              'scope': 'Offline byte reconstruction and line boundaries; no model receipt, tokens, latency or image qualification.'}
    out = HERE / 'results/report-pages-v2-01'
    out.mkdir(exist_ok=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
