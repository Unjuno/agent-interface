"""Prestarted, one-transaction process custody for bounded cancellation work.

The supervisor is deliberately one-shot. Its process is started and reports
readiness before the caller grants input authority. A transaction carries an
absolute monotonic deadline and exact session/operation identity. An expired,
stale, malformed, blocked, or unretired worker result is UNKNOWN; this module
never turns process liveness or a timeout into a release claim.
"""

from __future__ import annotations

import multiprocessing
import threading
import time


def _serve_one(command_receive, result_send, ready_send, worker_target):
    try:
        ready_send.send({'status': 'ready', 'pid': multiprocessing.current_process().pid})
    finally:
        ready_send.close()
    try:
        command = command_receive.recv()
        if command.get('op') == 'stop':
            return
        request = command.get('request')
        if not isinstance(request, dict):
            result = {'status': 'unknown', 'reason': 'malformed_request'}
        elif time.monotonic_ns() >= request.get('deadline_monotonic_ns', 0):
            result = {'status': 'unknown', 'reason': 'deadline_expired_before_start'}
        else:
            try:
                result = worker_target(request)
                if not isinstance(result, dict):
                    result = {'status': 'unknown', 'reason': 'malformed_worker_result'}
            except BaseException as error:
                result = {'status': 'unknown', 'reason': 'worker_exception',
                          'error_type': type(error).__name__, 'error': str(error)[:500]}
        result_send.send({'result': result,
                          'completed_monotonic_ns': time.monotonic_ns()})
    except (EOFError, OSError):
        pass
    finally:
        for connection in (command_receive, result_send):
            try:
                connection.close()
            except OSError:
                pass


class PrestartedCancellationSupervisor:
    """A ready process that can accept at most one deadline-bound request."""

    def __init__(self, worker_target, *, expected_session_id=None,
                 startup_timeout_s=5.0,
                 terminate_grace_s=0.1):
        if not callable(worker_target):
            raise TypeError('worker_target must be callable')
        if (type(startup_timeout_s) not in (int, float)
                or startup_timeout_s <= 0):
            raise ValueError('startup_timeout_s must be positive')
        if (type(terminate_grace_s) not in (int, float)
                or terminate_grace_s < 0):
            raise ValueError('terminate_grace_s must be nonnegative')
        self._context = multiprocessing.get_context('spawn')
        if (expected_session_id is not None
                and (type(expected_session_id) is not str or not expected_session_id)):
            raise ValueError('expected_session_id must be a non-empty string')
        self._expected_session_id = expected_session_id
        self._lock = threading.Lock()
        self._terminate_grace_s = float(terminate_grace_s)
        self._consumed = False
        self._closed = False
        self._receive = None
        self._send = None
        self._process = None
        command_receive, command_send = self._context.Pipe(duplex=False)
        result_receive, result_send = self._context.Pipe(duplex=False)
        ready_receive, ready_send = self._context.Pipe(duplex=False)
        process = self._context.Process(
            target=_serve_one,
            args=(command_receive, result_send, ready_send, worker_target),
            name='guarded-cancel-supervisor')
        try:
            process.start()
            command_receive.close()
            result_send.close()
            ready_send.close()
            if not ready_receive.poll(float(startup_timeout_s)):
                self._process = process
                self._terminate_locked()
                raise RuntimeError('cancellation supervisor readiness timed out')
            ready = ready_receive.recv()
            if (not isinstance(ready, dict) or ready.get('status') != 'ready'
                    or type(ready.get('pid')) is not int):
                self._process = process
                self._terminate_locked()
                raise RuntimeError('cancellation supervisor readiness malformed')
            self.pid = ready['pid']
            self._receive = result_receive
            self._send = command_send
            self._process = process
        except BaseException:
            for connection in (command_receive, command_send, result_receive,
                               result_send, ready_receive, ready_send):
                try:
                    connection.close()
                except OSError:
                    pass
            try:
                alive = process.pid is not None and process.is_alive()
            except (AssertionError, ValueError):
                alive = False
            if alive:
                process.terminate()
                process.join(self._terminate_grace_s)
                if process.is_alive() and callable(getattr(process, 'kill', None)):
                    process.kill()
                    process.join(self._terminate_grace_s)
            raise
        finally:
            try:
                ready_receive.close()
            except OSError:
                pass

    def _terminate_locked(self):
        process = self._process
        if process is None:
            return {'retired': True, 'exitcode': None}
        if process.is_alive():
            process.terminate()
            process.join(self._terminate_grace_s)
            if process.is_alive() and callable(getattr(process, 'kill', None)):
                process.kill()
                process.join(self._terminate_grace_s)
        try:
            retired = not process.is_alive()
            exitcode = process.exitcode
        except (AssertionError, ValueError):
            retired, exitcode = False, None
        return {'retired': retired or exitcode is not None,
                'exitcode': exitcode}

    def run(self, request, *, deadline_monotonic_ns):
        if (not isinstance(request, dict)
                or type(request.get('operation_id')) is not str
                or not request['operation_id']
                or type(request.get('session_id')) is not str
                or not request['session_id']
                or type(deadline_monotonic_ns) is not int
                or deadline_monotonic_ns <= 0):
            raise ValueError('request requires operation_id, session_id and an absolute deadline')
        request = dict(request, deadline_monotonic_ns=deadline_monotonic_ns)
        with self._lock:
            if self._closed or self._consumed:
                return {'status': 'unknown', 'reason': 'supervisor_unavailable',
                        'operation_id': request['operation_id'],
                        'session_id': request['session_id'],
                        'worker_retired': (not self._process.is_alive()
                                           if self._process is not None else True)}
            self._consumed = True
            if (self._expected_session_id is not None
                    and request['session_id'] != self._expected_session_id):
                retirement = self._terminate_locked()
                return {'status': 'unknown', 'reason': 'stale_session',
                        'operation_id': request['operation_id'],
                        'session_id': request['session_id'],
                        'worker_retired': retirement['retired'],
                        'worker_exitcode': retirement['exitcode']}
            if time.monotonic_ns() >= deadline_monotonic_ns:
                retirement = self._terminate_locked()
                return {'status': 'unknown', 'reason': 'deadline_expired_before_admission',
                        'operation_id': request['operation_id'],
                        'session_id': request['session_id'], **retirement}
            try:
                self._send.send({'op': 'run', 'request': request})
            except (EOFError, OSError) as error:
                retirement = self._terminate_locked()
                return {'status': 'unknown', 'reason': 'supervisor_send_failed',
                        'error': repr(error), 'operation_id': request['operation_id'],
                        'session_id': request['session_id'], **retirement}
            remaining_s = max(0, deadline_monotonic_ns - time.monotonic_ns()) / 1e9
            if not self._receive.poll(remaining_s):
                retirement = self._terminate_locked()
                return {'status': 'unknown', 'reason': 'transaction_deadline',
                        'operation_id': request['operation_id'],
                        'session_id': request['session_id'],
                        'worker_retired': retirement['retired'],
                        'worker_exitcode': retirement['exitcode']}
            try:
                envelope = self._receive.recv()
            except (EOFError, OSError) as error:
                envelope = {'result': {'status': 'unknown',
                                       'reason': 'supervisor_result_unavailable',
                                       'error': repr(error)}}
            process = self._process
            remaining_s = max(0, deadline_monotonic_ns - time.monotonic_ns()) / 1e9
            process.join(min(self._terminate_grace_s, remaining_s))
            retired = not process.is_alive()
            result = envelope.get('result') if isinstance(envelope, dict) else None
            if (not retired or process.exitcode != 0 or not isinstance(result, dict)
                    or time.monotonic_ns() > deadline_monotonic_ns):
                return {'status': 'unknown', 'reason': 'unretired_or_late_supervisor',
                        'operation_id': request['operation_id'],
                        'session_id': request['session_id'],
                        'worker_retired': retired, 'worker_exitcode': process.exitcode,
                        'completed_monotonic_ns': envelope.get('completed_monotonic_ns')
                            if isinstance(envelope, dict) else None}
            if (result.get('operation_id') != request['operation_id']
                    or result.get('session_id') != request['session_id']):
                return {'status': 'unknown', 'reason': 'stale_or_mismatched_receipt',
                        'operation_id': request['operation_id'],
                        'session_id': request['session_id'],
                        'worker_retired': retired, 'worker_exitcode': process.exitcode}
            return dict(result, worker_retired=True,
                        worker_exitcode=process.exitcode,
                        completed_monotonic_ns=envelope.get('completed_monotonic_ns'))

    def close(self):
        with self._lock:
            if self._closed:
                return {'retired': True, 'exitcode': None}
            self._closed = True
            process = self._process
            if process is not None and process.is_alive() and not self._consumed:
                try:
                    self._send.send({'op': 'stop'})
                except (EOFError, OSError):
                    pass
                process.join(self._terminate_grace_s)
            return self._terminate_locked()


def x11_cancel_worker(request):
    """Observe exact owner disconnection, then release only recorded inputs.

    This function runs in the prestarted process. Every synchronous X request
    remains killable by the parent at the operation deadline. A readback is
    retained as a stage receipt only; it does not establish queue drainage or
    owner-exclusive physical state, so this worker never reports product-level
    release confirmation or task success.
    """
    operation_id = request.get('operation_id')
    session_id = request.get('session_id')
    deadline_ns = request.get('deadline_monotonic_ns')
    resource_base = request.get('x_resource_base')
    expected_pid = request.get('owner_pid')
    display_name = request.get('display_name')
    keys = request.get('keys')
    buttons = request.get('buttons')
    binding_revision = request.get('binding_revision')
    owner_generation = request.get('owner_generation')
    result = {'operation_id': operation_id, 'session_id': session_id,
              'binding_revision': binding_revision,
              'worker_started_monotonic_ns':time.monotonic_ns(),
              'release_confirmed': False, 'task_success': None,
              'replay_allowed': False}
    invalid_fields = []
    if type(deadline_ns) is not int or deadline_ns <= 0:
        invalid_fields.append('deadline_monotonic_ns')
    if (type(resource_base) is not int
            or not 0 < resource_base < 2**32):
        invalid_fields.append('x_resource_base')
    if type(expected_pid) is not int or expected_pid <= 0:
        invalid_fields.append('owner_pid')
    if not isinstance(keys, dict):
        invalid_fields.append('keys')
    elif any(type(name) is not str or type(code) is not int
             or not 0 <= code < 256 for name, code in keys.items()):
        invalid_fields.append('keys.entries')
    if not isinstance(buttons, list):
        invalid_fields.append('buttons')
    elif any(type(button) is not str or button not in
             ('left', 'middle', 'right', 'x1', 'x2') for button in buttons):
        invalid_fields.append('buttons.entries')
    if not isinstance(owner_generation, dict):
        invalid_fields.append('owner_generation')
    else:
        for name, expected in (
                ('session_id', session_id), ('child_pid', expected_pid),
                ('x_resource_base', resource_base),
                ('binding_revision', binding_revision)):
            if owner_generation.get(name) != expected:
                invalid_fields.append('owner_generation.' + name)
    if invalid_fields:
        return dict(result, status='unknown', reason='invalid_cleanup_request',
                    cleanup_status='UNKNOWN', invalid_fields=invalid_fields)
    if time.monotonic_ns() >= deadline_ns:
        return dict(result, status='unknown', reason='transaction_deadline_before_xres',
                    cleanup_status='UNKNOWN')
    try:
        if __import__('sys').platform != 'linux':
            return dict(result, status='unknown', reason='unsupported_platform',
                        cleanup_status='UNKNOWN')
        from Xlib.display import Display
        from .xres_client_fence import client_pid_at_base
        display = Display(display_name)
        disconnect_started_ns = time.monotonic_ns()
        while True:
            if time.monotonic_ns() >= deadline_ns:
                return dict(result, status='unknown', reason='transaction_deadline_xres',
                            cleanup_status='UNKNOWN',
                            owner_client_disconnect={'status':'unknown',
                                'reason':'transaction_deadline',
                                'started_monotonic_ns':disconnect_started_ns})
            observed = client_pid_at_base(display, resource_base)
            if observed is False:
                break
            if observed != expected_pid:
                return dict(result, status='unknown', reason='stale_owner_identity',
                            cleanup_status='UNKNOWN', owner_client_disconnect={
                                'status':'unknown', 'reason':'resource_base_reused',
                                'observed_pid':observed,
                                'expected_pid':expected_pid})
            time.sleep(min(0.01, max(0, deadline_ns - time.monotonic_ns()) / 1e9))
        try:
            display.close()
        except Exception:
            pass
        result['owner_client_disconnect'] = {
            'status':'disconnected', 'expected_pid':expected_pid,
            'resource_base':resource_base,
            'started_monotonic_ns':disconnect_started_ns,
            'observed_monotonic_ns':time.monotonic_ns()}
    except BaseException as error:
        return dict(result, status='unknown', reason='xres_query_failed',
                    cleanup_status='UNKNOWN', error_type=type(error).__name__,
                    error=str(error)[:500])
    if time.monotonic_ns() >= deadline_ns:
        return dict(result, status='unknown', reason='transaction_deadline_before_release',
                    cleanup_status='UNKNOWN', owner_release_attempt={
                        'status':'not_attempted', 'reason':'transaction_deadline'})
    backend = None
    try:
        from runtime.backends.x11_v1.backend import X11Backend
        from Xlib import X
        from Xlib.ext import xtest
        from runtime.backends.x11_v1.backend import BUTTON_MAP
        backend = X11Backend(display_name, {})
        backend.held_keycodes = dict(keys)
        backend.held_buttons = set(buttons)
        release_started_ns = time.monotonic_ns()
        requested = []
        for code in keys.values():
            if time.monotonic_ns() >= deadline_ns:
                return dict(result, status='unknown', reason='transaction_deadline_during_release',
                            cleanup_status='UNKNOWN', owner_release_attempt={
                                'status':'unknown', 'reason':'deadline_before_next_release'})
            xtest.fake_input(backend.d, X.KeyRelease, code)
            requested.append({'kind':'KeyRelease', 'code':code,
                              'requested_monotonic_ns':time.monotonic_ns()})
        for button in buttons:
            if time.monotonic_ns() >= deadline_ns:
                return dict(result, status='unknown', reason='transaction_deadline_during_release',
                            cleanup_status='UNKNOWN', owner_release_attempt={
                                'status':'unknown', 'reason':'deadline_before_next_release'})
            xtest.fake_input(backend.d, X.ButtonRelease, BUTTON_MAP[button])
            requested.append({'kind':'ButtonRelease', 'button':button,
                              'requested_monotonic_ns':time.monotonic_ns()})
        if time.monotonic_ns() >= deadline_ns:
            return dict(result, status='unknown', reason='transaction_deadline_before_sync',
                        cleanup_status='UNKNOWN', owner_release_attempt={
                            'status':'unknown', 'reason':'deadline_before_sync'})
        sync_started_ns = time.monotonic_ns()
        backend.d.sync()
        sync_completed_ns = time.monotonic_ns()
        keys_down = backend._physical_keys_down(dict(keys))
        buttons_down = backend._physical_buttons_down()
        buttons_down = sorted(set(buttons_down) | (set(buttons) -
            {'left', 'middle', 'right'}))
        release = {'verified':not keys_down and not buttons_down,
                   'keys_down':keys_down, 'buttons_down':buttons_down,
                   'release_started_monotonic_ns':release_started_ns,
                   'release_requests':requested,
                   'sync_started_monotonic_ns':sync_started_ns,
                   'sync_completed_monotonic_ns':sync_completed_ns,
                   'readback_monotonic_ns':time.monotonic_ns()}
        release_attempt = {'status':'readback_verified' if release['verified'] else 'unknown',
                           'release':release,
                           'readback_source':'prestarted_supervisor_x11'}
        return dict(result, status='completed' if release['verified'] else 'unknown',
                    cleanup_status='UNKNOWN', owner_release_attempt=release_attempt)
    except BaseException as error:
        return dict(result, status='unknown', reason='release_failed',
                    cleanup_status='UNKNOWN', error_type=type(error).__name__,
                    error=str(error)[:500], owner_release_attempt={
                        'status':'unknown', 'reason':'release_failed'})
    finally:
        if backend is not None:
            try:
                backend.close()
            except BaseException:
                pass
