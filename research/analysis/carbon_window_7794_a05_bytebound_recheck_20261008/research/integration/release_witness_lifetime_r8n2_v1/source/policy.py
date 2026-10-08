"""Observation classification only. No X11 dependency and no input authority."""
from __future__ import annotations
import json
import sys


def classify(request: dict) -> dict:
    result = {'app': 'UNKNOWN', 'server': 'UNKNOWN', 'release_interval_ns': None,
              'authority': 'none', 'task_success': None}
    expected = request['identity']
    events = request.get('app_events', [])
    presses = [e for e in events if e.get('event_type') == 2 and e.get('event_keycode') == expected['keycode']]
    releases = [e for e in events if e.get('event_type') == 3 and e.get('event_keycode') == expected['keycode']]
    if len(presses) == len(releases) == 1 and presses[0]['time_ns'] < releases[0]['time_ns']:
        if all(e.get(k) == expected[k] for e in presses + releases for k in ('epoch', 'actuation', 'keycode')) and all(e.get('pid') == expected['recipient_pid'] and e.get('window') == expected['window'] for e in presses + releases):
            result['app'] = 'APP_RELEASE_OBSERVED'
    before, after = request.get('before'), request.get('after')
    if not isinstance(before, dict) or not isinstance(after, dict):
        return result
    for row, rid in ((before, 'down'), (after, 'post')):
        if row.get('kind') != 'sample' or row.get('request_id') != rid:
            return result
        if any(row.get(k) != expected[k] for k in ('epoch', 'actuation', 'keycode', 'pid')):
            return result
        if type(row.get('key_down')) is not bool:
            return result
        bitmap = row.get('keymap')
        if not isinstance(bitmap, list) or len(bitmap) != 32 or any(type(v) is not int or not 0 <= v < 256 for v in bitmap):
            return result
        code = expected['keycode']
        if type(code) is not int or not 8 <= code <= 255:
            return result
        if bool(bitmap[code // 8] & (1 << (code % 8))) != row['key_down']:
            return result
        if not all(type(row.get(k)) is int and row[k] > 0 for k in ('query_start_ns', 'query_end_ns', 'seq')):
            return result
        if row['query_start_ns'] > row['query_end_ns']:
            return result
    if before['query_end_ns'] > after['query_start_ns'] or before['seq'] >= after['seq']:
        return result
    if not before['key_down']:
        return result
    if after['key_down']:
        result['server'] = 'STILL_DOWN'
    else:
        result['server'] = 'SERVER_RELEASE_OBSERVED'
        result['release_interval_ns'] = [before['query_start_ns'], after['query_end_ns']]
    return result


if __name__ == '__main__':
    print(json.dumps(classify(json.load(sys.stdin)), sort_keys=True))
