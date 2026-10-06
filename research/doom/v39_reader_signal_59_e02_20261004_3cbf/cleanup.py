def cleanup(process, thread):
    faults = []
    exit_code = None
    stderr = ''

    def attempt(label, fn):
        try:
            return fn()
        except Exception as exc:
            faults.append(dict(step=label, error=repr(exc)))
    if process is not None:
        attempt('stdin-close', process.stdin.close)
        try:
            exit_code = process.wait(timeout=5)
        except Exception as exc:
            faults.append(dict(step='wait', error=repr(exc)))
            attempt('kill', process.kill)
            exit_code = attempt('wait-after-kill', lambda: process.wait(timeout=5))
    if thread is not None:
        attempt('reader-join', lambda: thread.join(timeout=2))
    if process is not None:
        terminal = attempt('poll', process.poll)
        retired = thread is None or not thread.is_alive()
        if terminal is not None:
            stderr = attempt('stderr-read', process.stderr.read)
        if terminal is not None and retired:
            for name in ('stdout', 'stderr'):
                attempt(name + '-close', getattr(process, name).close)
        else:
            faults.append(dict(step='pipe-close-deferred', error='unreaped child or live reader; avoid blocking stream lock; STOP and container teardown required'))
    return (exit_code, stderr, faults)
