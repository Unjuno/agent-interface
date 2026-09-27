"""Post-hoc raw-only reconstruction; never launches a GUI or runtime."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import zipfile

evidence = Path(sys.argv[1])
freeze_dir = Path(sys.argv[2])
artifact = freeze_dir/'agent-interface-runtime.pyz'
out = Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=False)
freeze = json.loads((freeze_dir/'FREEZE.json').read_text())
manifest = json.loads((freeze_dir/'manifest.json').read_text())
artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
runner_sha = hashlib.sha256((freeze_dir.parent/'container_smoke.py').read_bytes()).hexdigest()
parent_auditor_sha = hashlib.sha256((freeze_dir.parent/'audit.py').read_bytes()).hexdigest()
with zipfile.ZipFile(artifact) as archive:
    build = json.loads(archive.read('BUILD.json'))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse_json(path: Path):
    return json.loads(path.read_text())

def saved_image(root: Path, response: dict):
    images = response.get('images', [])
    if len(images) != 1:
        return None
    path = root/images[0].get('path', '')
    return path if path.is_file() else None

def validate(row: dict, root: Path) -> list[str]:
    failures = []
    def need(ok, label):
        if not ok:
            failures.append(label)
    need(row.get('runner_error') is None, 'runner_error')
    need(row.get('container_image_id') == freeze['container']['image_id'], 'container_image')
    need(row.get('container_platform') == freeze['container']['platform'], 'container_platform')
    need(row.get('artifact_sha256') == artifact_sha == freeze['portable_archive']['sha256'], 'archive_sha')
    need(row.get('build_metadata') == build, 'embedded_build_metadata')
    need(build.get('source_revision') == freeze['source_revision'] == manifest.get('source_revision'),
         'frozen_source_revision')
    need(build.get('source_files') == manifest.get('source_files'), 'source_manifest_match')
    need(row.get('listed_tools') == ['interface_dispatch', 'interface_observe', 'interface_results'],
         'tool_inventory')
    calls = row.get('call_records', [])
    need([c.get('operation') for c in calls] == ['observe', 'dispatch', 'observe'], 'call_order')
    need(row.get('request_count') == row.get('report_count') == len(calls) == 3, 'call_cardinality')
    expected_ids = []
    for key in ('initial_observation', 'dispatch', 'post_observation'):
        response = row.get(key, {})
        metadata = response.get('metadata') or {}
        call_id = Path(metadata.get('call_directory', '/invalid')).name
        expected_ids.append(call_id)
    need(expected_ids == [c.get('call_id') for c in calls], 'reply_call_id_binding')
    all_responses = (('initial_observation', calls[0] if len(calls) > 0 else {}, 'observe'),
                     ('dispatch', calls[1] if len(calls) > 1 else {}, 'dispatch'),
                     ('post_observation', calls[2] if len(calls) > 2 else {}, 'observe'))
    obs_ids = []
    obs_hashes = []
    for key, call, operation in all_responses:
        response = row.get(key, {})
        metadata = response.get('metadata') or {}
        need(response.get('text_count') == 1 and response.get('is_error') is False, key+'_transport')
        need(metadata.get('image_status') == 'image', key+'_review_status')
        receipt = metadata.get('receipt', {}).get('report', {})
        expected_report_path = root/'calls'/call.get('call_id', 'missing')/'report.json'
        expected_request_path = root/'calls'/call.get('call_id', 'missing')/'request.json'
        need(expected_request_path.is_file() and sha(expected_request_path) == call.get('request_sha256'),
             key+'_request_file_hash')
        need(expected_report_path.is_file() and sha(expected_report_path) == call.get('report_sha256'),
             key+'_report_file_hash')
        if expected_request_path.is_file():
            disk_request = parse_json(expected_request_path)
            need(disk_request == call.get('request'), key+'_request_content_link')
            need(disk_request.get('operation') == operation, key+'_request_operation')
        if expected_report_path.is_file():
            disk_report = parse_json(expected_report_path)
            need(disk_report == call.get('report') == receipt, key+'_report_content_link')
        if operation == 'observe':
            observation = receipt.get('observation', {})
            observation_id = receipt.get('observation_id')
            obs_ids.append(observation_id)
            need(receipt.get('schema') == 'agent-interface/runtime-observation-v1' and
                 receipt.get('status') == 'returned' and receipt.get('input_dispatched') is False,
                 key+'_read_only_report')
            native = observation
        else:
            native_result = receipt.get('result', {})
            execution = native_result.get('execution', {})
            need(receipt.get('schema') == 'agent-interface/runtime-dispatch-result-v1' and
                 receipt.get('status') == 'returned' and native_result.get('status') == 'completed' and
                 native_result.get('admission') == 'accepted', 'dispatch_raw_completion')
            need(metadata.get('outcome_summary', {}).get('execution_status') == 'completed' and
                 metadata.get('outcome_summary', {}).get('input_release_verified') is True,
                 'dispatch_review_summary')
            releases = execution.get('releases', [])
            need(bool(releases) and all(r.get('verified') is True and r.get('keys_down') == [] and
                                        r.get('buttons_down') == [] for r in releases), 'dispatch_release')
            observations = execution.get('observations', [])
            need(len(observations) == 1, 'dispatch_observation_count')
            native = observations[0] if len(observations) == 1 else {}
        artifact_info = native.get('artifact', {})
        mcp_image = saved_image(root, response)
        if mcp_image is None:
            need(False, key+'_one_image_file')
            continue
        image_digest = sha(mcp_image)
        image_row = response['images'][0]
        need(image_row.get('png_signature') is True and image_row.get('mime_type') == 'image/png',
             key+'_png_identity')
        need(image_digest == image_row.get('sha256') == metadata.get('image_reference', {}).get('sha256') ==
             artifact_info.get('sha256'), key+'_image_hash_binding')
        need(mcp_image.stat().st_size == image_row.get('bytes') == artifact_info.get('bytes'),
             key+'_image_byte_count')
        need(artifact_info.get('source_raw_sha256') == native.get('sha256'), key+'_raw_pixel_binding')
        source_path = Path(artifact_info.get('path', '/invalid'))
        retained_capture = root/'calls'/call.get('call_id', 'missing')/'images'/source_path.name
        need(source_path.parent.name == 'images' and retained_capture.is_file() and
             sha(retained_capture) == image_digest, key+'_artifact_path_binding')
        need(response.get('images') and response['images'][0].get('sha256') == image_digest,
             key+'_mcp_image_hash')
        if operation == 'observe':
            obs_hashes.append(image_digest)
    need(len(obs_ids) == 2 and all(obs_ids) and obs_ids[0] != obs_ids[1], 'distinct_observation_ids')
    need(len(obs_hashes) == 2 and obs_hashes[0] != obs_hashes[1], 'initial_post_image_change')
    dispatch_images = row.get('dispatch', {}).get('images', [])
    need(len(dispatch_images) == 1 and len(obs_hashes) == 2 and
         dispatch_images[0].get('sha256') == obs_hashes[1], 'dispatch_post_pixel_match')
    marker = row.get('marker')
    effect_path = root/'fixture-effect.json'
    need(effect_path.is_file() and parse_json(effect_path) == row.get('effect') ==
         {'saved': True, 'text': marker}, 'independent_exact_effect')
    events_path = root/'fixture-events.jsonl'
    try:
        disk_lines = events_path.read_text().splitlines()
        event_rows = [json.loads(line) for line in row.get('fixture_events', [])]
        need(disk_lines == row.get('fixture_events'), 'event_file_copy')
        typed = ''.join(e.get('char', '') for e in event_rows)
        keysyms = [e.get('keysym') for e in event_rows]
        need(marker in typed, 'fixture_received_marker')
        # Tk's matching <Control-s> callback returns "break", so its event does
        # not reach the subsequent diagnostic KeyPress logger. The saved effect
        # file is the independent oracle for the chord's application outcome.
        need('Control_L' in keysyms, 'fixture_received_control_prefix')
    except (OSError, TypeError, ValueError):
        need(False, 'fixture_event_stream_valid')
    need(row.get('children_reaped') is True and row.get('x11_socket_removed') is True,
         'process_reap_socket_cleanup')
    need(row.get('fixture_exit_code') is not None and row.get('xvfb_exit_code') is not None,
         'process_exit_codes_recorded')
    program = row.get('program', {})
    need(program.get('source') == {'observation_seq': 0, 'binding_revision': 0}, 'caller_source_binding')
    need(len([op for op in program.get('ops', []) if op.get('op') == 'key_chord' and
              op.get('keys') == ['CTRL', 'S']]) == 1, 'single_save_chord_program')
    need(program.get('ops', [{}])[-1].get('op') == 'release_all', 'final_release_operation')
    return failures

allocations = sorted(evidence.glob('formal-*/allocation.json'))
rows = [(path.parent, parse_json(path)) for path in allocations]
checks = []
for folder, row in rows:
    failures = validate(row, folder)
    checks.append({'allocation': folder.name, 'allocation_id': row.get('allocation_id'),
                   'checks': 'PASS' if not failures else 'FAIL', 'failures': failures})
valid = [row for _, row in rows]
aggregate_failures = []
if len(rows) != 3:
    aggregate_failures.append('exactly-three-allocations')
if len({r.get('marker') for r in valid}) != len(valid):
    aggregate_failures.append('unique-markers')
if runner_sha != freeze['runner']['sha256']:
    aggregate_failures.append('parent-runner-freeze-hash')
if parent_auditor_sha != freeze['auditor']['sha256']:
    aggregate_failures.append('parent-auditor-freeze-hash')

corruption_tests = []
def challenge(name, mutate):
    baseline_rejections = 0
    for folder, row in rows:
        altered = copy.deepcopy(row)
        mutate(altered)
        if validate(altered, folder):
            baseline_rejections += 1
    corruption_tests.append({'name': name, 'rejected_allocations': baseline_rejections,
                             'total_allocations': len(rows),
                             'pass': baseline_rejections == len(rows)})

challenge('source_revision', lambda r: r['build_metadata'].__setitem__('source_revision', '0'*40))
challenge('artifact_digest', lambda r: r.__setitem__('artifact_sha256', '0'*64))
challenge('effect_marker', lambda r: r['effect'].__setitem__('text', 'tampered'))
challenge('request_digest', lambda r: r['call_records'][0].__setitem__('request_sha256', '0'*64))
challenge('report_digest', lambda r: r['call_records'][1].__setitem__('report_sha256', '0'*64))
challenge('duplicate_observation_id', lambda r: r['post_observation']['metadata']['receipt']['report'].__setitem__(
    'observation_id', r['initial_observation']['metadata']['receipt']['report']['observation_id']))
challenge('post_image_digest', lambda r: r['post_observation']['images'][0].__setitem__('sha256', '0'*64))
def damage_marker_event(row):
    marker = row['marker']
    lines = row['fixture_events']
    for index, line in enumerate(lines):
        event = json.loads(line)
        if marker[0] in event.get('char', ''):
            event['char'] = event['char'].replace(marker[0], '?', 1)
            lines[index] = json.dumps(event, sort_keys=True)
            return
    row['fixture_events'] = []
challenge('fixture_marker_event', damage_marker_event)
def invalidate_release(row):
    for call in row['call_records']:
        if call['operation'] == 'dispatch':
            call['report']['result']['execution']['releases'][0]['verified'] = False
challenge('verified_release', invalidate_release)
challenge('call_order', lambda r: r['call_records'].__setitem__(0, r['call_records'][1]))
if any(not c['pass'] for c in corruption_tests):
    aggregate_failures.append('corruption_controls')
if any(c['checks'] != 'PASS' for c in checks):
    aggregate_failures.append('allocation_reconstruction')

raw_manifest = []
for path in sorted(p for p in evidence.rglob('*') if p.is_file()):
    raw_manifest.append({'path': path.relative_to(evidence).as_posix(),
                         'bytes': path.stat().st_size, 'sha256': sha(path)})

result = {'schema': 'agent-interface/issue-3595-raw-reconstruction-audit-v1',
          'outcome': 'PASS_RAW_RECONSTRUCTION_ONLY' if not aggregate_failures else 'HOLD_OR_FAIL',
          'official_issue_3587_frozen_gate': 'HOLD_OR_FAIL_UNCHANGED',
          'source_revision': freeze['source_revision'], 'artifact_sha256': artifact_sha,
          'parent_runner_sha256': runner_sha, 'parent_frozen_auditor_sha256': parent_auditor_sha,
          'allocation_count': len(rows), 'allocation_checks': checks,
          'corruption_controls': corruption_tests, 'aggregate_failures': aggregate_failures,
          'raw_file_count': len(raw_manifest), 'raw_manifest': raw_manifest,
          'scope': 'immutable raw-only reconstruction; no GUI, Xvfb, runtime, or input'}
(out/'AUDIT_V2.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
(out/'AUDIT_V2.sha256').write_text(sha(out/'AUDIT_V2.json')+'  AUDIT_V2.json\n')
(out/'RAW_SHA256SUMS').write_text(''.join(
    f"{row['sha256']}  {row['path']}\n" for row in raw_manifest))
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not aggregate_failures else 1)
