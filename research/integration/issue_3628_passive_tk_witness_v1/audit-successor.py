"""Frozen raw-only audit for #3628 passive Tk event witness allocations."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

evidence, artifact, out = map(Path, sys.argv[1:4])
out.mkdir(parents=True, exist_ok=False)
failures, checks = [], []

def need(condition, label):
    checks.append(label)
    if not condition:
        failures.append(label)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

with zipfile.ZipFile(artifact) as zf:
    build = json.loads(zf.read('BUILD.json'))
allocations = sorted(evidence.glob('formal-*/allocation.json'))
need(len(allocations) == 3, 'exactly-three-formal-allocation-records')
rows_out = []
for path in allocations:
    root = path.parent
    row = json.loads(path.read_text())
    tag = root.name
    need(row.get('runner_error') is None, f'{tag}:runner-completed')
    need(row.get('container_image_id') == 'sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a', f'{tag}:pinned-image')
    need(row.get('container_platform') == 'linux/arm64', f'{tag}:pinned-platform')
    need(row.get('artifact_sha256') == sha(artifact), f'{tag}:archive-hash')
    need(row.get('build_metadata', {}).get('source_revision') == '02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2', f'{tag}:archive-source-revision')
    need(row.get('build_metadata', {}).get('source_files') == build.get('source_files'), f'{tag}:embedded-source-manifest')
    need(row.get('listed_tools') == ['interface_dispatch', 'interface_observe', 'interface_results'], f'{tag}:public-tool-list')
    calls = row.get('call_records', [])
    need([c.get('operation') for c in calls] == ['observe', 'dispatch', 'observe'], f'{tag}:observe-dispatch-observe')
    need(row.get('request_count') == row.get('report_count') == len(calls) == 3, f'{tag}:request-report-count')
    ids, image_hashes = [], []
    for label in ('initial_observation', 'post_observation'):
        result = row.get(label, {})
        metadata = result.get('metadata') or {}
        receipt = metadata.get('receipt', {}).get('report', {})
        ids.append(receipt.get('observation_id'))
        images = result.get('images', [])
        need(result.get('text_count') == 1 and len(images) == 1, f'{tag}:{label}-one-text-image')
        if images:
            img = root / images[0]['path']
            need(img.exists() and sha(img) == images[0].get('sha256') and images[0].get('png_signature') is True, f'{tag}:{label}-image-bytes-hash-png')
            image_hashes.append(images[0].get('sha256'))
        need(metadata.get('image_status') == 'image' and receipt.get('status') == 'returned' and receipt.get('input_dispatched') is False, f'{tag}:{label}-read-only-receipt')
    need(all(ids) and ids[0] != ids[1], f'{tag}:fresh-observation-ids')
    need(len(image_hashes) == 2 and image_hashes[0] != image_hashes[1], f'{tag}:initial-post-images-differ')
    dispatch = row.get('dispatch', {})
    dm = dispatch.get('metadata') or {}
    report = dm.get('receipt', {}).get('report', {})
    execution = report.get('result', {}).get('execution', {})
    images = dispatch.get('images', [])
    need(dispatch.get('text_count') == 1 and len(images) == 1, f'{tag}:dispatch-one-text-image')
    if images:
        img = root / images[0]['path']
        need(img.exists() and sha(img) == images[0].get('sha256') and images[0].get('png_signature') is True, f'{tag}:dispatch-image-bytes-hash-png')
        need(len(image_hashes) == 2 and images[0].get('sha256') == image_hashes[1], f'{tag}:dispatch-matches-post-image')
    need(dm.get('outcome_summary', {}).get('execution_status') == 'completed', f'{tag}:dispatch-completed')
    releases = execution.get('releases', [])
    need(bool(releases) and all(r.get('verified') is True and r.get('keys_down') == [] and r.get('buttons_down') == [] for r in releases), f'{tag}:empty-verified-release')
    marker = row.get('marker')
    need(row.get('effect') == {'saved': True, 'text': marker}, f'{tag}:independent-effect-exact-marker')
    event_rows = [json.loads(line) for line in row.get('fixture_events', [])]
    passive = [e for e in event_rows if e.get('bindtag') == 'AgentInterfacePassiveAudit']
    chord = [e.get('keysym') for e in passive if e.get('keysym') in {'Control_L', 's'}]
    need(chord == ['Control_L', 's'], f'{tag}:passive-chord-exactly-once-ordered')
    need(marker in ''.join(e.get('char', '') for e in passive), f'{tag}:passive-event-marker')
    need(row.get('children_reaped') is True and row.get('x11_socket_removed') is True and row.get('xvfb_exit_code') == 0 and row.get('fixture_exit_code') is not None, f'{tag}:process-and-socket-cleanup')
    for call in calls:
        call_dir = root / 'calls' / call['call_id']
        req, rep = call_dir / 'request.json', call_dir / 'report.json'
        need(req.exists() and sha(req) == call.get('request_sha256'), f'{tag}:{call["operation"]}-request-hash')
        need(rep.exists() and sha(rep) == call.get('report_sha256'), f'{tag}:{call["operation"]}-report-hash')
        if call['operation'] == 'dispatch':
            need(json.loads(req.read_text()).get('arguments', {}).get('program') == row.get('program'), f'{tag}:dispatch-program-matches-record')
    rows_out.append({'allocation_id': row.get('allocation_id'), 'marker': marker, 'passive_chord': chord,
                     'observation_ids': ids, 'observation_png_sha256': image_hashes,
                     'dispatch_png_sha256': images[0].get('sha256') if images else None,
                     'effect': row.get('effect'), 'fixture_exit_code': row.get('fixture_exit_code'),
                     'xvfb_exit_code': row.get('xvfb_exit_code')})
need(len({r['allocation_id'] for r in rows_out}) == 3, 'unique-allocation-ids')
need(len({r['marker'] for r in rows_out}) == 3, 'unique-markers')
result = {'schema': 'issue-3628/passive-tk-witness-audit-v1',
          'outcome': 'PASS_TK_EVENT_WITNESS_AND_PUBLIC_MCP_CONTINUATION_SCOPED' if not failures else 'HOLD_OR_FAIL',
          'formal_allocations': len(allocations), 'checks_run': len(checks),
          'failed_checks': failures, 'archive_sha256': sha(artifact), 'allocations': rows_out}
target = out / 'AUDIT.json'
target.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
(out / 'AUDIT.sha256').write_text(sha(target) + '  AUDIT.json\n')
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not failures else 1)
