"""Opt-in single command-free pending read; no input retry or success inference."""
from pathlib import Path
from durable_submit_v4 import run
from append_checkpoint_v1 import load
from unix_json_deadline import exchange


def recover_once(path, timeout=3, transport=exchange):
    def guarded(session, request, **kwargs):
        # run holds the existing exclusive journal lock through this callback.
        state = load(Path(path))
        pending = state['pending']
        if pending is None:
            raise ValueError('no pending command to reconcile')
        if 'command' in request:
            raise ValueError('recovery must be command-free')
        command = pending['request']['command']
        if command['op'] == 'submit' and request.get('action_id') != command['id']:
            raise ValueError('pending action mismatch')
        return transport(session, request, **kwargs)

    # Existing run chooses clock/terminal boundary from the pending command.
    # It preserves pending on timeout/conflict; transport errors propagate.
    return run(path, {'timeout': timeout}, guarded)
