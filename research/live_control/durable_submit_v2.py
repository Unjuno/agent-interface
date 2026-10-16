"""Linux single-writer submit journal. Trusted local state; no lease authority.

Only submit and command-free reads are exposed. No retry/reset escape hatch.
Kernel flock is held through bounded transport and checkpoint commit.
"""
import copy, fcntl, json, os, uuid
from contextlib import contextmanager
from pathlib import Path
from received_continuation_v1 import advance, read_request
from unix_json_deadline import exchange


def store(path, state):
    path = Path(path)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('x', encoding='utf-8') as stream:
            json.dump(state, stream, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def locked(path):
    with Path(str(path) + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def initialize(path, continuation):
    with locked(path):
        if Path(path).exists(): raise ValueError('journal already exists')
        # Validate checkpoint before creating a journal; caller must own this session.
        advance(continuation, continuation['session'], continuation['cursor'],
                {'status': 'timeout', 'cursor': continuation['cursor'], 'records': []})
        store(path, {'format': 'durable-submit-v2', 'continuation': continuation,
                     'pending': None, 'last_resolution': None, 'authority': 'none'})


def reconcile(pending, records):
    if pending is None: return None, None
    p = copy.deepcopy(pending)
    expected = dict(p['request']['command'], transport_request_id=p['request']['request_id'])
    action_id = expected['id']
    for event in records:
        kind = event.get('event')
        if kind == 'command':
            command = event.get('command', {})
            if command == expected and not p['echo_seen']:
                p['echo_seen'] = True
            else:
                # Another command destroys unambiguous attribution in this v1.
                p['conflict'] = True
        if p['conflict'] or not p['echo_seen']: continue
        if (kind == 'rejected' and not p['accepted'] and event.get('op') == 'submit'
                and event.get('id') == action_id
                and event.get('transport_request_id') == p['request']['request_id']
                and event.get('admission') == 'not_admitted'):
            return None, {'request_id': p['request']['request_id'],
                          'rejected': event, 'authority': 'none'}
        if kind == 'accepted' and event.get('id') == action_id:
            p['accepted'] = True
        if kind == 'terminal' and event.get('id') == action_id and p['accepted']:
            release = event.get('release') or {}
            if (release.get('verified') is True and release.get('keys_down') == []
                    and release.get('buttons_down') == []):
                return None, {'request_id': p['request']['request_id'],
                              'terminal': event, 'authority': 'none'}
    return p, None


def run(path, spec, call=exchange):
    with locked(path):
        state = json.loads(Path(path).read_text())
        if state.get('format') != 'durable-submit-v2' or state.get('authority') != 'none':
            raise ValueError('invalid journal')
        if set(spec) - {'command', 'events', 'timeout'}: raise ValueError('unknown option')
        timeout = spec.get('timeout', 2)
        if type(timeout) not in (int, float) or not 0 <= timeout <= 30:
            raise ValueError('timeout must be 0..30')
        c = state['continuation']
        q = read_request(c, spec.get('events', ['terminal']), timeout)
        if 'command' in spec:
            if state['pending'] is not None: raise ValueError('unresolved command; read only')
            command = copy.deepcopy(spec['command'])
            if command.get('op') != 'submit' or 'id' in command or 'transport_request_id' in command:
                raise ValueError('submit only; journal assigns unique identities')
            command['id'] = 'durable-' + uuid.uuid4().hex
            q.update(command=command, request_id=uuid.uuid4().hex, action_id=command['id'])
            state['pending'] = {'request': q, 'write_state': 'may_have_been_sent',
                                'echo_seen': False, 'accepted': False, 'conflict': False}
            # MUST commit before transport, even when no bytes will actually be sent.
            store(path, state)
        elif state['pending']:
            q['action_id'] = state['pending']['request']['command']['id']
        reply = call(c['session'], q, timeout=timeout + 3)
        updated = advance(c, c['session'], q['after'], reply)
        pending, resolution = reconcile(state['pending'], reply['records'])
        state['continuation'] = updated
        state['pending'] = pending
        if resolution: state['last_resolution'] = resolution
        store(path, state)
        return {'request': q, 'reply': reply, 'state': state}
