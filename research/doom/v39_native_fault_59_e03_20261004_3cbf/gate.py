import json


def release_gate(row):
    try:
        identifier = row['id']; token = row['expected_token']
        if not isinstance(identifier, str) or not identifier or not isinstance(token, str) or not token:
            return False
        for section, event in [('accepted', 'accepted'), ('cancel', 'cancel_requested'),
                               ('released', 'input_released'), ('terminal', 'terminal')]:
            if row[section]['event'] != event or row[section]['id'] != identifier:
                return False
        if row['accepted']['intent_token'] != token or row['released']['intent_token'] != token:
            return False
        if row['cancel']['matched'] is not True or row['terminal']['status'] != 'cancelled':
            return False
        cause = row['terminal']['interruption']
        if cause['intent_token'] != token or json.dumps(cause['record'], sort_keys=True) != json.dumps(row['released']['owner_release'], sort_keys=True):
            return False
        if row['released']['owner_release']['reason'] != 'cancelled':
            return False
        if row['released']['emit_ns'] >= row['terminal']['emit_ns']:
            return False
        for release in (row['released']['owner_release'], row['terminal']['release']):
            if release['verified'] is not True or release['keys_down'] != [] or release['buttons_down'] != []:
                return False
        if row['before'] != {'keys': [], 'buttons': []} or row['after'] != {'keys': [], 'buttons': []}:
            return False
        if row['held'] != {'keys': [row['right_code']], 'buttons': []}:
            return False
        return type(row['child_exit']) is int and row['child_exit'] == 0 and row['cleanup_faults'] == []
    except (KeyError, TypeError):
        return False


def fault_gate(row):
    try:
        wanted = {'original_fault': ('TimeoutError', None, False),
                  'candidate_fault': ('_SessionReaderFailure', 'JSONDecodeError', False),
                  'candidate_healthy': ('TimeoutError', None, True)}[row['case']]
        if (row['wait_outcome'], row['cause']) != wanted[:2] or row['reader_alive_at_cancel'] is not wanted[2]:
            return False
        expected = {'keys': [row['right_code']], 'buttons': []}
        if row['after_notification'] != expected or row['before_cancel'] != expected:
            return False
        if not (row['held_ns'] < row['wait_start_ns'] <= row['wait_end_ns']
                <= row['notification_sample_ns'] <= row['before_cancel_ns'] < row['cancel_send']['start_ns']):
            return False
        if row['case'] == 'candidate_healthy':
            return row['injected_ns'] is None and row['injection_state'] is None and row['unhandled'] == []
        if row['injection_state'] != expected or not (
                row['held_ns'] < row['fault_requested_ns'] <= row['injected_ns'] <= row['wait_end_ns']):
            return False
        if row['case'] == 'candidate_fault':
            return row['unhandled'] == []
        return (len(row['unhandled']) == 1 and row['unhandled'][0]['thread'] == 'selected-v39-reader'
                and row['unhandled'][0]['type'] == 'JSONDecodeError')
    except (KeyError, TypeError):
        return False
