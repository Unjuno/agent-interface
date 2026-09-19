"""Research input owner: one X11 connection, independent of capture and logging.

This is scheduler-dependent deadline enforcement, not hard real-time control.
No user callback, image work, file write or stdout write runs on this thread.
"""
import queue
import threading
import time
from Xlib import X, XK, display
from Xlib.ext import xtest
from executor_v3 import Cancelled


class InputOwner:
    def __init__(self, display_name):
        self.requests = queue.Queue()
        self.records = []
        self.ready = threading.Event()
        self.error = None
        self.closed = False
        self.display_name = display_name
        self.thread = threading.Thread(target=self._run, name='input-owner')
        self.thread.start()
        self.ready.wait()
        if self.error is not None:
            self.thread.join()
            raise self.error

    def call(self, operation, lease=None, key=None):
        if self.closed:
            raise RuntimeError('input owner closed')
        done = threading.Event()
        reply = []
        self.requests.put((operation, lease, key, done, reply))
        done.wait()
        ok, result = reply[0]
        if not ok:
            raise result
        return result

    def close(self):
        if not self.closed:
            try:
                self.call('close')
            finally:
                self.closed = True
                self.thread.join()

    def _run(self):
        try:
            d = display.Display(self.display_name)
        except Exception as exc:
            self.error = exc
            self.ready.set()
            return
        held = {}
        touched = set()
        active = None
        fault = None
        self.ready.set()

        def release(reason):
            nonlocal active
            for code in list(held):
                xtest.fake_input(d, X.KeyRelease, code)
            d.sync()
            bitmap = d.query_keymap()
            down = [code for code in touched if bitmap[code // 8] & (1 << (code % 8))]
            record = dict(event='owner_release', reason=reason, verified=not down,
                          keys_down=down, verified_ns=time.perf_counter_ns(),
                          valid_until_ns=active.deadline if active else None)
            self.records.append(record)
            if down:
                raise RuntimeError('owner release not verified: ' + repr(down))
            held.clear()
            touched.clear()
            active = None
            return record

        try:
            while True:
                # Check before dequeue so a busy request queue cannot starve expiry.
                if active is not None:
                    expired = time.perf_counter_ns() >= active.deadline
                    if expired or active.cancel.is_set():
                        try:
                            release('expired' if expired else 'cancelled')
                        except Exception as exc:
                            fault = exc
                            active = None
                timeout = .002
                if active is not None:
                    timeout = min(timeout, max(0, (active.deadline-time.perf_counter_ns())/1e9))
                try:
                    op, lease, key, done, reply = self.requests.get(timeout=timeout)
                except queue.Empty:
                    continue
                closing = op == 'close'
                try:
                    if op in ('release', 'close'):
                        if op == 'release' and active is not None and active is not lease:
                            raise ValueError('release belongs to another intent')
                        result = release(op)
                    elif op in ('down', 'up'):
                        code = d.keysym_to_keycode(XK.string_to_keysym(key))
                        if not code:
                            raise ValueError('key unavailable on input owner')
                        if op == 'down':
                            if fault is not None:
                                raise RuntimeError('input owner failed closed') from fault
                            if active is not None and active is not lease:
                                raise ValueError('another intent owns input')
                            lease.check()
                            if lease.cancel.is_set():
                                raise Cancelled()
                            admitted = time.perf_counter_ns()
                            active = lease
                            touched.add(code)
                            held[code] = lease
                            xtest.fake_input(d, X.KeyPress, code)
                            d.sync()
                            result = dict(event='input_admission', key=key, admitted_ns=admitted,
                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)
                        else:
                            # Cleanup from an old intent must never release a newer hold.
                            if code in held and held[code] is not lease:
                                raise ValueError('key belongs to another intent')
                            if code in held:
                                xtest.fake_input(d, X.KeyRelease, code)
                                d.sync()
                                del held[code]
                            result = None
                    else:
                        raise ValueError('unknown input operation')
                    reply.append((True, result))
                except Exception as exc:
                    reply.append((False, exc))
                finally:
                    done.set()
                if closing:
                    break
        finally:
            d.close()
