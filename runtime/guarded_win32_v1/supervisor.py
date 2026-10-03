"""Bound waiting on a caller-owned ordinary verifier child; no input replay."""
import subprocess, time

def run(argv, payload, deadline_ns):
    if type(deadline_ns) is not int or type(payload) is not bytes or len(payload) > 1048576:
        raise ValueError('bounded bytes payload and integer deadline required')
    if time.monotonic_ns() >= deadline_ns:
        return {'status': 'unknown', 'reason': 'deadline_before_start', 'started': False}
    p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        remaining = (deadline_ns - time.monotonic_ns()) / 1000000000.0
        if remaining <= 0:
            raise subprocess.TimeoutExpired(argv, 0)
        out, err = p.communicate(payload, timeout=remaining)
    except subprocess.TimeoutExpired:
        try:
            p.kill()
        except Exception as error:
            # Failed termination must not lose ownership of a live child.
            return {'status': 'unknown', 'reason': 'termination_unconfirmed',
                    'started': True, 'pid': p.pid, 'exit': p.poll(), 'process': p,
                    'termination_error': {'type': type(error).__name__,
                                          'detail': str(error)}}
        try:
            out, err = p.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            return {'status': 'unknown', 'reason': 'termination_unconfirmed', 'started': True, 'pid': p.pid, 'exit': p.poll(), 'process': p}
        except Exception as error:
            return {'status': 'unknown', 'reason': 'termination_unconfirmed',
                    'started': True, 'pid': p.pid, 'exit': p.poll(), 'process': p,
                    'communication_error': {'type': type(error).__name__,
                                            'detail': str(error)}}
        return {'status': 'unknown', 'reason': 'deadline', 'started': True, 'pid': p.pid, 'exit': p.returncode, 'stdout': out, 'stderr': err, 'terminated': p.returncode is not None}
    except Exception as error:
        receipt = {'status': 'unknown', 'reason': 'termination_unconfirmed',
                   'started': True, 'pid': p.pid, 'process': p,
                   'communication_error': {'type': type(error).__name__,
                                           'detail': str(error)}}
        try:
            p.kill()
        except Exception as termination_error:
            receipt['termination_error'] = {
                'type': type(termination_error).__name__,
                'detail': str(termination_error)}
        receipt['exit'] = p.poll()
        return receipt
    return {'status': 'returned' if p.returncode == 0 and time.monotonic_ns() < deadline_ns else 'unknown', 'reason': 'child_exit_or_deadline', 'started': True, 'pid': p.pid, 'exit': p.returncode, 'stdout': out, 'stderr': err, 'terminated': True}
