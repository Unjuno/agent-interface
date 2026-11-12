"""Outer research attempt boundary; launcher return is not task success."""
import json
import os
from pathlib import Path
import time

def write_once(path, row):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(row, stream, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())

def record_launch(directory, launch, *, planned_stages):
    started = time.monotonic_ns()
    root = Path(directory)
    root.mkdir(exist_ok=False)
    write_once(root/'attempt-start.json', {
        'schema':'integrated-launch-attempt-v1','started_ns':started,
        'planned_stages':list(planned_stages), 'replay_allowed':False,
        'note':'Start record does not prove invocation or completion.'})
    terminal={'status':'unknown','usage':None,'usage_status':'unavailable',
              'task_success':None,'cleanup_status':'unverified','replay_allowed':False}
    try:
        value=launch()
        terminal['status']='launcher_returned'
        return value
    except BaseException as error:
        terminal.update(status='launcher_raised',error_type=type(error).__name__)
        if isinstance(error,SystemExit):
            terminal['exit_code']=error.code if type(error.code) is int else None
        raise
    finally:
        ended=time.monotonic_ns()
        terminal.update(started_ns=started,ended_ns=ended,elapsed_ns=ended-started,
                        scope='outer invocation only; nested stages require their own receipts')
        write_once(root/'attempt-terminal.json',terminal)
