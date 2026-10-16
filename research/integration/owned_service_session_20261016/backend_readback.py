"""Offline audit of selected-backend evidence; no runtime/process imports."""
import base64
import copy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import struct
import zlib
HERE = Path(__file__).resolve().parent
CASES = {'normal', 'cancel', 'inflight', 'blocked', 'stale', 'original-ordinary-binding', 'concurrent-close', 'window-lifecycle-refused', 'program-capabilities', 'startup-cleanup', 'surface-validation', 'unverified-release'}

def need(value, reason):
    if not value:
        raise ValueError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def sources(pins):
    for digest in pins.values():
        need(sha((HERE / 'sources' / (digest + '.py.txt')).read_bytes()) == digest, 'source hash')

def decode_files(items):
    result = {}
    for name, item in items.items():
        raw = base64.b64decode(item['bytes_b64'], validate=True)
        need(sha(raw) == item['sha256'], 'raw hash ' + name)
        result[name] = raw
    return result

def rgb_png(blob):
    need(blob[:8] == b'\x89PNG\r\n\x1a\n', 'PNG signature')
    position = 8
    idat = bytearray()
    header = None
    while position < len(blob):
        count = struct.unpack('>I', blob[position:position + 4])[0]
        kind = blob[position + 4:position + 8]
        payload = blob[position + 8:position + 8 + count]
        crc = struct.unpack('>I', blob[position + 8 + count:position + 12 + count])[0]
        need(zlib.crc32(kind + payload) & 4294967295 == crc, 'PNG chunk CRC')
        position += count + 12
        if kind == b'IHDR':
            header = struct.unpack('>IIBBBBB', payload)
        if kind == b'IDAT':
            idat.extend(payload)
        if kind == b'IEND':
            break
    need(header is not None and header[:2] == (32, 32) and (header[2:] == (8, 2, 0, 0, 0)), 'fixture PNG format')
    raw = zlib.decompress(idat)
    stride = 96
    need(len(raw) == 32 * (stride + 1), 'PNG decompressed shape')
    result = bytearray()
    previous = bytearray(stride)
    for index in range(32):
        kind = raw[index * (stride + 1)]
        line = bytearray(raw[index * (stride + 1) + 1:(index + 1) * (stride + 1)])
        need(kind in range(5), 'PNG filter')
        for i in range(stride):
            left = line[i - 3] if i >= 3 else 0
            above = previous[i]
            corner = previous[i - 3] if i >= 3 else 0
            if kind == 0:
                prediction = 0
            elif kind == 1:
                prediction = left
            elif kind == 2:
                prediction = above
            elif kind == 3:
                prediction = (left + above) // 2
            else:
                p = left + above - corner
                distances = (abs(p - left), abs(p - above), abs(p - corner))
                prediction = (left, above, corner)[distances.index(min(distances))]
            line[i] = line[i] + prediction & 255
        result.extend(line)
        previous = line
    return bytes(result)

def audit(data, mode):
    need((data['tests'], data['failures'], data['errors'], data['skipped'], data['optimize']) == (208, 0, 0, 0, mode), 'suite')
    need(len(data['modules']) == 27 and len(data['adapter_rows']) == len(CASES) and ({r['case'] for r in data['adapter_rows']} == CASES), 'inventory')
    need(tuple((len(data[k]) for k in ('cancel_rows', 'boundary_rows', 'process_rows', 'rpc_rows'))) == (11, 3, 13, 26), 'regression row inventory')
    sources(data['source_sha256_lf'])
    pids = set()
    generations = set()
    for row in data['adapter_rows']:
        case = row['case']
        if case == 'original-ordinary-binding':
            need(set(row['rejected']) == {'target_process_identity', 'deadline', 'intent_token'} and row['sends'] == 0 and row['restore_retry_refused'], 'ordinary original-source fence')
            continue
        if case == 'concurrent-close':
            need(not row['first']['verified'] and (not row['after']['verified']) and row['retained'], 'concurrent close unknown sticky')
            continue
        if case == 'window-lifecycle-refused':
            need(row['before_resources'], 'window refusal')
            continue
        if case == 'program-capabilities':
            need(len(row['rejected']) == 4 and row['supported_validate'], 'whole-program capability refusal')
            continue
        if case == 'startup-cleanup':
            need(len(row['outcomes']) == 2 and all((x['cleanup'] == ['ordinary', 'channels'] and x['owned_handle_retained'] for x in row['outcomes'])), 'startup custody')
            continue
        if case == 'surface-validation':
            need(row['invalid_xids_refused'] == 5 and row['bad_geometry_quarantined'] and (row['sends'] == 1), 'surface bounds/quarantine')
            continue
        if case == 'unverified-release':
            need(row['retained'], 'release false retained')
            continue
        files = decode_files(row['files'])
        parent = decode_files(row['parent_artifacts'])
        startup = row['startup']
        need(json.loads(files['startup.json']) == startup, 'accepted startup')
        need(startup['display'] == ':fake' and startup['python_optimize'] == mode and (startup['cancellation_enabled'] is True), 'child conditions')
        need(startup['pid'] == row['spawn_pid'] or startup['parent_pid'] == row['spawn_pid'], 'owned lineage')
        need(startup['service_id'] not in generations, 'unique service')
        generations.add(startup['service_id'])
        pids.update((startup['pid'], row['spawn_pid']))
        sources(startup['source_sha256_lf'])
        identity = {k: startup[k] for k in ('service_id', 'display', 'pid', 'parent_pid', 'supervisor_pid', 'owner_id')}
        recovery = json.loads(files['recovery.json'])
        finish = json.loads(files['finish.json'])
        control = json.loads(files['control.json'])
        need(control['identity'] == recovery['identity'] == finish['identity'] == identity, 'service/owner join')
        need(recovery['startup_sha256'] == finish['startup_sha256'] == sha(files['startup.json']), 'startup hash')
        need(recovery['control_sha256'] == sha(files['control.json']) and finish['recovery_sha256'] == sha(files['recovery.json']), 'control/recovery hash chain')
        need(finish['initial_verification'] is recovery['verified'], 'initial result immutable')
        need(row['service_report']['verified'] and (not row['service_report']['process_alive']) and (row['service_report']['exit_code'] == 0), 'eventual owned cleanup')
        need(row['service_report']['recovery'] == recovery and row['service_report']['finish'] == finish and recovery['verified'] and finish['verified'], 'eventual saved cleanup')
        need(control['control']['error'] is None and control['control']['thread_stopped'], 'control joined')
        edge_rows = [json.loads(line) for line in files.get('fixture-edges.jsonl', b'').splitlines()]
        need(edge_rows == row['edges'] and all((e['pid'] == startup['pid'] for e in edge_rows)), 'edge ownership/raw')
        need([e['event'] for e in edge_rows] == ([] if case == 'stale' else [2, 3]), 'input sequence')
        observation = row['observation']
        binding = observation['pointer_binding']
        need(binding == {'focus': 41, 'surface': 41, 'geometry': [0, 0, 32, 32]} and row['pointer_program_refused'], 'actual remote geometry/full-program refusal')
        need(sha(rgb_png(parent[PureWindowsPath(observation['image']).name])) == observation['frame_rgb_sha256'], 'published image/capture RGB')
        need(len(parent['001.ait']) == observation['wire_bytes'], 'wire artifact retained')
        source = observation['target_process_identity']
        need(source == dict(sequence=1, surface=41, digest=('b' if case == 'stale' else 'a') * 64), 'captured source')
        accepted = next((e for e in row['events'] if e.get('event') == 'accepted'))
        admissions = [e for e in row['events'] if e.get('event') == 'input_admission']
        if case != 'stale':
            need(len(admissions) == 1 and admissions[0]['owner_id'] == startup['owner_id'], 'selected owner admission')
            need(admissions[0]['target_process_identity'] == [source['sequence'], source['surface'], source['digest'], accepted['valid_until_ns']], 'original capture-to-press binding')
        else:
            need(not admissions, 'stale source no admission')
        terminal = row['terminal']
        closed = row['adapter_close']
        need(closed['service_id'] == startup['service_id'] and closed['owner_id'] == startup['owner_id'], 'adapter custody identity')
        if case in ('cancel', 'inflight'):
            before = row['before_resume']
            cause = before['cause']
            record = cause['record']
            need(before['worker_alive'] and (not before['resume_set']) and ([e['event'] for e in before['edges']] == [2, 3]), 'release before worker resume')
            need(cause['intent_token'] == accepted['intent_token'] and record['intent_token'] == accepted['intent_token'] and record['verified'], 'original parent cause')
            need(record['target_process_identity'] == admissions[0]['target_process_identity'], 'cause source')
        if case == 'blocked':
            first = row['first_control']
            need(first['accepted'] and (not first['release_verified']) and (first['cause'] is None), 'first unverified control')
            need(row['before_resume']['worker_alive'] and row['before_resume']['cause'] is None, 'unresolved parent cause')
            need(terminal['status'] == 'failed' and terminal['release']['verified'] is False and terminal['input_recovery_required'], 'terminal failure custody')
            need(row['owner_obligation'] is not None and closed['obligation'] == row['owner_obligation'] and (not closed['verified']), 'late cleanup never clears obligation')
            need(row['custody']['release_obligation'] is not None and row['custody']['owner_service_obligation'] == row['owner_obligation'], 'backend/executor custody')
            need(row['replacement_refused'] and row['close_unchanged'], 'replacement/close fence')
        elif case == 'stale':
            need(terminal['status'] == 'failed' and row['owner_obligation'] is not None and (not closed['verified']), 'stale refusal remains owned')
        else:
            need(terminal['status'] == ('completed' if case == 'normal' else 'cancelled') and terminal['release']['verified'] and closed['verified'] and (row['owner_obligation'] is None), 'positive cleanup')
    for row in data['cancel_rows'] + data['boundary_rows'] + data['process_rows']:
        if row.get('startup'):
            pids.update((row['startup']['pid'], row['spawn_pid']))
        if row.get('client_ready'):
            pids.update((row['client_ready']['pid'], row['client_spawn_pid']))
        if row.get('case') == 'startup-failure':
            failure = json.loads(base64.b64decode(row['files']['failure.json']['bytes_b64']))
            pids.update((failure['pid'], row['spawn_pid']))
    return sorted(pids)
