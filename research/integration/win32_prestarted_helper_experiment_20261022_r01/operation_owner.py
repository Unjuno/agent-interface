"""Inert process-ownership prototype; it never calls Win32 or emits input."""
from __future__ import annotations

from copy import deepcopy
import multiprocessing
import threading
import time


def _remaining_seconds(deadline_ns: int) -> float:
    return max(0, deadline_ns - time.monotonic_ns()) / 1_000_000_000


class InertOperationOwner:
    """Exercise producer-retirement ordering with injected inert processes.

    Targets have the shape ``target(send_connection, request, *target_args)``.
    They are expected to be top-level, spawn-picklable callables. This class is
    a research model, not a production runtime or a Win32 backend.
    """

    def __init__(self, worker_target, recovery_target, observer_target, *,
                 worker_args=(), recovery_args=(), observer_args=(),
                 context=None, process_factory=None):
        for name, target in (('worker_target', worker_target),
                             ('recovery_target', recovery_target),
                             ('observer_target', observer_target)):
            if not callable(target):
                raise TypeError(f'{name} must be callable')
        self._context = context or multiprocessing.get_context('spawn')
        self._process_factory = process_factory or self._context.Process
        self._targets = (worker_target, recovery_target, observer_target)
        self._args = (tuple(worker_args), tuple(recovery_args),
                      tuple(observer_args))
        self._lock = threading.Lock()
        self._state = 'idle'
        self._request = None
        self._process = None
        self._receive = None
        self._used_operation_ids = set()
        self._cached_cancel = None
        self._helpers = {}
        try:
            self._start_helper(1)
            self._start_helper(2)
        except BaseException:
            self.close()
            raise

    def _start_helper(self, index):
        target = self._targets[index]
        args = self._args[index]
        connection = self._context.Pipe(duplex=True)
        process = self._process_factory(
            target=_helper_server,
            args=(target, args, connection[1]), daemon=True)
        try:
            process.start()
        except BaseException:
            connection[0].close()
            connection[1].close()
            raise
        connection[1].close()
        receive = connection[0]
        if not receive.poll(2.0):
            self._retire(process, time.monotonic_ns() + 1_000_000_000)
            receive.close()
            raise RuntimeError('prestarted helper readiness timeout')
        try:
            ready = receive.recv()
        except (EOFError, OSError) as error:
            self._retire(process, time.monotonic_ns() + 1_000_000_000)
            receive.close()
            raise RuntimeError('prestarted helper readiness unavailable') from error
        if ready != {'status': 'ready'} or not process.is_alive():
            self._retire(process, time.monotonic_ns() + 1_000_000_000)
            receive.close()
            raise RuntimeError('prestarted helper readiness invalid')
        self._helpers[index] = {
            'process': process, 'connection': receive, 'available': True}

    @staticmethod
    def _validate_request(request, current_session_id,
                          current_target_generation):
        if not isinstance(request, dict):
            raise ValueError('request must be an object')
        operation_id = request.get('operation_id')
        session_id = request.get('session_id')
        generation = request.get('target_generation')
        keys = request.get('keys')
        buttons = request.get('buttons')
        if (type(operation_id) is not str or not operation_id
                or type(session_id) is not str or not session_id
                or type(generation) is not int or generation < 0
                or type(keys) is not list
                or any(type(key) is not str or not key for key in keys)
                or type(buttons) is not list
                or any(type(button) is not str or not button for button in buttons)
                or len(set(keys)) != len(keys)
                or len(set(buttons)) != len(buttons)):
            raise ValueError('invalid operation identity or frozen obligations')
        if session_id != current_session_id:
            return 'stale_session'
        if generation != current_target_generation:
            return 'stale_target_generation'
        return None

    def begin(self, request, *, current_session_id, current_target_generation):
        refusal = self._validate_request(request, current_session_id,
                                         current_target_generation)
        if refusal:
            return {'status': 'refused', 'reason': refusal,
                    'input_dispatched': False}
        frozen = deepcopy(request)
        with self._lock:
            if self._state in ('active', 'cancelling', 'unknown'):
                return {'status': 'refused', 'reason': 'producer_not_retired',
                        'input_dispatched': False}
            try:
                helpers_ready = all(
                    self._helpers.get(index, {}).get('available') is True
                    and self._helpers[index]['process'].is_alive()
                    for index in (1, 2))
            except (AssertionError, OSError, ValueError):
                helpers_ready = False
            if not helpers_ready:
                self._state = 'unknown'
                return {'status': 'refused',
                        'reason': 'prestarted_helper_unavailable',
                        'input_dispatched': False, 'replay_allowed': False}
            if frozen['operation_id'] in self._used_operation_ids:
                return {'status': 'refused', 'reason': 'duplicate_operation_id',
                        'input_dispatched': False}
            if self._request is not None:
                previous = self._request
                fresh = (frozen['session_id'] != previous['session_id']
                         or frozen['target_generation']
                         > previous['target_generation'])
                if not fresh:
                    return {'status': 'refused', 'reason': 'fresh_target_required',
                            'input_dispatched': False}

            receive, send = self._context.Pipe(duplex=False)
            target = self._targets[0]
            args = (send, frozen, *self._args[0])
            process = self._process_factory(target=target, args=args,
                                            daemon=True)
            try:
                process.start()
            except BaseException:
                receive.close()
                send.close()
                raise
            send.close()
            self._request = frozen
            self._process = process
            self._receive = receive
            self._cached_cancel = None
            self._used_operation_ids.add(frozen['operation_id'])
            self._state = 'active'
            return {'status': 'admitted', 'operation_id': frozen['operation_id'],
                    'input_dispatched': True, 'synthetic': True}

    def _retire(self, process, deadline_ns):
        try:
            if process.is_alive():
                process.terminate()
            process.join(_remaining_seconds(deadline_ns))
            return not process.is_alive()
        except (AssertionError, OSError, ValueError):
            return False

    def _bounded_target(self, index, request, deadline_ns):
        if _remaining_seconds(deadline_ns) <= 0:
            return {'status': 'unknown', 'reason': 'deadline_before_helper',
                    'worker_retired': True}
        helper = self._helpers.get(index)
        if (helper is None or not helper['available']
                or not helper['process'].is_alive()):
            return {'status': 'unknown', 'reason': 'prestarted_helper_unavailable',
                    'worker_retired': True}
        process = helper['process']
        receive = helper['connection']
        try:
            receive.send(request)
            remaining = _remaining_seconds(deadline_ns)
            if remaining and receive.poll(remaining):
                result = receive.recv()
            else:
                result = None
            remaining = _remaining_seconds(deadline_ns)
            if (result is not None and remaining
                    and receive.poll(remaining)):
                completion = receive.recv()
            else:
                completion = None
        except (EOFError, OSError):
            result = None
            completion = None
        if completion != {'control': 'operation_complete'}:
            result = None
        if result is None:
            helper['available'] = False
            retired = self._retire(process, deadline_ns)
            return {'status': 'unknown',
                    'reason': 'helper_timeout' if retired else 'helper_not_retired',
                    'worker_retired': retired}
        if not process.is_alive():
            helper['available'] = False
            return {'status': 'unknown', 'reason': 'helper_exited_after_receipt',
                    'worker_retired': True}
        exitcode = getattr(process, 'exitcode', None)
        if exitcode not in (0, None):
            helper['available'] = False
            return {'status': 'unknown', 'reason': 'helper_failed',
                    'worker_retired': True, 'exitcode': exitcode}
        if not isinstance(result, dict):
            helper['available'] = False
            return {'status': 'unknown', 'reason': 'helper_receipt_missing',
                    'worker_retired': True}
        return {'status': 'completed', 'result': result,
                'worker_retired': True, 'helper_process_reused': True}

    def close(self):
        """Retire all owned children; tests and startup failure use this path."""
        if self._process is not None:
            process = self._process
            retired = self._retire(
                process, time.monotonic_ns() + 1_000_000_000)
            if self._receive is not None:
                try:
                    self._receive.close()
                except OSError:
                    pass
                self._receive = None
            if retired:
                close = getattr(process, 'close', None)
                if callable(close):
                    try:
                        close()
                    except (AssertionError, OSError, ValueError):
                        pass
                self._process = None
        for helper in self._helpers.values():
            helper['available'] = False
            try:
                helper['connection'].send(None)
            except (EOFError, OSError):
                pass
            process = helper['process']
            retired = (self._retire(
                process, time.monotonic_ns() + 1_000_000_000)
                if process.is_alive() else True)
            try:
                helper['connection'].close()
            except OSError:
                pass
            if retired:
                close = getattr(process, 'close', None)
                if callable(close):
                    try:
                        close()
                    except (AssertionError, OSError, ValueError):
                        pass
        self._helpers.clear()

    def cancel(self, operation_id, *, deadline_monotonic_ns):
        if type(operation_id) is not str or not operation_id:
            raise ValueError('operation_id must be a nonempty string')
        if type(deadline_monotonic_ns) is not int:
            raise ValueError('deadline_monotonic_ns must be an integer')
        with self._lock:
            if (self._cached_cancel is not None
                    and self._cached_cancel.get('operation_id') == operation_id):
                return {**deepcopy(self._cached_cancel), 'duplicate': True}
            if (self._request is None
                    or self._request['operation_id'] != operation_id
                    or self._state != 'active'):
                return {'status': 'refused', 'reason': 'stale_operation_id',
                        'operation_id': operation_id,
                        'input_dispatched': False, 'replay_allowed': False}
            self._state = 'cancelling'
            process = self._process
            receive = self._receive
            request = deepcopy(self._request)

        if receive is not None:
            try:
                receive.close()
            except OSError:
                pass
        producer_retired = self._retire(process, deadline_monotonic_ns)
        if producer_retired:
            close = getattr(process, 'close', None)
            if callable(close):
                try:
                    close()
                except (AssertionError, OSError, ValueError):
                    pass
        if not producer_retired:
            result = {'status': 'unknown', 'reason': 'producer_retirement_unknown',
                      'operation_id': operation_id, 'producer_retired': False,
                      'recovery_attempted': False, 'replay_allowed': False,
                      'operation_result': 'unknown', 'task_success': None,
                      'synthetic': True}
        elif _remaining_seconds(deadline_monotonic_ns) <= 0:
            result = {'status': 'unknown',
                      'reason': 'deadline_expired_before_recovery',
                      'operation_id': operation_id, 'producer_retired': True,
                      'recovery_attempted': False, 'replay_allowed': False,
                      'operation_result': 'unknown', 'task_success': None,
                      'synthetic': True}
        else:
            try:
                recovery = self._bounded_target(
                    1, request, deadline_monotonic_ns)
            except Exception as error:
                recovery = {'status': 'unknown',
                            'reason': 'helper_start_or_run_failed',
                            'error_type': type(error).__name__}
            if (recovery.get('status') != 'completed'
                    or recovery.get('result', {}).get('status') != 'released'):
                result = {'status': 'unknown', 'reason': 'recovery_unconfirmed',
                          'operation_id': operation_id, 'producer_retired': True,
                          'recovery_attempted': True, 'recovery': recovery,
                          'replay_allowed': False, 'operation_result': 'unknown',
                          'task_success': None,
                          'synthetic': True}
            else:
                try:
                    observation = self._bounded_target(
                        2, request, deadline_monotonic_ns)
                except Exception as error:
                    observation = {'status': 'unknown',
                                   'reason': 'helper_start_or_run_failed',
                                   'error_type': type(error).__name__}
                neutral = (observation.get('status') == 'completed'
                           and observation.get('result', {}).get('keys_down') == []
                           and observation.get('result', {}).get('buttons_down') == [])
                result = {
                    'status': 'input_recovered_fake' if neutral else 'unknown',
                    'reason': None if neutral else 'neutral_state_unconfirmed',
                    'operation_id': operation_id, 'producer_retired': True,
                    'recovery_attempted': True, 'recovery': recovery,
                    'observation': observation,
                    'synthetic_neutral_state': neutral,
                    'replay_allowed': False, 'operation_result': 'unknown',
                    'task_success': None,
                    'synthetic': True,
                }

        with self._lock:
            self._state = ('recovered'
                           if result['status'] == 'input_recovered_fake'
                           else 'unknown')
            self._cached_cancel = deepcopy(result)
        return result


def _target_adapter(target, send, args):
    try:
        target(send, *args)
    finally:
        try:
            send.close()
        except OSError:
            pass


def _helper_server(target, target_args, connection):
    """Serve bounded inert helper requests over a process started at owner init."""
    try:
        connection.send({'status': 'ready'})
        while True:
            try:
                request = connection.recv()
            except (EOFError, OSError):
                return
            if request is None:
                return
            try:
                target(connection, request, *target_args)
                connection.send({'control': 'operation_complete'})
            except BaseException as error:
                try:
                    connection.send({'status': 'helper_error',
                                     'error_type': type(error).__name__})
                    connection.send({'control': 'operation_complete'})
                except (EOFError, OSError):
                    return
    finally:
        try:
            connection.close()
        except OSError:
            pass
