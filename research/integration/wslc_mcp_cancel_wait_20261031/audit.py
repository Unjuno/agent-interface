"""Audit recorded trial outcomes; no GUI or input actions are performed."""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json

HERE = Path(__file__).resolve().parent

def load(z, path):
    return json.loads(z.read(path))

for name in ('a01', 'a02', 'a03', 'a05'):
    with ZipFile(HERE / (name + '.zip')) as z:
        result = load(z, 'output/result.json')
        terminal = load(z, 'output/mcp-terminal.json')
        ex = terminal['result']['execution']
        assert result['initial_status'] == 'pending'
        assert result['mid_score']['pass_effect'] is False
        assert result['after_score']['pass_effect'] is True
        assert hashlib.sha256(z.read('output/mid.fods')).hexdigest() == result['baseline_sha256']
        assert result['keys_down'] == [] and result['buttons_after'] == 0
        assert all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in ex['releases'])
        if name in ('a01', 'a03'):
            assert terminal['status'] == 'completed' and ex['waits'][0]['completed']
            assert 3 in ex['completed_ops']
            print(name, 'control completed')
        else:
            cancel = load(z, 'output/mcp-cancel.json')
            assert cancel['response']['status'] == 'cancel_requested'
            assert terminal['status'] == 'execution_failed'
            if name == 'a02':
                assert ex['waits'][0]['completed'] and ex['failed_op'] == 3
            else:
                assert not ex['waits'][0]['completed'] and ex['failed_op'] == 2
                assert 'cancellation requested' in ex['error']
                assert 3 not in ex['completed_ops']
            print(name, 'request-to-execution-end ms:', (ex['ended_ns'] - cancel['requested_ns']) / 1e6)
with ZipFile(HERE / 'a04.zip') as z:
    entry = load(z, 'output/entry-result.json')
    assert entry['status'] == 'refused' and entry['input_dispatched'] is False
    assert entry['guard_checks'][0]['status'] == 'STALE'
    print('a04 refused stale observation before input')
