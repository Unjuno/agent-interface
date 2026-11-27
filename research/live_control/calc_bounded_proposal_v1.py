"""One bounded wait for a trusted, read-only proposal callback.

Timeout retires the wrapper and discards late results; Python threads cannot
interrupt a blocked callback. This is not a sandbox or a physical stop bound.
"""
import copy
import threading
import time


class BoundedProposal:
    def __init__(self, provider, *, timeout_ms, cancelled):
        if (not callable(provider) or not callable(cancelled) or
                type(timeout_ms) is not int or not 1 <= timeout_ms <= 5000):
            raise ValueError('provider, cancellation and finite timeout required')
        self.provider, self.timeout_ms, self.cancelled = provider, timeout_ms, cancelled
        self.lock = threading.Lock()
        self.used = False
        self.retired = False
        self.thread = None

    def snapshot(self):
        with self.lock:
            return {'used': self.used, 'retired': self.retired,
                    'thread_alive': self.thread is not None and self.thread.is_alive()}

    def __call__(self, native, image):
        with self.lock:
            if self.used:
                return None
            self.used = True
        deadline = time.monotonic_ns() + self.timeout_ms * 1_000_000
        done = threading.Event()
        result = {}
        try:
            if self.cancelled() is not False:
                return None
            native_copy, image_copy = copy.deepcopy(native), image.copy()
            # Snapshot copying can consume the whole lease or race cancellation.
            # Never start a proposal worker after either boundary has expired.
            if self.cancelled() is not False or time.monotonic_ns() >= deadline:
                return None
            def work():
                try:
                    result['value'] = self.provider(native_copy, image_copy)
                except BaseException:
                    result['failed'] = True
                finally:
                    done.set()
            self.thread = threading.Thread(target=work, name='calc-proposal-readonly', daemon=True)
            self.thread.start()
            while True:
                remaining = deadline - time.monotonic_ns()
                if remaining <= 0 or self.cancelled() is not False:
                    return None
                if done.wait(min(0.005, remaining / 1_000_000_000)):
                    if time.monotonic_ns() >= deadline or self.cancelled() is not False:
                        return None
                    value = result.get('value')
                    return copy.deepcopy(value) if type(value) is dict and not result.get('failed') else None
        except Exception:
            return None
        finally:
            with self.lock:
                self.retired = True