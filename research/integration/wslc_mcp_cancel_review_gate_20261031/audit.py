"""Read-only audit of review gate and Calc file evidence."""
import hashlib, json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
TABLE = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
OFFICE = '{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

def read(z, name):
    return json.loads(z.read(name))

def first_two_values(blob):
    root = ET.fromstring(blob)
    sheets = root.findall('.//' + TABLE + 'table')
    assert len(sheets) == 1
    rows = sheets[0].findall(TABLE + 'table-row')
    assert len(rows) >= 2
    cells = [r.find(TABLE + 'table-cell') for r in rows[:2]]
    assert all(c is not None for c in cells)
    return [c.get(OFFICE + 'value') for c in cells]

for name in ('a08', 'a09'):
    with ZipFile(HERE / (name + '.zip')) as z:
        result = read(z, 'output/result.json')
        initial = read(z, 'output/mcp-initial.json')
        terminal = read(z, 'output/mcp-terminal.json')
        probe = read(z, 'output/post-terminal-probe.json')
        payload = probe['payload']
        assert initial['status'] == 'pending'
        assert result['call_id'] == initial['call_id']
        assert result['keys_down'] == [] and result['buttons_after'] == 0
        releases = terminal['result']['execution']['releases']
        assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
        mid, after = z.read('output/mid.fods'), z.read('output/after.fods')
        assert hashlib.sha256(mid).hexdigest() == result['baseline_sha256']
        assert first_two_values(mid) == [None, None]
        assert first_two_values(after) == ['731', '864']
        if name == 'a08':
            assert terminal['status'] == 'completed'
            assert probe['is_error'] is False and payload['status'] == 'completed'
            assert payload['result']['execution']['program_emissions'] == 2
        else:
            cancel = read(z, 'output/mcp-cancel.json')
            assert cancel['response']['status'] == 'cancel_requested'
            assert terminal['status'] == 'execution_failed'
            assert terminal['result']['execution']['waits'][0]['completed'] is False
            assert probe['is_error'] is True and payload['status'] == 'refused'
            assert payload['result']['error'] == 'WINDOW_REVIEW_REQUIRED'
            assert payload['result']['input_dispatched'] is False
        print(name, terminal['status'], payload['status'], 'blank before resume, saved after')
with ZipFile(HERE / 'a07.zip') as z:
    assert b'WINDOW_REVIEW_REQUIRED' in z.read('container.stderr')
    print('a07: refusal reached, trial harness raised before remaining observations')
