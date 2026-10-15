"""Opt-in read-only X client; never injects input or closes the input client."""
import queue
import threading
import time
from types import SimpleNamespace
from Xlib import display
from .process_identity import read_linux_x11_process_identity


class QueryUnavailable(RuntimeError):
    pass


def focus_within_target(connection, window_id, *, raise_errors=False):
    try:
        focus = connection.get_input_focus().focus
        seen = set()
        for _ in range(64):
            identifier = getattr(focus,'id',None)
            if type(identifier) is not int or identifier <= 0 or identifier in seen:
                return False
            if identifier == window_id:
                return True
            seen.add(identifier)
            focus = focus.query_tree().parent
    except Exception:
        if raise_errors: raise
        return False
    return False


class X11TargetQueries:
    def __init__(self, display_name):
        self.connection = display.Display(display_name)

    def read(self, operation, xid):
        if operation == 'focus':
            return focus_within_target(self.connection,xid,raise_errors=True)
        if operation == 'process_identity':
            return read_linux_x11_process_identity(self.connection,xid)
        raise ValueError('unknown target query')

    def close(self):
        self.connection.close()


class TargetQueryWorker:
    """One client/thread, one request; retirement is sticky and never waits on I/O.

    A timed-out client closes on its own thread after its blocked call returns.
    This cannot interrupt X, force close, or establish a physical release bound.
    """
    def __init__(self, factory):
        self.factory = factory
        self.lock = threading.Lock()
        self.queue = queue.Queue(maxsize=1)
        self.thread = None
        self.current = None
        self.retired = False
        self.close_error = None

    def snapshot(self):
        with self.lock:
            return dict(retired=self.retired, pending=self.current is not None and not self.current.done.is_set(),
                        thread_alive=self.thread is not None and self.thread.is_alive(),close_error=self.close_error)

    def close(self):
        with self.lock:
            self.retired = True
            try: self.queue.put_nowait(None)
            except queue.Full: pass
        return self.snapshot()

    def _run(self):
        reader = None
        try:
            while True:
                job = self.queue.get()
                with self.lock:
                    if self.retired or job is None: break
                try:
                    if reader is None: reader = self.factory()
                    # Opening may have blocked after the waiter retired this client.
                    # Do not begin another I/O operation when that open returns.
                    with self.lock:
                        if self.retired: raise QueryUnavailable('target query retired during open')
                    job.value = reader.read(job.operation,job.xid)
                except BaseException as error:
                    job.error = error
                finally:
                    job.done.set()
                with self.lock:
                    if self.retired: break
        finally:
            if reader is not None:
                try: reader.close()
                except BaseException as error:
                    with self.lock: self.close_error = repr(error)

    def read(self, operation, xid, *, deadline_ns, cancelled):
        if type(deadline_ns) is not int:
            raise QueryUnavailable('original target-query deadline required')
        if cancelled() or time.monotonic_ns() >= deadline_ns:
            self.close()
            raise QueryUnavailable('target query cancelled or original deadline expired')
        with self.lock:
            if self.retired or self.current is not None:
                raise QueryUnavailable('target query worker retired or occupied')
            job = SimpleNamespace(operation=operation,xid=xid,done=threading.Event(),value=None,error=None)
            self.current = job
            self.queue.put_nowait(job)
            if self.thread is None:
                self.thread = threading.Thread(target=self._run,name='guarded-read-only-query',daemon=True)
                try: self.thread.start()
                except BaseException as error:
                    self.retired = True
                    job.done.set()
                    raise QueryUnavailable('target query worker did not start') from error
        try:
            while True:
                with self.lock:
                    if self.retired: raise QueryUnavailable('target query retired')
                if cancelled() or time.monotonic_ns() >= deadline_ns:
                    raise QueryUnavailable('target query cancelled or original deadline expired')
                if job.done.wait(.005):
                    if cancelled() or time.monotonic_ns() >= deadline_ns:
                        raise QueryUnavailable('late target query discarded')
                    if job.error is not None:
                        raise QueryUnavailable('target query failed') from job.error
                    with self.lock:
                        if self.retired: raise QueryUnavailable('target query retired')
                        self.current = None
                    return job.value
        except BaseException:
            self.close()
            raise
