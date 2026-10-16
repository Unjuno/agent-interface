"""Verify recorded page-only retry and reconstruction; visibility is reported."""
import json
from pathlib import Path
from report_pages_v1 import reconstruct, wire, digest
from pointer_report_view_v1 import unpack

HERE = Path(__file__).resolve().parent


def main():
    root = HERE / 'results/report-pages-self-use-01'
    record = json.loads((root / 'attempts.json').read_text())
    source = (HERE.parent.parent / record['source']).read_bytes()
    assert digest(source) == record['digest']
    assert reconstruct(record['pages']) == source
    attempts = record['attempts']
    assert len(attempts) == 7 and len(record['pages']) == 6
    assert [a['displayed'] for a in attempts] == [True, False, True, True, True, True, True]
    assert attempts[1]['page'] == attempts[2]['page']
    assert record['pages'] == [a['page'] for a in attempts if a['displayed']]
    assert all(len(wire(a['page'])) <= 4096 for a in attempts)
    try:
        reconstruct([record['pages'][0]] + record['pages'][2:])
    except ValueError:
        pass
    else:
        raise AssertionError('missing displayed page accepted')
    report = unpack(json.loads(source)['view'])
    assert report['terminal']['status'] == 'completed'
    result = {'sources': {p.name: digest(p.read_bytes()) for p in (Path(__file__), HERE / 'report_pages_v1.py')},
              'attempts_sha256': digest((root / 'attempts.json').read_bytes()),
              'source_sha256': digest(source), 'exact_reconstruction': True,
              'unique_pages': 6, 'cli_calls': 7, 'simulated_display_omissions': 1,
              'wire_bytes_unique': sum(len(wire(p)) for p in record['pages']),
              'wire_bytes_attempted': sum(len(wire(a['page'])) for a in attempts),
              'source_bytes': len(source), 'missing_page_rejected': True,
              'task_input_calls': 0, 'observed_terminal': report['terminal'],
              'scope': 'Actual assistant inspection of historical text with deliberately suppressed display; not real transport loss, fresh task success, image delivery, model receipt or token measurement.',
              'usability_issue': 'Byte boundaries split numbers and JSON structures; exactness alone does not make fragments easy to review.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
