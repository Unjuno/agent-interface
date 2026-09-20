"""Independent raw-only audit for #3587; writes only to a fresh output path."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

evidence = Path(sys.argv[1])
artifact = Path(sys.argv[2])
out = Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=False)
failures = []
checks = []

def need(condition, label):
    checks.append(label)
    if not condition:
        failures.append(label)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

artifact_hash = sha(artifact)
with zipfile.ZipFile(artifact) as zf:
    build = json.loads(zf.read('BUILD.json'))
allocations = sorted(evidence.glob('formal-*/allocation.json'))
need(len(allocations) == 3, 'exactly-three-formal-allocation-records')
allocation_results = []
for allocation_path in allocations:
    root = allocation_path.parent
    row = json.loads(allocation_path.read_text())
    need(row.get('runner_error') is None, f'{root.name}:runner-completed')
    need(row.get('container_image_id') == 'sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a',
         f'{root.name}:pinned-container-image')
    need(row.get('container_platform') == 'linux/arm64', f'{root.name}:pinned-platform')
    need(row.get('artifact_sha256') == artifact_hash, f'{root.name}:artifact-digest')
    need(row.get('build_metadata', {}).get('source_revision') ==
         '02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2', f'{root.name}:committed-archive-source')
    need(row.get('build_metadata', {}).get('source_files') == build.get('source_files'),
         f'{root.name}:embedded-source-manifest')
    need(row.get('listed_tools') == ['interface_dispatch', 'interface_observe', 'interface_results'],
         f'{root.name}:exact-public-tools')
    need([c.get('operation') for c in row.get('call_records', [])] == ['observe', 'dispatch', 'observe'],
         f'{root.name}:observe-dispatch-observe-order')
    need(row.get('request_count') == row.get('report_count') == 3 == len(row.get('call_records', [])),
         f'{root.name}:request-report-cardinality')
    ids = []
    digests = []
    for label in ('initial_observation', 'post_observation'):
        result = row.get(label, {})
        metadata = result.get('metadata') or {}
        receipt = metadata.get('receipt', {}).get('report', {})
        ids.append(receipt.get('observation_id'))
        images = result.get('images', [])
        need(result.get('text_count') == 1 and len(images) == 1,
             f'{root.name}:{label}-one-text-one-image')
        if images:
            image = root/images[0]['path']
            need(image.exists() and sha(image) == images[0].get('sha256'),
                 f'{root.name}:{label}-image-hash')
            need(images[0].get('png_signature') is True, f'{root.name}:{label}-png')
            digests.append(images[0].get('sha256'))
        need(metadata.get('image_status') == 'image', f'{root.name}:{label}-review-image')
        need(receipt.get('status') == 'returned' and receipt.get('input_dispatched') is False,
             f'{root.name}:{label}-read-only-observation')
    need(all(ids) and ids[0] != ids[1], f'{root.name}:fresh-observation-identity')
    need(len(digests) == 2 and digests[0] != digests[1], f'{root.name}:initial-post-pixels-differ')
    dispatch = row.get('dispatch', {})
    dispatch_meta = dispatch.get('metadata') or {}
    raw = dispatch_meta.get('receipt', {}).get('report', {})
    execution = raw.get('result', {}).get('execution', {})
    dispatch_images = dispatch.get('images', [])
    need(dispatch.get('text_count') == 1 and len(dispatch_images) == 1,
         f'{root.name}:dispatch-one-text-one-image')
    if dispatch_images:
        image = root/dispatch_images[0]['path']
        need(image.exists() and sha(image) == dispatch_images[0].get('sha256'),
             f'{root.name}:dispatch-image-hash')
        need(dispatch_images[0].get('png_signature') is True, f'{root.name}:dispatch-png')
        need(len(digests) == 2 and dispatch_images[0].get('sha256') == digests[1],
             f'{root.name}:post-image-matches-action-observation')
    need(dispatch_meta.get('outcome_summary', {}).get('execution_status') == 'completed',
         f'{root.name}:dispatch-completed')
    releases = execution.get('releases', [])
    need(bool(releases) and all(r.get('verified') is True and r.get('keys_down') == [] and
                                r.get('buttons_down') == [] for r in releases),
         f'{root.name}:verified-empty-release')
    marker = row.get('marker')
    need(row.get('effect') == {'saved': True, 'text': marker}, f'{root.name}:independent-exact-effect')
    event_rows = []
    try:
        event_rows = [json.loads(line) for line in row.get('fixture_events', [])]
    except (TypeError, ValueError):
        pass
    need(bool(event_rows), f'{root.name}:fixture-input-event-log')
    typed = ''.join(event.get('char', '') for event in event_rows)
    keysyms = [event.get('keysym') for event in event_rows]
    need(isinstance(marker, str) and marker in typed, f'{root.name}:fixture-received-exact-marker')
    need('Control_L' in keysyms and 's' in keysyms, f'{root.name}:fixture-received-save-chord')
    need(row.get('children_reaped') is True and row.get('x11_socket_removed') is True,
         f'{root.name}:child-reap-and-socket-cleanup')
    need(row.get('fixture_exit_code') is not None and row.get('xvfb_exit_code') is not None,
         f'{root.name}:exit-codes-recorded')
    for call in row.get('call_records', []):
        request = call.get('request') or {}
        report_path = evidence/root.name/'calls'/call['call_id']/'report.json'
        request_path = evidence/root.name/'calls'/call['call_id']/'request.json'
        need(request_path.exists() and sha(request_path) == call.get('request_sha256'),
             f'{root.name}:{call["operation"]}-request-hash')
        need(report_path.exists() and sha(report_path) == call.get('report_sha256'),
             f'{root.name}:{call["operation"]}-report-hash')
        if call['operation'] == 'dispatch':
            need(request.get('arguments', {}).get('program') == row.get('program'),
                 f'{root.name}:dispatched-frozen-program')
    allocation_results.append({'allocation_id': row.get('allocation_id'),
        'marker': marker, 'observation_ids': ids, 'observation_png_sha256': digests,
        'dispatch_png_sha256': dispatch_images[0].get('sha256') if dispatch_images else None,
        'effect': row.get('effect'), 'fixture_exit_code': row.get('fixture_exit_code'),
        'xvfb_exit_code': row.get('xvfb_exit_code')})

need(len({r.get('marker') for r in allocation_results}) == len(allocation_results),
     'unique-marker-per-allocation')

result = {'schema': 'agent-interface/issue-3587-independent-audit-v2',
          'outcome': 'PASS_POST_ACTION_OBSERVE_ORBSTAC_SCOPED' if not failures else 'HOLD_OR_FAIL',
          'formal_allocations': len(allocations), 'checks_run': len(checks),
          'failed_checks': failures, 'artifact_sha256': artifact_hash,
          'source_revision': build.get('source_revision'),
          'allocations': allocation_results}
(out/'AUDIT.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
(out/'AUDIT.sha256').write_text(sha(out/'AUDIT.json')+'  AUDIT.json\n')
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not failures else 1)
