"""Explicit process boundary for the standard guarded-X11 session.

The child owns the complete NativeHandleBridge session. Parent calls are
allowlisted RPCs; cancellation uses a separate pipe. Retiring the child bounds
its future user-space writes, but never proves that queued server requests or
physical input were released.
"""
from copy import deepcopy
import multiprocessing
from pathlib import Path
import threading
import time
from types import SimpleNamespace

from .mcp_guarded import GuardedSessionOwner


_STARTUP_TIMEOUT_S = 5.0
_CLOSE_TIMEOUT_S = 5.0
_CANCEL_RETIRE_GRACE_S = 1.0
_JOIN_TIMEOUT_S = 1.0


def _owner_snapshot(owner, pid):
    row = owner.snapshot()
    session = getattr(owner, 'session', None)
    backend = getattr(session, 'backend', None)
    connection = getattr(getattr(backend, 'd', None), 'display', None)
    display_info = getattr(connection, 'info', None)
    client_base = getattr(display_info, 'resource_id_base', None)
    if type(client_base) is not int or not 0 < client_base < 2**32:
        client_base = None
    row['interrupted_execution'] = deepcopy(
        getattr(backend, 'interrupted_execution', None))
    row['owner_process_pid'] = pid
    row['owner_x_client_resource_base'] = client_base
    return row


def _control_loop(connection, stop, owner, pid):
    while not stop.is_set():
        try:
            if not connection.poll(0.1):
                continue
            request = connection.recv()
        except (EOFError, OSError):
            return
        if request.get('operation') != 'cancel_guarded':
            response = {'ok':False, 'error':'unsupported control operation'}
        else:
            try:
                result = owner.cancel_guarded(request['token'])
                response = {'ok':True, 'result':result,
                            'snapshot':_owner_snapshot(owner, pid)}
            except BaseException as error:
                response = {'ok':False, 'error_type':type(error).__name__,
                            'error':str(error)[:1000],
                            'snapshot':_owner_snapshot(owner, pid)}
        try:
            connection.send(response)
        except (EOFError, OSError):
            return


def _serve_owned_guarded_session(rpc_connection, control_connection, targets,
                                 directory, display_name, options, owner_factory):
    owner = None
    control_stop = threading.Event()
    control_thread = None
    ready_sent = False
    try:
        owner = (owner_factory(targets, directory, display_name, options)
                 if owner_factory is not None else
                 GuardedSessionOwner(targets, directory, display_name, **options))
        owner.get()
        pid = multiprocessing.current_process().pid
        rpc_connection.send({'ok':True, 'snapshot':_owner_snapshot(owner, pid)})
        ready_sent = True
        control_thread = threading.Thread(
            target=_control_loop,
            args=(control_connection, control_stop, owner, pid),
            name='guarded-owner-control', daemon=True)
        control_thread.start()
        allowed = {'snapshot', 'invoke_guarded', 'recover_input', 'inspect_target',
                   'review_target', 'dispatch', 'inspect_after_dispatch', 'observe', 'close'}
        while True:
            request = rpc_connection.recv()
            operation = request.get('operation')
            if operation not in allowed:
                response = {'ok':False, 'error_type':'ValueError',
                            'error':'unsupported guarded owner operation'}
            else:
                try:
                    arguments = request.get('arguments', {})
                    if operation == 'snapshot':
                        result = owner.snapshot()
                    elif operation == 'invoke_guarded':
                        result = owner.invoke_guarded(**arguments)
                    elif operation == 'recover_input':
                        result = owner.recover_input(**arguments)
                    elif operation == 'inspect_target':
                        result = owner.inspect_target(**arguments)
                    elif operation == 'review_target':
                        result = owner.review_target(**arguments)
                    elif operation == 'dispatch':
                        result = owner.dispatch(**arguments)
                    elif operation == 'inspect_after_dispatch':
                        result = owner.inspect_after_dispatch(**arguments)
                    elif operation == 'observe':
                        from .observe import observe_in_session
                        result = observe_in_session(owner.get(), **arguments)
                    else:
                        result = owner.close()
                    response = {'ok':True, 'result':result,
                                'snapshot':_owner_snapshot(owner, pid)}
                except BaseException as error:
                    response = {'ok':False, 'error_type':type(error).__name__,
                                'error':str(error)[:1000],
                                'snapshot':_owner_snapshot(owner, pid)}
            rpc_connection.send(response)
            if operation == 'close' and response.get('ok'):
                return
    except BaseException as error:
        if not ready_sent:
            try:
                rpc_connection.send({'ok':False, 'error_type':type(error).__name__,
                                     'error':str(error)[:1000]})
            except (EOFError, OSError):
                pass
    finally:
        control_stop.set()
        if control_thread is not None:
            control_thread.join(0.5)
        if owner is not None:
            cleanup = getattr(owner, '_owned_process_test_cleanup', None)
            if cleanup is not None:
                try:
                    cleanup.doCleanups()
                except BaseException:
                    pass
        for connection in (rpc_connection, control_connection):
            try:
                connection.close()
            except OSError:
                pass


class OwnedGuardedSessionOwner(GuardedSessionOwner):
    """GuardedSessionOwner-compatible facade backed by one spawned process.

    This is opt-in. Cancellation may retire the exact owned process after a
    bounded grace, but release remains UNKNOWN unless the child reports and
    confirms it before retirement. No process restart or input replay occurs.
    """

    def __init__(self, targets, directory, display_name=None, *,
                 process_identity=False, query_worker=False,
                 observation_worker=False, window_lifecycle=False,
                 _owner_factory=None):
        super().__init__(targets, directory, display_name,
                         process_identity=process_identity,
                         query_worker=query_worker,
                         observation_worker=observation_worker,
                         window_lifecycle=window_lifecycle)
        self._owner_root = Path(directory)
        self._owner_factory = _owner_factory
        self._rpc = None
        self._control = None
        self._process = None
        self._rpc_lock = threading.Lock()
        self._control_lock = threading.Lock()
        self._snapshot_cache = super().snapshot()
        self._execution_unknown = False
        self._retirement = None
        self.review_required = False

    def _apply_snapshot(self, snapshot):
        self._snapshot_cache = deepcopy(snapshot)
        self.session_id = snapshot.get('session_id', self.session_id)
        self.binding_revision = snapshot.get('binding_revision', self.binding_revision)
        self.targets = deepcopy(snapshot.get('targets', self.targets))
        self.state = snapshot.get('state', self.state)
        self.error = snapshot.get('error', self.error)
        self.review_required = snapshot.get('review_required', self.review_required)
        self.session = SimpleNamespace(
            recovery_required=snapshot.get('recovery_required'),
            backend=SimpleNamespace(
                interrupted_execution=deepcopy(snapshot.get('interrupted_execution'))))

    def _ensure_started(self):
        if self._process is not None:
            if self._process.is_alive() and self.state == 'open':
                return
            if not self._process.is_alive() and self.state == 'open':
                self._execution_unknown = True
                self.state = 'failed'
                self.error = 'owned guarded process exited without an accepted close receipt'
                self.review_required = True
            raise RuntimeError('owned guarded session unavailable: ' + self.state)
        if self.state != 'unopened':
            raise RuntimeError('owned guarded session unavailable: ' + self.state)
        context = multiprocessing.get_context('spawn')
        rpc_parent, rpc_child = context.Pipe(duplex=True)
        control_parent, control_child = context.Pipe(duplex=True)
        process = context.Process(
            target=_serve_owned_guarded_session,
            args=(rpc_child, control_child, self.targets, str(self._owner_root),
                  self.display_name,
                  {'process_identity':self.process_identity,
                   'query_worker':self.query_worker,
                   'observation_worker':self.observation_worker,
                   'window_lifecycle':self.window_lifecycle},
                  self._owner_factory),
            name='guarded-x11-owner-' + self.session_id[:8])
        self.state = 'opening'
        try:
            process.start()
            rpc_child.close()
            control_child.close()
            self._process, self._rpc, self._control = process, rpc_parent, control_parent
            if not rpc_parent.poll(_STARTUP_TIMEOUT_S):
                self._execution_unknown = True
                self._retire('owned guarded process startup timed out')
                raise RuntimeError('owned guarded process startup timed out')
            response = rpc_parent.recv()
            if response.get('ok') is not True:
                self.error = response.get('error_type', 'owner_startup_failed') + ': ' + response.get('error', '')
                self.state = 'failed'
                process.join(_JOIN_TIMEOUT_S)
                raise RuntimeError(self.error)
            self._apply_snapshot(response['snapshot'])
            self.state = 'open'
        except BaseException:
            if self.state == 'opening':
                self.state = 'failed'
            for connection in (rpc_parent, control_parent, rpc_child, control_child):
                try:
                    connection.close()
                except OSError:
                    pass
            raise

    def _request_locked(self, operation, arguments=None):
        self._ensure_started()
        if self._rpc is None:
            raise RuntimeError('owned guarded RPC channel unavailable')
        self._rpc.send({'operation':operation, 'arguments':arguments or {}})
        response = self._rpc.recv()
        snapshot = response.get('snapshot')
        if isinstance(snapshot, dict):
            self._apply_snapshot(snapshot)
        if response.get('ok') is not True:
            self._execution_unknown = True
            self.review_required = True
            raise RuntimeError(response.get('error_type', 'owned_call_failed') + ': ' +
                               response.get('error', ''))
        return response.get('result')

    def _call(self, method, **arguments):
        with self._rpc_lock:
            return self._request_locked(method, arguments)

    def get(self):
        self._ensure_started()
        return self.session

    def snapshot(self):
        row = deepcopy(self._snapshot_cache)
        if self._process is None:
            process = {'pid':None, 'alive':False, 'exitcode':None,
                       'retired':False, 'release_confirmed':None}
        else:
            alive = self._process.is_alive()
            if not alive and self.state == 'open':
                self._execution_unknown = True
                self.state = 'failed'
                self.error = 'owned guarded process exited without an accepted close receipt'
                self.review_required = True
            process = {'pid':self._process.pid, 'alive':alive,
                       'exitcode':self._process.exitcode,
                       'retired':self._retirement is not None,
                       'release_confirmed':False if self._execution_unknown else None,
                       'x_client_resource_base':self._snapshot_cache.get(
                           'owner_x_client_resource_base')}
        row.update(session_id=self.session_id, mode='guarded-x11-owned-process',
                   state=self.state, binding_revision=self.binding_revision,
                   targets=deepcopy(self.targets), error=self.error,
                   review_required=self.review_required,
                   owner_process=process,
                   cleanup_status='UNKNOWN' if self._execution_unknown else None,
                   authority_granted=False, restart_allowed=False)
        return row

    def invoke_guarded(self, operation, arguments, call_root):
        return self._call('invoke_guarded', operation=operation,
                          arguments=deepcopy(arguments), call_root=Path(call_root))

    def recover_input(self, current_binding_revision, target=None, region=None,
                      capture_directory=None):
        arguments = dict(current_binding_revision=current_binding_revision,
                         target=target, region=region,
                         capture_directory=capture_directory)
        return self._call('recover_input', **arguments)

    def inspect_target(self, target, screen_region=None, capture_directory=None):
        return self._call('inspect_target', target=target, screen_region=screen_region,
                          capture_directory=capture_directory)

    def review_target(self, target, window_id, review_id, screen_region=None,
                      capture_directory=None):
        return self._call('review_target', target=target, window_id=window_id,
                          review_id=review_id, screen_region=screen_region,
                          capture_directory=capture_directory)

    def inspect_after_dispatch(self, report, target, screen_region=None,
                               capture_directory=None, wait_ms=None):
        return self._call('inspect_after_dispatch', report=deepcopy(report), target=target,
                          screen_region=screen_region, capture_directory=capture_directory,
                          wait_ms=wait_ms)

    def dispatch(self, program, *, current_observation_seq,
                 current_binding_revision, capture_directory=None):
        return self._call('dispatch', program=deepcopy(program),
                          current_observation_seq=current_observation_seq,
                          current_binding_revision=current_binding_revision,
                          capture_directory=capture_directory)

    def observe(self, *, target, frame, region, capture_directory=None):
        return self._call('observe', target=target, frame=frame, region=region,
                          capture_directory=capture_directory)

    def cancel_guarded(self, token):
        if self._process is None or not self._process.is_alive() or self._control is None:
            return {'status':'not_active', 'input_dispatched':False,
                    'release_confirmed':False}
        with self._control_lock:
            try:
                self._control.send({'operation':'cancel_guarded', 'token':token})
                if not self._control.poll(_STARTUP_TIMEOUT_S):
                    self._execution_unknown = True
                    self.review_required = True
                    return {'status':'cancel_unconfirmed', 'input_dispatched':None,
                            'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                            'replay_allowed':False}
                response = self._control.recv()
            except (EOFError, OSError) as error:
                self._execution_unknown = True
                self.review_required = True
                return {'status':'cancel_unconfirmed', 'error':repr(error),
                        'input_dispatched':None, 'release_confirmed':False,
                        'cleanup_status':'UNKNOWN', 'replay_allowed':False}
        if response.get('ok') is not True:
            self._execution_unknown = True
            self.review_required = True
            return {'status':'cancel_unconfirmed', 'input_dispatched':None,
                    'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                    'replay_allowed':False, 'error':response.get('error')}
        result = response['result']
        if result.get('status') != 'cancel_requested':
            return result
        if self._rpc_lock.acquire(timeout=_CANCEL_RETIRE_GRACE_S):
            self._rpc_lock.release()
            return result
        retirement = self._retire('cancel retirement grace elapsed')
        self._execution_unknown = True
        self.review_required = True
        return dict(result, owner_process_retired=retirement['retired'],
                    owner_process_exitcode=retirement['exitcode'],
                    release_confirmed=False, cleanup_status='UNKNOWN',
                    task_success=None, replay_allowed=False,
                    late_server_request_possible=True)

    def _retire(self, reason):
        process = self._process
        if process is None:
            return {'retired':False, 'exitcode':None, 'reason':reason}
        if process.is_alive():
            process.terminate()
            process.join(_JOIN_TIMEOUT_S)
        retired = not process.is_alive()
        self._retirement = {'reason':reason, 'retired':retired,
                            'exitcode':process.exitcode}
        self.state = 'failed'
        self.error = reason
        self._execution_unknown = True
        self.review_required = True
        return self._retirement

    def retire(self, reason='explicit owner retirement'):
        """Retire only this exact child; never report input release from death."""
        return self._retire(reason)

    def close(self):
        if self.close_report is not None:
            return deepcopy(self.close_report)
        if self._process is None:
            self.state = 'closed'
            row = {'status':'closed', 'session_id':self.session_id,
                   'authority_granted':False, 'restart_allowed':False,
                   'release_attempted':False, 'release_confirmed':None,
                   'connection_close_attempted':False, 'verified':True}
            self.close_report = row
            return deepcopy(row)
        acquired = self._rpc_lock.acquire(timeout=_CLOSE_TIMEOUT_S)
        if not acquired:
            retirement = self._retire('close timed out waiting for owned operation')
            row = {'status':'cleanup_failed', 'session_id':self.session_id,
                   'release_attempted':True, 'release_confirmed':False,
                   'cleanup_status':'UNKNOWN', 'task_success':None,
                   'replay_allowed':False, 'connection_close_attempted':False,
                   'owner_process_retired':retirement['retired'],
                   'owner_process_exitcode':retirement['exitcode'],
                   'late_server_request_possible':True, 'verified':False}
            self.close_report = row
            return deepcopy(row)
        try:
            try:
                report = self._request_locked('close')
            except (EOFError, OSError, RuntimeError) as error:
                self._execution_unknown = True
                self.review_required = True
                retirement = self._retire('owned close result unavailable')
                report = {'status':'cleanup_failed', 'error':repr(error),
                          'release_attempted':True, 'release_confirmed':False,
                          'cleanup_status':'UNKNOWN', 'task_success':None,
                          'replay_allowed':False, 'verified':False,
                          'owner_process_retired':retirement['retired'],
                          'owner_process_exitcode':retirement['exitcode'],
                          'late_server_request_possible':True}
        finally:
            self._rpc_lock.release()
        self._process.join(_JOIN_TIMEOUT_S)
        if self._process.is_alive():
            retirement = self._retire('owned process did not exit after close receipt')
            report = dict(report, status='cleanup_failed', verified=False,
                          release_confirmed=False, cleanup_status='UNKNOWN',
                          owner_process_retired=retirement['retired'],
                          owner_process_exitcode=retirement['exitcode'],
                          late_server_request_possible=True)
        else:
            release = report.get('release')
            neutral = (report.get('release_attempted') is False or
                       (isinstance(release, dict) and release.get('verified') is True
                        and release.get('keys_down') == []
                        and release.get('buttons_down') == []))
            verified_close = (report.get('status') == 'closed'
                              and report.get('connection_close_attempted') is True
                              and neutral)
            report = dict(report, verified=verified_close,
                          release_confirmed=(release.get('verified') is True
                              if isinstance(release, dict) else None))
        if not self._process.is_alive() and report.get('verified') is True:
            self.state = 'closed'
        else:
            report = dict(report, status='cleanup_failed', verified=False,
                          release_confirmed=False, cleanup_status='UNKNOWN')
            self._execution_unknown = True
            self.review_required = True
            self.state = 'failed'
        self.close_report = deepcopy(report)
        return deepcopy(report)
