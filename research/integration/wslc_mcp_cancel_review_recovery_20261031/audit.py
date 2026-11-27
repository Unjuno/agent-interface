"""Read-only audit of one WSLc cancellation and fresh-review continuation."""
import hashlib, json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

T = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O = '{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

def values(blob, count):
    sheets = ET.fromstring(blob).findall('.//' + T + 'table')
    assert len(sheets) == 1
    rows = sheets[0].findall(T + 'table-row')
    assert len(rows) >= count
    return [row.find(T + 'table-cell').get(O + 'value') for row in rows[:count]]

with ZipFile(Path(__file__).with_name('a10.zip')) as z:
    def read(name): return json.loads(z.read('output/' + name))
    initial, terminal = read('mcp-initial.json'), read('mcp-terminal.json')
    cancel, probe = read('mcp-cancel.json'), read('post-terminal-probe.json')
    review, old = read('mcp-review.json'), read('post-review-old-alias.json')
    mint, new, result = read('mcp-remint.json'), read('recovery-input.json'), read('result.json')
    assert initial['status'] == 'pending' and result['call_id'] == initial['call_id']
    assert cancel['response']['status'] == 'cancel_requested'
    assert terminal['status'] == 'execution_failed'
    assert not terminal['result']['execution']['waits'][0]['completed']
    assert probe['is_error'] and probe['payload']['result']['error'] == 'WINDOW_REVIEW_REQUIRED'
    assert not probe['payload']['result']['input_dispatched']
    assert review['status'] == 'reviewed' and not review['review']['input_dispatched']
    assert review['review']['binding_revision'] == review['review']['previous_binding_revision'] + 1
    assert review['review']['scope'] != review['review']['previous_scope']
    assert hashlib.sha256(z.read('output/review-image.png')).hexdigest() == review['source']['native']['artifact']['sha256']
    assert old['is_error'] and old['payload']['status'] == 'refused'
    assert not old['payload']['result']['input_dispatched']
    assert old['payload']['result']['guard_checks'][0]['status'] == 'MISSING'
    assert mint['status'] == 'minted' and mint['source_sequence'] == review['source']['sequence']
    assert new['is_error'] is False and new['payload']['status'] == 'completed'
    for execution in (terminal['result']['execution'], new['payload']['result']['execution']):
        assert execution['releases'] and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in execution['releases'])
    assert result['keys_down'] == [] and result['buttons_after'] == 0
    mid, after, recovery = (z.read('output/' + f) for f in ('mid.fods','after.fods','after-recovery.fods'))
    assert hashlib.sha256(mid).hexdigest() == result['baseline_sha256']
    assert values(mid, 2) == [None, None]
    assert values(after, 2) == ['731', '864']
    assert result['after_score']['pass_effect'] is True
    assert values(recovery, 3) == ['731', '864', '975']
print('cancel, old-reference refusal, fresh review, distinct saved continuation: verified for a10')
