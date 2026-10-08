"""A02 stable-source qualification; independent of observer decoding."""
import base64
import struct

def integer(value):
    if type(value) is not int: raise ValueError('exact timestamp/identity integer')
    return value

def qualify(source, capture):
    events = {integer(e['id']): e for e in source['events']}
    if len(events) != len(source['events']): raise ValueError('duplicate source identity')
    stable, boundary, unknown = set(), 0, 0
    for frame in capture['frames']:
        start, end = integer(frame['start_ns']), integer(frame['native_return_ns'])
        if start > end: raise ValueError('acquisition chronology')
        raw = base64.b64decode(frame['pixels_b64'], validate=True)
        if len(raw) != 4096: raise ValueError('complete native pixels')
        pixels = struct.unpack('<1024I', raw)
        identity, color = pixels[:2]
        if 1 <= identity <= 8 and color in (0xFF0000, 0x00FF00) and len(set(pixels[1:])) == 1:
            e = events.get(identity)
            if e is None or integer(e['color']) != color: raise ValueError('source membership/color')
            ds, de, cs, ce = [integer(e[k]) for k in ('draw_start_ns','draw_end_ns','clear_start_ns','clear_end_ns')]
            if not ds <= de <= cs <= ce: raise ValueError('source chronology')
            if start > ce or end < ds: raise ValueError('source possible overlap')
            if de <= start <= end <= cs: stable.add(identity)
            else: boundary += 1
        elif any(pixels): unknown += 1
    return {'stable_ids': sorted(stable), 'boundary_hits': boundary, 'unknown_frames': unknown}
