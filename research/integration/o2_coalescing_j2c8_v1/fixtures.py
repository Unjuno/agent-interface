"""Fixed synthetic corpus, not screenshots or a stochastic workload."""
import hashlib

CONDITIONS = ('SINGLE', 'CHANGE_BURST', 'UNCHANGED_BURST', 'ABA_BURST',
              'TWO_STREAMS', 'CRITICAL_BURST')
MODES = ('FIFO', 'ENCODE_THEN_SELECT', 'SELECT_THEN_ENCODE')


def make(condition, identity, mode, small=False):
    w, h = (8, 8) if small else (16, 12)
    base = b''.join(hashlib.sha256(('j2c8-' + str(i)).encode()).digest()
                    for i in range((w * h + 31) // 32))[:w * h]
    streams = ('v1', 'v2') if condition == 'TWO_STREAMS' else ('v1',)

    def item(index, stream, kind, pixels=None):
        record = {'event_id': identity + ':' + str(index), 'seq': index,
                  't_ns': 1000000 + index * 1000, 'session': identity,
                  'target': 'target-' + stream, 'stream': stream, 'kind': kind}
        result = {'record': record}
        if pixels is not None:
            result['frame'] = {'width': w, 'height': h, 'mode': 'L',
                               'pixels': bytes(pixels).hex()}
        return result

    bootstrap = [item(i, s, 'FRAME', base) for i, s in enumerate(streams)]
    burst, index = [], len(bootstrap)
    for step in range(1 if condition == 'SINGLE' else 3):
        for s in streams:
            pixels = bytearray(base)
            if condition != 'UNCHANGED_BURST' and not (condition == 'ABA_BURST' and step == 2):
                for j in range(step + 1):
                    pixels[j] ^= 255
            burst.append(item(index, s, 'FRAME', pixels))
            index += 1
        if condition == 'CRITICAL_BURST' and step < 2:
            kind = ('FOCUS_CHANGED', 'EFFECT_VERIFIED')[step]
            burst.append(item(index, 'v1', kind))
            index += 1
    return {'mode': mode, 'bootstrap': bootstrap, 'burst': burst,
            'now_ns': 1000000 + index * 1000, 'max_age_ns': 1000000,
            'tile_size': 4}
