"""Fixture-only saved-artifact checkpoint; no GUI action or controller oracle."""
import hashlib
import time
from score_drag_v1 import score


def checkpoint(engine, events, output, directory, command):
    if set(command) - {'op', 'save_id', 'transport_request_id'} or not isinstance(command.get('save_id'), str):
        raise ValueError('effect requires save_id')
    # Serialize against program admission/completion. Main loop is the only submitter.
    with engine.lock:
        if engine.active is not None:
            raise ValueError('effect requires idle executor')
        terminals = [e for e in events if e['event'] == 'terminal']
        if not terminals or terminals[-1]['id'] != command['save_id'] or terminals[-1]['status'] != 'completed':
            raise ValueError('effect requires latest completed save program')
        terminal = terminals[-1]
        submissions = [e['command'] for e in events if e['event'] == 'command' and e['command'].get('op') == 'submit' and e['command'].get('id') == command['save_id']]
        expected = [{'op': 'chord', 'modifier': 'Control_L', 'key': 's'}, {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}]
        if len(submissions) != 1 or submissions[0]['steps'] != expected:
            raise ValueError('effect requires declared save/settle steps')
        data = output.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        artifact = directory / ('effect-' + sha + '.svg')
        if not artifact.exists():
            with artifact.open('xb') as stream:
                stream.write(data)
        if artifact.read_bytes() != data:
            raise ValueError('effect artifact mismatch')
        return dict(event='saved_effect', save_id=command['save_id'], save_terminal_ns=terminal['terminal_ns'],
                    svg_sha256=sha, artifact=str(artifact.resolve()), score=score(artifact),
                    sampled_ns=time.perf_counter_ns(), authority='none; independent benchmark evaluator only',
                    scope='saved bytes after completed GUI save/settle; not proof all unsaved GUI state is persisted')
