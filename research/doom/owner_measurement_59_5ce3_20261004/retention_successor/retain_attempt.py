"""Research-only ordinary child failure retention; no native execution by itself."""
import json
from pathlib import Path
import subprocess
import time


def run(command, output, timeout):
    output = Path(output)
    # Reserve before opening logs or starting the child. Never reuse an attempt.
    with (output / 'ATTEMPT.json').open('x') as stream:
        json.dump(dict(command=command, timeout_seconds=timeout,
            started_ns=time.perf_counter_ns()), stream)
        stream.flush()
    result = dict(disposition='STOP_CHILD_START', exit_code=None)
    process = None
    try:
        with (output / 'stdout.txt').open('x') as stdout, (output / 'stderr.txt').open('x') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            try:
                code = process.wait(timeout=timeout)
                result.update(exit_code=code, disposition='PASS_CHILD_EXIT' if code == 0 else 'STOP_CHILD_EXIT')
            except subprocess.TimeoutExpired:
                process.kill()
                result.update(exit_code=process.wait(timeout=2), disposition='STOP_CHILD_TIMEOUT')
    except Exception as error:
        result['error'] = repr(error)
        if process is not None and process.poll() is None:
            process.kill()
            result['exit_code'] = process.wait(timeout=2)
    finally:
        result['finished_ns'] = time.perf_counter_ns()
        with (output / 'TERMINAL.json').open('x') as stream:
            json.dump(result, stream, indent=2)
    return result
