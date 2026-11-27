"""Offline raw reconstruction; no runtime imports, Pillow, X server or trial replay."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib

HERE = Path(__file__).resolve().parent


def png_rgb(raw):
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('PNG signature')
    pos, compressed, header = 8, bytearray(), None
    while pos < len(raw):
        size = struct.unpack('>I', raw[pos:pos+4])[0]
        kind = raw[pos+4:pos+8]
        data = raw[pos+8:pos+8+size]
        crc = struct.unpack('>I', raw[pos+8+size:pos+12+size])[0]
        if zlib.crc32(kind + data) != crc:
            raise ValueError('PNG CRC')
        if kind == b'IHDR':
            header = struct.unpack('>IIBBBBB', data)
        elif kind == b'IDAT':
            compressed.extend(data)
        pos += size + 12
        if kind == b'IEND':
            break
    width, height, depth, kind, compression, filtering, interlace = header
    if (depth, kind, compression, filtering, interlace) != (8, 2, 0, 0, 0):
        raise ValueError('requires RGB8 non-interlaced')
    pixels = zlib.decompress(compressed)
    stride = width * 3
    if len(pixels) != height * (stride + 1):
        raise ValueError('scanline length')
    result, previous = bytearray(), bytearray(stride)
    for y in range(height):
        offset = y * (stride + 1)
        mode, row = pixels[offset], bytearray(pixels[offset+1:offset+1+stride])
        for x in range(stride):
            left = row[x-3] if x >= 3 else 0
            up, corner = previous[x], previous[x-3] if x >= 3 else 0
            if mode == 0:
                predictor = 0
            elif mode == 1:
                predictor = left
            elif mode == 2:
                predictor = up
            elif mode == 3:
                predictor = (left + up) // 2
            elif mode == 4:
                prediction = left + up - corner
                distances = (abs(prediction-left), abs(prediction-up), abs(prediction-corner))
                predictor = (left, up, corner)[distances.index(min(distances))]
            else:
                raise ValueError('PNG filter')
            row[x] = (row[x] + predictor) & 255
        result.extend(row)
        previous = row
    return width, height, bytes(result)


def audit():
    checks = []
    def check(name, predicate):
        checks.append({'check': name, 'passed': bool(predicate)})
        if not predicate:
            raise ValueError(name)
    def load(name):
        return json.loads((HERE / name).read_text())
    report = load('result.json')
    check('one successful process-scoped invocation', load('launch.json')['exit_code'] == 0
          and report['status'] == 'PASS_OBSERVATION_SCOPED' and len(report['observations']) == 2)
    requests = list((HERE / 'mcp').glob('*/request.json'))
    check('exactly two observes and one close request', len(requests) == 3
          and sorted(json.loads(p.read_text())['operation'] for p in requests) == ['close', 'observe', 'observe'])
    sessions = set()
    for index, expected in enumerate((bytes((255, 0, 0)), bytes((0, 255, 0)))):
        raw = (HERE / ('observation-' + str(index) + '.png')).read_bytes()
        width, height, pixels = png_rgb(raw)
        check('literal full RGB image ' + str(index), (width, height) == (64, 64)
              and pixels == expected * 4096)
        damaged = bytearray(raw)
        damaged[45] ^= 1
        rejected = False
        try:
            png_rgb(damaged)
        except ValueError:
            rejected = True
        check('CRC corruption rejected ' + str(index), rejected)
        entry = report['observations'][index]
        native_report = load('mcp/' + entry['call_id'] + '/report.json')
        native = native_report['observation']
        sessions.add(native_report['session']['session_id'])
        check('native timestamps match recorded interval ' + str(index),
            entry['capture_started_ns'] == native['capture_started_ns']
            and entry['capture_ended_ns'] == native['capture_ended_ns']
            and entry['app_sync_returned_ns'] <= entry['call_started_ns']
            <= native['capture_started_ns'] <= native['capture_ended_ns'] <= entry['call_returned_ns'])
        check('no input/authority in native report ' + str(index), native_report['input_dispatched'] is False
              and native_report['side_effect_authority'] is False and native_report['status'] == 'returned')
        artifact = native['artifact']
        digest = hashlib.sha256(raw).hexdigest()
        local_path = HERE / 'mcp' / entry['call_id'] / 'images' / Path(artifact['path']).name
        check('raw artifact bytes/hash ' + str(index), local_path.read_bytes() == raw
              and artifact['sha256'] == digest == entry['png_sha256'] and artifact['bytes'] == len(raw))
        original = load('observe-' + str(index) + '-reply-0.json')
        retained = load('retained-' + str(index) + '-reply-0.json')
        metadata = json.loads(retained['content'][0]['text'])
        check('retained bytes and no replay ' + str(index),
              original['content'][1]['data'] == retained['content'][1]['data']
              and base64.b64decode(retained['content'][1]['data'], validate=True) == raw
              and metadata['operation_invoked'] is False and metadata['call_id'] == entry['call_id'])
    check('persistent session reused', len(sessions) == 1)
    close = report['public_close_report']
    check('public close without input release', close['status'] == 'closed'
          and close['release_attempted'] is False and close['connection_close_attempted'] is True
          and close['session_id'] in sessions)
    check('Xvfb clean exit', report['xvfb_exit_code'] == 0 and 'cleanup_error' not in report)
    cleanup = load('cleanup-recheck.json')
    check('independent post-exit absence', cleanup['old_pid'] == report['pid']
          and cleanup['old_pid_present'] is False and cleanup['lock_present'] is False
          and cleanup['pathname_socket_present'] is False and cleanup['checked_monotonic_ns'] >= report['ended_ns'])
    check('no input claimed', report['input_operations'] == 0)
    return {'status': 'PASS_RAW_RECONSTRUCTION', 'checks': checks}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
