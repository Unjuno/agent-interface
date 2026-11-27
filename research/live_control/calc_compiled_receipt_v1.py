"""Conservative, offline projection of a Calc decision-receipt-v4.

Historical image references are never fresh observations or input authority.
"""
import re


def map_receipt(receipt):
    result = {'disposition': 'stop', 'delivery': 'unknown',
              'release': 'unknown', 'completed_steps': None,
              'replay_permitted': False, 'task_success': None,
              'reason': 'invalid_receipt', 'evidence': None}
    if (type(receipt) is not dict or receipt.get('format') != 'decision-receipt-v4' or
            receipt.get('reported_state') != 'terminal'):
        return result
    terminals = receipt.get('terminals')
    if type(terminals) is not list or len(terminals) != 1 or type(terminals[0]) is not dict:
        return result
    terminal = terminals[0].get('record')
    if type(terminal) is not dict or terminal.get('event') != 'terminal':
        return result
    steps = terminal.get('steps_completed')
    may_write = receipt.get('program_write_may_have_been_attempted')
    if type(steps) is not int or steps < 0 or type(may_write) is not bool:
        return result
    status = terminal.get('status')
    if type(status) is not str or not status:
        return result
    result['completed_steps'] = steps
    result['reason'] = terminal.get('decision_reason') if type(terminal.get('decision_reason')) is str else status
    release = terminal.get('release')
    if (type(release) is dict and release.get('verified') is True and
            release.get('keys_down') == [] and release.get('buttons_down') == [] and
            release.get('keys_unknown') == []):
        result['release'] = 'verified_empty'
    image = receipt.get('image')
    if type(image) is dict and image.get('status') == 'image':
        path, digest = image.get('relative_path'), image.get('sha256')
        if (type(path) is str and path and '/' not in path and '\\' not in path and
                path not in ('.', '..') and type(digest) is str and
                re.fullmatch(r'[0-9a-f]{64}', digest)):
            result['evidence'] = {'reference': path, 'sha256': digest, 'fresh': False,
                                  'retrievable': 'unverified'}
    if (status == 'completed' and result['release'] == 'verified_empty' and
            (steps == 0 or may_write is True)):
        result['disposition'] = 'completed_unverified'
    return result