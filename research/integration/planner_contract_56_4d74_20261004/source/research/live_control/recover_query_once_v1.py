"""One command-free read of one identified pending saved-effect query."""
from pathlib import Path
from append_checkpoint_v1 import load
from durable_submit_v5 import run
from unix_json_deadline import exchange


def recover_query_once(path, request_id, timeout=3, transport=exchange):
    if type(request_id) is not str or not 1 <= len(request_id) <= 128:
        raise ValueError('original query request ID required')

    def guarded(session, request, **kwargs):
        # durable run holds the journal lock through this callback and commit.
        state = load(Path(path))
        pending = state['pending']
        if pending is None:
            raise ValueError('no pending query to reconcile')
        original = pending['request']
        if original['command']['op'] != 'effect_checkpoint':
            raise ValueError('pending operation is not an artifact query')
        if original['request_id'] != request_id:
            raise ValueError('original query identity changed')
        if 'command' in request or request.get('read_request_id') != request_id:
            raise ValueError('recovery must read the original query without a command')
        return transport(session, request, **kwargs)

    # Timeout, conflict or closed-without-evidence stays pending; errors propagate.
    # This function neither retries the query nor interprets its effect as success.
    return run(path, {'timeout': timeout}, guarded)
