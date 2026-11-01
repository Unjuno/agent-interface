"""Explicitly owned, disposable Linux/X11 target-process lifecycle.

This module is a primitive for callers that launch a disposable target
themselves. It never adopts a PID supplied after launch and refuses to retire
an X11 target unless XRes identity matches the retained child incarnation.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import select
import signal
import subprocess
import sys
import threading
import time
import uuid
from functools import wraps
from pathlib import Path
from typing import Mapping, Sequence

from .process_identity import read_linux_x11_process_identity
from .xres_client_fence import supervise_xres_worker


_MAX_RETIRE_WAIT_S = 10.0
_LAUNCH_RECEIPT = object()


def _with_handle_lock(method):
    @wraps(method)
    def locked(self, *args, **kwargs):
        with self._handle_lock:
            return method(self, *args, **kwargs)
    return locked


def _target_identity_worker(send_connection, display_name, xid):
    connection = None
    try:
        from Xlib.display import Display
        connection = Display(display_name)
        digest = read_linux_x11_process_identity(connection, xid)
        send_connection.send({'status':'observed', 'identity_digest':digest})
    except Exception as error:
        try:
            send_connection.send({'status':'unknown', 'reason':'identity_query_failed',
                                  'error_type':type(error).__name__})
        except (OSError, EOFError):
            pass
    finally:
        if connection is not None:
            connection.close()
        send_connection.close()


def _prestarted_target_identity_worker(request):
    from Xlib.display import Display
    connection = Display(request['display_name'])
    try:
        digest = read_linux_x11_process_identity(connection, request['xid'])
        return {'status':'observed', 'identity_digest':digest,
                'operation_id':request['operation_id'], 'session_id':request['session_id']}
    finally:
        connection.close()


def _linux_process_start_ticks(pid: int) -> int:
    stat = Path('/proc', str(pid), 'stat').read_text(encoding='ascii')
    opening, closing = stat.find('('), stat.rfind(')')
    if opening < 1 or closing <= opening or stat[:opening].strip() != str(pid):
        raise RuntimeError('launched process identity mismatch')
    fields = stat[closing + 1:].split()
    if (len(fields) <= 19 or fields[0] in ('Z', 'X', 'x')
            or not fields[19].isascii() or not fields[19].isdigit()):
        raise RuntimeError('launched process start identity unavailable')
    return int(fields[19])


def _identity_digest(xid: int, pid: int, start_ticks: int) -> str:
    payload = {'scheme':'xres-linux-process-v1', 'xid':xid,
               'pid':pid, 'start_ticks':start_ticks}
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('ascii')
    return hashlib.sha256(encoded).hexdigest()


def _bounded_timeout(value: float, name: str) -> float:
    if (type(value) not in (int, float) or isinstance(value, bool)
            or not math.isfinite(value) or not 0 <= value <= _MAX_RETIRE_WAIT_S):
        raise ValueError(f'{name} must be finite and in [0, {_MAX_RETIRE_WAIT_S}]')
    return float(value)


class OwnedTargetProcess:
    """A target launched and retained by this caller, never an adopted PID.

    Construction requires explicit disposable-target intent. Linux pidfd is
    mandatory for identity-safe termination: there is no PID-only signal
    fallback. A process must also own the selected X resource as reported by
    the trusted local X server before ``retire_x11_target`` can signal it.
    """

    def __init__(self, process: subprocess.Popen, pidfd: int, start_ticks: int,
                 *, _launch_receipt=None):
        if _launch_receipt is not _LAUNCH_RECEIPT:
            raise PermissionError('target ownership handles must come from launch()')
        self._process = process
        self._pidfd = pidfd
        self.pid = process.pid
        self.start_ticks = start_ticks
        self._closed = False
        self._bound_xid = None
        self._bound_identity_digest = None
        self._handle_lock = threading.RLock()
        self._session_custody = None
        self._custody_epoch = 0

    def _require_custody(self, token):
        if token is not self._session_custody:
            raise PermissionError('target custody token is not current')

    @_with_handle_lock
    def claim_session(self):
        if self._closed or self._process.poll() is not None:
            raise RuntimeError('target unavailable for custody')
        if self._session_custody is not None:
            raise RuntimeError('target already claimed by a session')
        token = object()
        self._session_custody = token
        self._custody_epoch += 1
        self._bound_xid = None
        self._bound_identity_digest = None
        return token

    @_with_handle_lock
    def release_session(self, token):
        self._require_custody(token)
        if token is None:
            raise PermissionError('a session custody token is required')
        self._session_custody = None
        self._custody_epoch += 1
        self._bound_xid = None
        self._bound_identity_digest = None

    @classmethod
    def launch(cls, argv: Sequence[str], *, disposable: bool,
               cwd: str | os.PathLike | None = None,
               env: Mapping[str, str] | None = None) -> 'OwnedTargetProcess':
        if disposable is not True:
            raise PermissionError('target must be explicitly declared disposable')
        if not sys.platform.startswith('linux'):
            raise RuntimeError('owned X11 target retirement currently requires Linux')
        if not callable(getattr(os, 'pidfd_open', None)) or not callable(
                getattr(signal, 'pidfd_send_signal', None)):
            raise RuntimeError('pidfd support is required; PID-only fallback is disabled')
        if (isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence)
                or not argv or any(type(part) is not str or not part or '\0' in part
                                   for part in argv)):
            raise ValueError('argv must be a non-empty sequence of strings')
        if env is not None and (not isinstance(env, Mapping)
                or any(type(key) is not str or type(value) is not str
                       or '\0' in key or '\0' in value
                       for key, value in env.items())):
            raise ValueError('env must map strings to strings')

        process = subprocess.Popen(
            list(argv), cwd=cwd, env=None if env is None else dict(env),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True, shell=False)
        try:
            pidfd = os.pidfd_open(process.pid, 0)
        except BaseException as error:
            # This is the exact Popen child created above. Clean up only this
            # just-launched child; never fall back to signaling an adopted PID.
            if process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired as wait_error:
                raise RuntimeError(
                    'pidfd unavailable and launched child did not exit within 1 s') from wait_error
            raise error
        try:
            start_ticks = _linux_process_start_ticks(process.pid)
        except BaseException as error:
            try:
                if process.poll() is None:
                    try:
                        signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                    except OSError:
                        # Popen still refers to the exact child created above.
                        process.kill()
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired as wait_error:
                raise RuntimeError(
                    'could not confirm exit of launched child after identity failure') from wait_error
            finally:
                os.close(pidfd)
            raise error
        return cls(process, pidfd, start_ticks,
                   _launch_receipt=_LAUNCH_RECEIPT)

    @property
    @_with_handle_lock
    def running(self) -> bool:
        return not self._closed and self._process.poll() is None

    def _wait_for_exit(self, timeout_s: float) -> bool:
        timeout_s = _bounded_timeout(timeout_s, 'timeout_s')
        if self._process.poll() is not None:
            return True
        poller = select.poll()
        poller.register(self._pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
        events = poller.poll(math.ceil(timeout_s * 1000))
        return bool(events) and self._process.poll() is not None

    def matches_x11_target(self, connection, xid: int) -> bool:
        if (self._closed or type(xid) is not int or not 1 < xid < 2**32
                or self._process.poll() is not None):
            return False
        try:
            observed = read_linux_x11_process_identity(connection, xid)
        except Exception:
            return False
        expected = _identity_digest(xid, self.pid, self.start_ticks)
        return observed == expected

    def bind_x11_target(self, connection, xid: int, *, _custody=None) -> dict:
        """Retain a pre-outage proof that this X resource belongs to this child."""
        with self._handle_lock:
            self._require_custody(_custody)
            custody_epoch = self._custody_epoch
            if self._closed:
                return {'status':'refused', 'reason':'ownership_handle_closed'}
        if not self.matches_x11_target(connection, xid):
            return {'status':'refused', 'reason':'target_process_identity_mismatch',
                    'pid':self.pid, 'start_ticks':self.start_ticks}
        with self._handle_lock:
            self._require_custody(_custody)
            if custody_epoch != self._custody_epoch:
                return {'status':'refused', 'reason':'custody_generation_changed'}
            if self._closed or self._process.poll() is not None:
                return {'status':'refused', 'reason':'target_unavailable'}
            digest = _identity_digest(xid, self.pid, self.start_ticks)
            if self._bound_xid is not None and (
                    self._bound_xid != xid or self._bound_identity_digest != digest):
                return {'status':'refused', 'reason':'target_binding_already_frozen',
                        'bound_xid':self._bound_xid, 'requested_xid':xid}
            self._bound_xid = xid
            self._bound_identity_digest = digest
            return {'status':'bound', 'xid':xid, 'pid':self.pid,
                    'start_ticks':self.start_ticks,
                    'identity_digest':digest}

    def bind_x11_target_supervised(self, display_name, xid: int, *, timeout_s=1.0,
                                   _custody=None) -> dict:
        """Bind with a killable XRes worker; process startup is outside its deadline."""
        timeout_s = _bounded_timeout(timeout_s, 'timeout_s')
        if timeout_s == 0:
            raise ValueError('timeout_s must be positive')
        with self._handle_lock:
            self._require_custody(_custody)
            custody_epoch = self._custody_epoch
        if (self._closed or type(xid) is not int or not 1 < xid < 2**32
                or self._process.poll() is not None):
            return {'status':'refused', 'reason':'target_unavailable'}
        observed = supervise_xres_worker(
            _target_identity_worker, (display_name, xid), timeout_s=timeout_s,
            accepted_statuses=('observed', 'unknown'))
        return self._bind_supervised_observation(xid, observed, _custody=_custody,
                                                 _expected_epoch=custody_epoch)

    def bind_x11_target_prestarted(self, supervisor, session_id, display_name, xid: int,
                                   *, timeout_s=1.0, _custody=None) -> dict:
        timeout_s = _bounded_timeout(timeout_s, 'timeout_s')
        if timeout_s == 0:
            raise ValueError('timeout_s must be positive')
        with self._handle_lock:
            self._require_custody(_custody)
            custody_epoch = self._custody_epoch
        if (self._closed or type(xid) is not int or not 1 < xid < 2**32
                or self._process.poll() is not None):
            return {'status':'refused', 'reason':'target_unavailable'}
        request = {'operation_id':uuid.uuid4().hex, 'session_id':session_id,
                   'display_name':display_name, 'xid':xid}
        observed = supervisor.run(
            request, deadline_monotonic_ns=time.monotonic_ns() + int(timeout_s * 1e9))
        return self._bind_supervised_observation(xid, observed, _custody=_custody,
                                                 _expected_epoch=custody_epoch)

    @_with_handle_lock
    def _bind_supervised_observation(self, xid, observed, *, _custody=None,
                                     _expected_epoch=None):
        self._require_custody(_custody)
        if _expected_epoch is not None and _expected_epoch != self._custody_epoch:
            return {'status':'refused', 'reason':'custody_generation_changed'}
        if (observed.get('status') != 'observed'
                or observed.get('worker_retired') is not True
                or observed.get('worker_exitcode') != 0):
            return {'status':'refused', 'reason':'target_identity_unavailable',
                    'identity_query':observed}
        digest = _identity_digest(xid, self.pid, self.start_ticks)
        if self._closed or self._process.poll() is not None or observed.get('identity_digest') != digest:
            return {'status':'refused', 'reason':'target_process_identity_mismatch'}
        if self._bound_xid is not None and (
                self._bound_xid != xid or self._bound_identity_digest != digest):
            return {'status':'refused', 'reason':'target_binding_already_frozen'}
        self._bound_xid, self._bound_identity_digest = xid, digest
        return {'status':'bound', 'xid':xid, 'pid':self.pid,
                'start_ticks':self.start_ticks, 'identity_digest':digest,
                'identity_query':observed}

    def retire_bound_target(self, *, term_timeout_s: float = 0.25,
                            kill_timeout_s: float = 0.25,
                            deadline_monotonic_ns=None, _custody=None) -> dict:
        """Retire only the child bound while X11 identity queries were healthy."""
        if (deadline_monotonic_ns is not None and
                (type(deadline_monotonic_ns) is not int or deadline_monotonic_ns <= 0)):
            raise ValueError('deadline_monotonic_ns must be a positive integer')
        if deadline_monotonic_ns is None:
            acquired = self._handle_lock.acquire()
        else:
            acquired = self._handle_lock.acquire(timeout=max(
                0, (deadline_monotonic_ns - time.monotonic_ns()) / 1e9))
        if not acquired:
            return {'status':'unknown', 'reason':'target_retirement_lock_unavailable',
                    'signal_attempts':[], 'target_identity_verified':False,
                    'process_exit_verified':False}
        try:
            self._require_custody(_custody)
            if self._closed:
                return {'status':'refused', 'reason':'ownership_handle_closed',
                        'signal_attempts':[], 'target_identity_verified':False}
            if self._bound_xid is None or self._bound_identity_digest is None:
                return {'status':'refused', 'reason':'target_binding_unavailable',
                        'signal_attempts':[], 'target_identity_verified':False}
            return self._retire_bound_target(
                xid=self._bound_xid, identity_digest=self._bound_identity_digest,
                term_timeout_s=term_timeout_s, kill_timeout_s=kill_timeout_s,
                deadline_monotonic_ns=deadline_monotonic_ns)
        finally:
            self._handle_lock.release()

    def retire_x11_target(self, connection, xid: int, *,
                          term_timeout_s: float = 0.25,
                          kill_timeout_s: float = 0.25, _custody=None) -> dict:
        term_timeout_s = _bounded_timeout(term_timeout_s, 'term_timeout_s')
        kill_timeout_s = _bounded_timeout(kill_timeout_s, 'kill_timeout_s')
        with self._handle_lock:
            self._require_custody(_custody)
            custody_epoch = self._custody_epoch
        if self._closed:
            return {'status':'refused', 'reason':'ownership_handle_closed',
                    'signal_attempts':[], 'target_identity_verified':False}
        if self._process.poll() is not None:
            return {'status':'already_exited', 'exitcode':self._process.returncode,
                    'signal_attempts':[], 'target_identity_verified':False,
                    'process_exit_verified':True}
        binding = self.bind_x11_target(connection, xid, _custody=_custody)
        if binding.get('status') != 'bound':
            return {'status':'refused', 'reason':binding.get('reason', 'target_unavailable'),
                    'signal_attempts':[], 'target_identity_verified':False}
        with self._handle_lock:
            self._require_custody(_custody)
            if custody_epoch != self._custody_epoch:
                return {'status':'refused', 'reason':'custody_generation_changed',
                        'signal_attempts':[], 'target_identity_verified':False}
            return self.retire_bound_target(term_timeout_s=term_timeout_s,
                                            kill_timeout_s=kill_timeout_s, _custody=_custody)

    def _retire_bound_target(self, *, xid: int, identity_digest: str,
                             term_timeout_s: float,
                             kill_timeout_s: float, deadline_monotonic_ns=None) -> dict:
        term_timeout_s = _bounded_timeout(term_timeout_s, 'term_timeout_s')
        kill_timeout_s = _bounded_timeout(kill_timeout_s, 'kill_timeout_s')
        if (deadline_monotonic_ns is not None and
                (type(deadline_monotonic_ns) is not int or deadline_monotonic_ns <= 0)):
            raise ValueError('deadline_monotonic_ns must be a positive integer')
        if self._process.poll() is not None:
            return {'status':'already_exited', 'exitcode':self._process.returncode,
                    'signal_attempts':[], 'target_identity_verified':True,
                    'target_xid':xid, 'identity_digest':identity_digest,
                    'process_exit_verified':True}

        attempts = []
        for signum, grace in ((signal.SIGTERM, term_timeout_s),
                              (signal.SIGKILL, kill_timeout_s)):
            if self._process.poll() is not None:
                return {'status':'retired', 'exitcode':self._process.returncode,
                        'signal_attempts':attempts,
                        'target_identity_verified':True,
                        'target_xid':xid, 'identity_digest':identity_digest,
                        'process_exit_verified':True}
            if (deadline_monotonic_ns is not None
                    and time.monotonic_ns() >= deadline_monotonic_ns):
                return {'status':'unknown', 'reason':'target_retirement_deadline',
                        'signal_attempts':attempts, 'target_identity_verified':True,
                        'target_xid':xid, 'identity_digest':identity_digest,
                        'process_exit_verified':False}
            try:
                signal.pidfd_send_signal(self._pidfd, signum)
                attempts.append({'signal':signum, 'status':'sent'})
            except ProcessLookupError:
                attempts.append({'signal':signum, 'status':'already_exited'})
            except OSError as error:
                attempts.append({'signal':signum, 'status':'error',
                                 'error_type':type(error).__name__})
                return {'status':'unknown', 'reason':'pidfd_signal_failed',
                        'signal_attempts':attempts,
                        'target_identity_verified':True,
                        'target_xid':xid, 'identity_digest':identity_digest,
                        'process_exit_verified':False}
            if deadline_monotonic_ns is not None:
                remaining = max(0, deadline_monotonic_ns - time.monotonic_ns()) / 1e9
                # Leave part of a short budget for the identity-bound KILL.
                grace = min(grace, remaining / 2 if signum == signal.SIGTERM else remaining)
            if self._wait_for_exit(grace):
                return {'status':'retired', 'exitcode':self._process.wait(timeout=0),
                        'signal_attempts':attempts,
                        'target_identity_verified':True,
                        'target_xid':xid, 'identity_digest':identity_digest,
                        'process_exit_verified':True}
        return {'status':'unknown', 'reason':'target_exit_deadline_exceeded',
                'signal_attempts':attempts, 'target_identity_verified':True,
                'target_xid':xid, 'identity_digest':identity_digest,
                'process_exit_verified':False}

    @_with_handle_lock
    def close(self, *, _custody=None) -> None:
        if self._closed:
            return
        self._require_custody(_custody)
        if self._process.poll() is None:
            raise RuntimeError('cannot close ownership handle while target is running')
        try:
            os.close(self._pidfd)
        finally:
            # A failed close may already have released the fd. Never retry the
            # numeric descriptor, which could have been reused for another fd.
            self._closed = True

    def __enter__(self) -> 'OwnedTargetProcess':
        if self._closed:
            raise RuntimeError('ownership handle is closed')
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
