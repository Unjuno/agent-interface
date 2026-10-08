"""Construction-only one-time FD ownership transfer; no production integration."""
import threading


class OnceOwner:
    def __init__(self, fd):
        self._fd = fd
        self._lock = threading.Lock()

    def take_for_close(self):
        with self._lock:
            fd = self._fd
            self._fd = None
            return fd
