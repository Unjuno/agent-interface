"""Isolated killed-lock-owner versus released-lock-owner Event.set probe."""
import json
import multiprocessing as mp
import platform
import time


def hold(event, ready, release):
    with event._cond._lock:  # CPython implementation detail; deliberately inject lock ownership.
        ready.send('held')
        release.recv()


def set_event(event, result):
    start = time.monotonic_ns()
    event.set()
    result.send({'returned': True, 'elapsed_ns': time.monotonic_ns()-start})


def one(kill_while_held):
    ctx = mp.get_context('spawn')
    event = ctx.Event()
    ready_r, ready_w = ctx.Pipe(False)
    release_r, release_w = ctx.Pipe(False)
    result_r, result_w = ctx.Pipe(False)
    holder = ctx.Process(target=hold, args=(event, ready_w, release_r))
    setter = None
    try:
        holder.start()
        if not ready_r.poll(3) or ready_r.recv() != 'held':
            raise RuntimeError('holder did not acquire lock')
        if kill_while_held:
            holder.kill()
        else:
            release_w.send('release')
        holder.join(3)
        if holder.is_alive():
            raise RuntimeError('holder did not exit')
        setter = ctx.Process(target=set_event, args=(event, result_w))
        start = time.monotonic_ns()
        setter.start()
        setter.join(1.0)
        still_alive = setter.is_alive()
        receipt = result_r.recv() if result_r.poll() else None
        return {'arm': 'killed_holding_lock' if kill_while_held else 'released',
                'holder_exitcode': holder.exitcode, 'setter_alive_after_1s': still_alive,
                'elapsed_ns': time.monotonic_ns()-start, 'setter_receipt': receipt}
    finally:
        if setter is not None:
            if setter.is_alive(): setter.kill()
            setter.join(3)
            if setter.is_alive(): raise RuntimeError('setter cleanup failed')
        if holder.is_alive(): holder.kill()
        holder.join(3)
        if holder.is_alive(): raise RuntimeError('holder cleanup failed')
        for conn in (ready_r, ready_w, release_r, release_w, result_r, result_w): conn.close()


if __name__ == '__main__':
    print(json.dumps({'python':platform.python_version(), 'platform':platform.platform(),
                      'start_method':'spawn', 'arms':[one(False),one(True)]}, indent=2))
