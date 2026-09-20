"""Independent read-only gate for the retained #3573 container bundle."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
result = json.loads((root/'smoke-result.json').read_text())
manifest_path = root/'manifest.json'
if not manifest_path.exists():
    manifest_path = Path(__file__).with_name('manifest.json')
manifest = json.loads(manifest_path.read_text())
artifact = manifest_path.with_name('agent-interface-runtime.pyz')
raw = artifact.read_bytes()
failures = []
def need(ok, label):
    if not ok: failures.append(label)

need(result['transport_initialize_count'] == 1, 'one MCP initialize')
need(result['observe_call_count'] == 1 and result['dispatch_call_count'] == 1, 'one call per operation')
need(result['listed_tools'] == ['interface_dispatch', 'interface_observe'], 'exact public tool list')
need(result['observation']['image_block_count'] == 1, 'observation image block')
need(result['observation']['png_sha256'] is not None, 'observation PNG digest')
need(result['dispatch']['image_block_count'] == 1, 'dispatch image block')
need(result['dispatch']['text_status'] == 'completed', 'dispatch completed')
need(result['dispatch']['image_status'] == 'image', 'dispatch image reviewed')
need(bool(result['dispatch']['release_rows']) and all(
    row.get('verified') is True and row.get('keys_down') == [] and row.get('buttons_down') == []
    for row in result['dispatch']['release_rows']), 'verified neutral release')
need(result['report_count'] == 2 and result['request_count'] == 2 and result['call_directory_count'] == 2,
     'exact retained call/request/report counts')
need(result['effect'] == {'saved': True, 'text': result['marker']}, 'independent fixture effect')
need(result['fixture_event_lines'] > 0, 'fixture observed input events')
need(result['fixture_exit_code'] in (-2, -15, 0) and result['xvfb_exit_code'] in (0, 143),
     'owned fixture/display processes were reaped at container teardown')
need(hashlib.sha256(raw).hexdigest() == manifest['sha256'] == result['archive_sha256'], 'zipapp hash chain')
need(manifest['source_revision'] == '79bd0410e7baac734be2190a9ae7200f91b5c940', 'frozen source revision')
need(len(manifest['source_files']) == 30, 'source manifest complete')
need(result['runtime']['mcp_version'] == '1.30.0' and
     result['runtime']['python'].startswith('3.12.'), 'pinned runtime versions')
audit = {'schema': 'agent-interface/issue-3573-independent-audit-v1',
         'result': 'PASS_PORTABLE_MCP_ORBSTACK_SCOPED' if not failures else 'FAIL_OR_HOLD',
         'failures': failures, 'artifact_sha256': hashlib.sha256(raw).hexdigest(),
         'gates_checked': 14}
(root/'audit-result.json').write_text(json.dumps(audit, indent=2, sort_keys=True)+'\n')
print(json.dumps(audit, sort_keys=True))
raise SystemExit(0 if not failures else 1)
