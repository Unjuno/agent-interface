"""Candidate partial-startup record classifier; not E03 official auditor."""


def classify_partial_stop(row, stdout, stderr, imports_present):
    if type(row) is not dict or type(stdout) is not bytes or type(stderr) is not bytes:
        raise ValueError('invalid record/stream types')
    if imports_present is not False or stdout != b'' or not stderr.strip():
        raise ValueError('not a partial-startup empty-output failure')
    if type(row.get('child_exit')) is not int or row['child_exit'] == 0:
        raise ValueError('missing failed child terminal')
    if row.get('release_gate') is not False or row.get('outcome_gate') is not False:
        raise ValueError('failed gates must be literal false')
    if row.get('cleanup_faults') != [] or row.get('unhandled') != []:
        raise ValueError('unresolved cleanup or reader failure')
    for field in ('case', 'id', 'fatal'):
        if type(row.get(field)) is not str or not row[field].strip():
            raise ValueError('missing failure identity or exception')
    for field in ('pid', 'start_ns', 'end_ns'):
        if type(row.get(field)) is not int or row[field] <= 0:
            raise ValueError('missing process/clock identity')
    if row['end_ns'] <= row['start_ns']:
        raise ValueError('unordered process lifetime')
    command = row.get('command')
    if type(command) is not list or not command or any(type(x) is not str or not x for x in command):
        raise ValueError('missing child command')
    allowed = {'case', 'id', 'child_exit', 'start_ns', 'end_ns', 'release_gate',
               'outcome_gate', 'cleanup_faults', 'unhandled', 'fatal', 'pid',
               'command', 'proc_status', 'reader_sha256', 'scope'}
    if set(row) - allowed:
        raise ValueError('partial record contains unknown or exposure fields')
    return {'saved_disposition': 'VERIFIED_PARTIAL_STARTUP_STOP',
            'scientific_pass': False, 'exposure': 'NOT_ESTABLISHED'}
