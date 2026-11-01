"""Experimental per-process Xlib socket guard for an owned private X server.

Install only in a fresh, disposable Linux worker before its first X connection.
This process-wide hook does not protect already-open connections, other workers,
or code that bypasses python-xlib's connection factory. The worker owner remains
responsible for bounding and retiring the process if a syscall blocks.
"""

import os
from pathlib import Path
import select
import socket
import struct
import sys
import threading


_INSTALL_LOCK = threading.Lock()


class OwnedXlibConnector:
    def __init__(self, pidfd, expected_pid, *, disposable):
        if disposable is not True or not sys.platform.startswith('linux'):
            raise ValueError('explicit disposable Linux worker required')
        if type(expected_pid) is not int or expected_pid <= 0:
            raise ValueError('invalid server PID')
        from Xlib.support import connect
        self._lock = threading.Lock()
        self._closed = False
        self._close_result = None
        self._pid = expected_pid
        self._pidfd = os.dup(pidfd)
        try:
            self._check_pidfd()
            with _INSTALL_LOCK:
                if isinstance(connect.get_socket, OwnedXlibConnector):
                    raise RuntimeError('connector already installed')
                self._original = connect.get_socket
                connect.get_socket = self
        except BaseException:
            os.close(self._pidfd)
            self._closed = True
            raise

    def _check_pidfd(self):
        poller = select.poll()
        poller.register(self._pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
        contents = Path('/proc/self/fdinfo', str(self._pidfd)).read_text()
        fields = dict(line.split(':', 1) for line in contents.splitlines() if ':' in line)
        if fields.get('Pid', '').strip() != str(self._pid) or poller.poll(0):
            raise RuntimeError('owned display unavailable')

    def __call__(self, *args):
        with self._lock:
            if self._closed:
                raise RuntimeError('owned connector closed')
            self._check_pidfd()
            sock = self._original(*args)
            try:
                if sock.family != socket.AF_UNIX:
                    raise RuntimeError('unsupported transport')
                peer = struct.unpack('3i', sock.getsockopt(
                    socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[0]
                self._check_pidfd()
                if peer != self._pid:
                    raise RuntimeError('display peer mismatch')
                return sock
            except BaseException:
                sock.close()
                raise

    def close(self):
        """Close the retained pidfd once; False means busy or outcome unknown."""
        if not self._lock.acquire(blocking=False):
            return False
        try:
            if not self._closed:
                self._closed = True
                try:
                    os.close(self._pidfd)
                except BaseException:
                    self._close_result = False
                    raise
                self._close_result = True
            return self._close_result
        finally:
            self._lock.release()
