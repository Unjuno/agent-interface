"""Run the real harness, stopping its owner just before the first reply commit.

The primary assistant still supplies the action through the normal exchange.
An external supervisor must verify the checkpoint PID identity before killing
the stopped owner. No input replay, owner restart, or release inference here.
"""
import json
import os
from pathlib import Path
import signal
import sys
import time

import run_native_calc_self_use_v1 as harness
from native_exchange_v1 import encoded, publish


def identity(pid):
    # starttime is field 22; comm can contain spaces or parentheses.
    row = Path(f'/proc/{pid}/stat').read_text()
    return {'pid': pid, 'starttime': row[row.rfind(')')+2:].split()[19]}


def main():
    out = Path(sys.argv[sys.argv.index('--out')+1]).resolve()
    original_session, original_prepare = harness.PrivateSession, harness.suite.prepare
    processes = []

    class RecordedSession(original_session):
        def _popen(self, args, **kwargs):
            process = super()._popen(args, **kwargs)
            processes.append(dict(identity(process.pid), executable=Path(args[0]).name))
            (out/'processes.json').write_bytes(encoded(processes))
            return process

        def __init__(self):
            super().__init__()
            publish(out/'private-session.json', encoded({'display': self.name, 'owner': identity(os.getpid())}))

    def prepare(*args, **kwargs):
        result = original_prepare(*args, **kwargs)
        publish(out/'live-output.json', encoded({'path': str(result[1])}))
        return result

    def checkpoint(path, data):
        if Path(path).name == 'reply-1.json':
            publish(out/'before-reply.json', encoded({
                'phase': 'after_action_and_review_before_reply_commit',
                'owner': identity(os.getpid()), 'monotonic_ns': time.monotonic_ns(),
                'reply_would_be': json.loads(data), 'input_replay_allowed': False}))
            os.kill(os.getpid(), signal.SIGSTOP)
            raise RuntimeError('stopped owner must not resume input or reply publication')
        return publish(path, data)

    harness.PrivateSession = RecordedSession
    harness.suite.prepare = prepare
    harness.publish = checkpoint
    harness.main()


if __name__ == '__main__':
    main()
