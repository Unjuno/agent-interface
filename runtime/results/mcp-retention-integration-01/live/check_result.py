import hashlib
import json
from pathlib import Path

root = Path(__file__).parent
def read(name):
    return json.loads((root/name).read_text(encoding='utf-8-sig'))

first = read('action-2-metadata.json')
lookup = read('action-3-metadata.json')
assert first['call_id'] == lookup['call_id']
assert first['outcome_summary'] == lookup['outcome_summary']
assert first['receipt']['source']['raw_report'] == lookup['receipt']['source']['raw_report']
assert first['outcome_summary']['input_release_verified'] is True
assert first['outcome_summary']['execution_status'] == 'completed'
assert lookup['operation_invoked'] is False
assert lookup['image_delivery'] == 'omitted_by_request'
assert all(block['type'] != 'image' for block in read('action-3-response.json')['content'])
before = {row['path']: row['sha256'] for row in read('before-lookup-hashes.json')}
after = {str(path.relative_to(root/'calls')): hashlib.sha256(path.read_bytes()).hexdigest().upper()
         for path in (root/'calls').rglob('*') if path.is_file()}
assert before == after
requests = [json.loads(path.read_bytes()) for path in (root/'calls').glob('*/request.json')]
assert sorted(row['operation'] for row in requests) == ['dispatch', 'observe']
assert not list((root/'calls').rglob('*.tmp'))
assert read('effect.json') == {'saved': True, 'text': 'receipt-72'}
assert read('primary-declaration.json')['primary_complete'] is True
result = {'status': 'PASS_LOCAL_PRIMARY_MCP_COMPOSITION', 'call_id': first['call_id'],
          'raw_report_equal': True, 'retained_files_unchanged': len(after),
          'dispatch_count': 1, 'observe_count': 1, 'saved_text': 'receipt-72',
          'input_release_verified': True, 'lookup_emitted_image': False,
          'cleanup': read('cleanup.json'),
          'scope': 'single fixture primary SDK-mediated MCP use; no disconnect injected; no registered-host, speed/token or general reliability claim'}
(root/'RESULT.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
