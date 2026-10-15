"""Read the inert saved packet only; no producer imports, sockets or displays."""
import base64
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON key')
        value[key] = item
    return value


def load_json(value):
    return json.loads(value, object_pairs_hook=unique_object)


def verify_original_paths(repository):
    raw = (Path(__file__).resolve().parent / 'ORIGINAL_PATHS.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() ==
            '424e184805c3fedf9e4a444346f16d9c1df7a9e96cc915b3fd32c4ba383b622c', 'original path pin')
    pins = load_json(raw)
    require(pins['source_ref'] == '8394ab7f4a82cafc29a851c28afd56d7a1c8f804' and
            pins['original_paths'] == len(pins['paths']) == 261, 'original source/count')
    for name, digest in pins['paths'].items():
        path = PurePosixPath(name)
        require(name.startswith('research/concurrency/') and '..' not in path.parts and
                ':' not in name and '\\' not in name, 'original path')
        data = repository.joinpath(*path.parts).read_bytes()
        blob = b'blob ' + str(len(data)).encode('ascii') + b'\0' + data
        require(hashlib.sha1(blob).hexdigest() == digest, 'original blob mismatch: ' + name)
    return 261


def decode_packet(root):
    manifest = load_json((root / 'MANIFEST.json').read_bytes())
    encoded = b''.join((root / 'EVIDENCE.json.gz.b64.txt').read_bytes().split())
    compressed = base64.b64decode(encoded, validate=True)
    require(manifest['gzip_sha256'] ==
            '8f088f226e6abe7da8663f5216695ade5abc8a264a7522b6f956d92b59895e7f', 'unqualified gzip pin')
    require(hashlib.sha256(compressed).hexdigest() == manifest['gzip_sha256'], 'gzip hash')
    raw = gzip.decompress(compressed)
    require(len(raw) == manifest['json_bytes'] == 2046932, 'JSON size')
    require(hashlib.sha256(raw).hexdigest() == manifest['json_sha256'] ==
            '360fcda2f2c8e3671f703ecd01ef57908bea880315be36709fdfd242165f64d6', 'JSON hash')
    require(manifest['members'] == 274, 'member count pin')
    return load_json(raw)


def verify_members(document):
    encoded = document['files']
    projection = document['projection_manifest']
    require(type(encoded) is dict and len(encoded) == 274, 'member count')
    require(type(projection) is list and len(projection) == 274, 'projection count')
    seen, files = set(), {}
    for record in projection:
        name = record['path']
        require(type(name) is str and bool(name) and ':' not in name and '\\' not in name,
                'member path')
        path = PurePosixPath(name)
        require(not path.is_absolute() and '..' not in path.parts and name not in seen,
                'unsafe or duplicate member')
        seen.add(name)
        data = base64.b64decode(encoded[name], validate=True)
        require(type(record['public_bytes']) is int and len(data) == record['public_bytes'],
                'public size mismatch')
        require(hashlib.sha256(data).hexdigest() == record['public_sha256'], 'public hash mismatch')
        files[name] = data
    require(seen == set(encoded), 'projection coverage')
    return files


def events_of(value):
    events = value['events']
    require(type(events) is list and bool(events), 'events missing')
    require(all(type(row['ns']) is int and row['ns'] > 0 for row in events), 'event clock type')
    require(all(a['ns'] <= b['ns'] for a, b in zip(events, events[1:])), 'event clock order')
    return events


def event_time(events, kind, label=None):
    rows = [row for row in events if row['kind'] == kind and
            (label is None or row.get('label') == label)]
    require(len(rows) == 1, 'ambiguous or missing event: ' + kind)
    return rows[0]['ns']


def zero(value):
    return type(value) is int and value == 0


def same(value, expected):
    if type(value) is not type(expected):
        return False
    if type(expected) is dict:
        return set(value) == set(expected) and all(same(value[k], v) for k, v in expected.items())
    if type(expected) is list:
        return len(value) == len(expected) and all(same(a, b) for a, b in zip(value, expected))
    return value == expected


def verify_boundaries(files):
    server = load_json(files['xlib-server-stop-70ab/RESULT.json'])
    require(server['status'] == 'PASS_READ_ONLY_SERVER_GLOBAL_STOP', 'server disposition')
    require(server['source'] == '274ea957d13b7132e9c62a9adcfc806c8e2d9bb6', 'server source')
    require(server['error'] is None and zero(server['input_emissions']), 'server input/error')
    require(same(server['snapshots']['server_stopped'],
            {'alive': [True, True], 'completed': {}}), 'both queries must remain pending')
    after = server['snapshots']['after_main_shutdown']
    require(same(after['alive'], [False, True]) and set(after['completed']) == {'main'},
            'shutdown must not complete independent query')
    require(after['completed']['main'].get('error') == "ConnectionClosedError('server')",
            'main shutdown outcome')
    require(same(server['completed'], {
        'main': {'error': "ConnectionClosedError('server')"},
        'independent': {'map': '00' * 32}}), 'final query outcomes')
    require(same(server['threads_alive_final'], [False, False]) and zero(server['Xvfb_exit']),
            'server/thread cleanup')
    events = events_of(server)
    stop = event_time(events, 'server_stop')
    shutdown = event_time(events, 'main_shutdown')
    resume = event_time(events, 'server_resume')
    require(stop < event_time(events, 'query_start', 'main') < shutdown and
            stop < event_time(events, 'query_start', 'independent') < shutdown <
            event_time(events, 'query_error', 'main') < resume <
            event_time(events, 'query_return', 'independent'), 'server stop/shutdown/resume order')

    timeout = load_json(files['python-xlib-timeout-70ab/RESULT.json'])
    require(timeout['status'] == 'OBSERVED_SOCKET_TIMEOUT_DOES_NOT_BOUND_REPLY_WAIT',
            'timeout disposition')
    require(same(timeout['Xlib_version'], [0, 33]) and timeout['actual_X_server'] is False and
            zero(timeout['actual_input_opcodes']), 'transport scope')
    gate = timeout['pre_gate']
    require(gate['socket_timeout_seconds'] == .05 and
            type(gate['additional_no_reply_hold_ns']) is int and
            gate['additional_no_reply_hold_ns'] >= 200_000_000, 'original no-reply hold')
    require(same(gate['blocked_alive'], [True, True]) and
            same(gate['completed'], {'independent': [1, 1, 0]}), 'connection contrast')
    require(same(timeout['completed'], {name: [1, 1, 0] for name in
            ('independent', 'blocked_first', 'blocked_second')}) and timeout['errors'] == [] and
            type(timeout['retired_threads']) is int and timeout['retired_threads'] == 5,
            'transport final state')
    events = events_of(timeout)
    release = event_time(events, 'release_peer_gate')
    for name in ('blocked_first', 'blocked_second'):
        require(event_time(events, 'query_start', name) < release <
                event_time(events, 'query_end', name), 'blocked query completion order')
    require(event_time(events, 'query_start', 'independent') <
            event_time(events, 'query_end', 'independent') < release, 'independent reply order')
    requests = [row for row in events if row['kind'] == 'peer_request']
    require(len(requests) == 3 and all(type(row['opcode']) is int and row['opcode'] == 106
                                     for row in requests), 'read-only request opcodes')
    return ['server_global_stop', 'socket_timeout_not_logical_deadline']


if __name__ == '__main__':
    packet = Path(__file__).resolve().parent.parent / 'python_xlib_boundary_17_20261004_70ab'
    original_paths = verify_original_paths(Path(__file__).resolve().parents[3])
    members = verify_members(decode_packet(packet))
    print(json.dumps(dict(status='PASS_SAVED_BOUNDARIES', public_members=len(members),
                          original_paths=original_paths,
                          checked=verify_boundaries(members), producer_replays=0,
                          scope='saved historical read-only evidence; no held-input/physical bound'), indent=2))
