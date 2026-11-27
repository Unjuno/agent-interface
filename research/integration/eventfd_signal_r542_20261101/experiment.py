"""One-shot Linux eventfd observation and child-death fault injection."""
import json
import multiprocessing as mp
from multiprocessing.reduction import DupFd
import os
import platform
import select
import time


def child(fd_wrapper, ready, gate, result):
    fd = fd_wrapper.detach()
    try:
        ready.send('attached')
        gate.recv()
        poll = select.poll()
        poll.register(fd, select.POLLIN)
        result.send({'readable': bool(poll.poll(0))})
    finally:
        os.close(fd)


def trial(arm):
    context = mp.get_context('spawn')
    fd = os.eventfd(0, os.EFD_CLOEXEC | os.EFD_NONBLOCK)
    ready_r, ready_w = context.Pipe(False)
    gate_r, gate_w = context.Pipe(False)
    result_r, result_w = context.Pipe(False)
    process = context.Process(target=child, args=(DupFd(fd), ready_w, gate_r, result_w))
    try:
        process.start()
        if not ready_r.poll(3) or ready_r.recv() != 'attached':
            raise RuntimeError('child did not attach eventfd')
        if arm == 'kill_then_signal':
            process.kill(); process.join(3)
            if process.is_alive(): raise RuntimeError('child did not die')
        started = time.monotonic_ns()
        if arm != 'unrevoked_control':
            os.eventfd_write(fd, 1)
        elapsed = time.monotonic_ns() - started
        observed = None
        if arm != 'kill_then_signal':
            gate_w.send('go')
            if not result_r.poll(3): raise RuntimeError('child did not report')
            observed = result_r.recv()
            process.join(3)
        if process.is_alive(): raise RuntimeError('child did not exit')
        return {'arm': arm, 'signal_elapsed_ns': elapsed, 'child_exitcode': process.exitcode,
                'child_observation': observed}
    finally:
        if process.is_alive(): process.kill()
        process.join(3)
        if process.is_alive(): raise RuntimeError('fixture cleanup failed')
        os.close(fd)
        for connection in (ready_r, ready_w, gate_r, gate_w, result_r, result_w):
            connection.close()


if __name__ == '__main__':
    print(json.dumps({'python':platform.python_version(), 'platform':platform.platform(),
                      'start_method':'spawn', 'arms':[trial('unrevoked_control'),
                      trial('signal_before_check'), trial('kill_then_signal')]}, indent=2))
