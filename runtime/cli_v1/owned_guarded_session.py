"""Explicit process boundary for the standard guarded-X11 session.

The child owns the complete NativeHandleBridge session. Parent calls are
allowlisted RPCs; cancellation uses a separate pipe. Retiring the child bounds
its future user-space writes, but never proves that queued server requests or
physical input were released.
"""
from copy import deepcopy
import hashlib
import json
import multiprocessing
from pathlib import Path
import threading
import time
from types import SimpleNamespace

from .mcp_guarded import GuardedSessionOwner
from ..guarded_x11_v1.xres_client_fence import (
    supervise_xres_worker, wait_for_client_disconnect_supervised)


_STARTUP_TIMEOUT_S = 5.0
_CLOSE_TIMEOUT_S = 5.0
# Cancellation must reach the bounded retirement path promptly even when the
# owner's control thread is waiting on platform I/O. Keep this independent of
# startup's more permissive readiness budget.
_CANCEL_CONTROL_RESPONSE_TIMEOUT_S = 0.25
_CANCEL_RETIRE_GRACE_S = 1.0
_RETIRE_TERMINATE_GRACE_S = 0.25
_RETIRE_KILL_GRACE_S = 0.25
# A final short reap window covers children that exit just after the SIGKILL
# grace poll reports them alive. Polling is required because Process.join may
# return immediately while the OS process is still completing termination.
_RETIRE_KILL_SETTLE_GRACE_S = 0.01
_JOIN_TIMEOUT_S = 1.0
_XRES_DISCONNECT_TIMEOUT_S = 0.15
_XRES_DISCONNECT_TERMINATE_GRACE_S = 0.1
# The spawned fresh client must import, connect, emit exact releases, sync, and
# read back. Reserve 1.5 seconds for this bounded worker while retaining
# headroom under the caller's three-second cancellation target; timeout still
# means UNKNOWN, never release.
_RETIRED_RELEASE_TIMEOUT_S = 1.5
_RETIRED_RELEASE_TERMINATE_GRACE_S = 0.1
_OWNER_INPUT_OBLIGATIONS_SCHEMA = 'agent-interface/owner-input-obligations-v1'
_OWNER_INPUT_OBLIGATIONS_CAPACITY = 8192
_OWNER_INPUT_OBLIGATIONS_MAGIC = b'AIOL'
_OWNER_INPUT_OBLIGATIONS_HEADER_SIZE = 40


def _publish_owner_input_obligations(shared_state, keys, buttons):
    state = {'schema':_OWNER_INPUT_OBLIGATIONS_SCHEMA,
             'keys':dict(keys), 'buttons':list(buttons)}
    payload = json.dumps(state, separators=(',', ':')).encode('utf-8')
    if len(payload) + _OWNER_INPUT_OBLIGATIONS_HEADER_SIZE > len(shared_state):
        payload = json.dumps({'schema':_OWNER_INPUT_OBLIGATIONS_SCHEMA,
                              'status':'overflow'}, separators=(',', ':')).encode('utf-8')
    digest = hashlib.sha256(payload).digest()
    header = (len(payload).to_bytes(4, 'big') + digest)
    # Invalidate first and publish the commit marker last. A terminated writer
    # can leave only a rejected record; the parent reads after child retirement.
    shared_state[0] = 0
    for index, byte in enumerate(header, start=4):
        shared_state[index] = byte
    for index, byte in enumerate(payload, start=_OWNER_INPUT_OBLIGATIONS_HEADER_SIZE):
        shared_state[index] = byte
    for index, byte in enumerate(_OWNER_INPUT_OBLIGATIONS_MAGIC[1:], start=1):
        shared_state[index] = byte
    shared_state[0] = _OWNER_INPUT_OBLIGATIONS_MAGIC[0]


def _read_owner_input_obligations(shared_state):
    if shared_state is None:
        return {'status':'unavailable', 'reason':'shared_state_unavailable'}
    try:
        record = bytes(shared_state[:])
    except Exception as error:
        return {'status':'unknown', 'reason':'shared_state_invalid',
                'error_type':type(error).__name__}
    if record[:4] != _OWNER_INPUT_OBLIGATIONS_MAGIC:
        return {'status':'unknown', 'reason':'shared_state_uncommitted'}
    payload_length = int.from_bytes(record[4:8], 'big')
    if (payload_length <= 0
            or payload_length + _OWNER_INPUT_OBLIGATIONS_HEADER_SIZE > len(record)):
        return {'status':'unknown', 'reason':'shared_state_length_invalid'}
    expected_digest = record[8:_OWNER_INPUT_OBLIGATIONS_HEADER_SIZE]
    payload = record[_OWNER_INPUT_OBLIGATIONS_HEADER_SIZE:
                     _OWNER_INPUT_OBLIGATIONS_HEADER_SIZE + payload_length]
    if hashlib.sha256(payload).digest() != expected_digest:
        return {'status':'unknown', 'reason':'shared_state_checksum_invalid'}
    try:
        state = json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {'status':'unknown', 'reason':'shared_state_payload_invalid'}
    if (not isinstance(state, dict)
            or state.get('schema') != _OWNER_INPUT_OBLIGATIONS_SCHEMA):
        return {'status':'unknown', 'reason':'shared_state_schema_invalid'}
    if state.get('status') == 'overflow':
        return {'status':'unknown', 'reason':'shared_state_overflow'}
    keys, buttons = state.get('keys'), state.get('buttons')
    if (not isinstance(keys, dict) or not isinstance(buttons, list)
            or any(type(name) is not str or type(code) is not int
                   or not 0 <= code < 256 for name, code in keys.items())
            or any(type(button) is not str
                   or button not in ('left', 'middle', 'right', 'x1', 'x2')
                   for button in buttons)):
        return {'status':'unknown', 'reason':'shared_state_obligations_invalid'}
    return {'status':'snapshot',
            'obligations':{'keys':keys, 'buttons':buttons}}


def _bind_owner_input_obligation_publisher(owner, shared_state):
    session = getattr(owner, 'session', None)
    backend = getattr(session, 'backend', None)
    setter = getattr(backend, 'set_input_obligation_publisher', None)
    if not callable(setter):
        raise RuntimeError('owned X11 backend cannot publish live input obligations')
    setter(lambda keys, buttons: _publish_owner_input_obligations(
        shared_state, keys, buttons))


def _release_retired_inputs_worker(send_connection, display_name, keys, buttons):
    """Release only exact prearmed inputs on a fresh X client."""
    backend = None
    try:
        from runtime.backends.x11_v1.backend import X11Backend

        backend = X11Backend(display_name, {})
        backend.held_keycodes = dict(keys)
        backend.held_buttons = set(buttons)
        release = backend.release_all()
        backend.close()
        backend = None
        send_connection.send({
            'status':'released' if release.get('verified') is True else 'unknown',
            'release':release,
        })
    except Exception as error:
        try:
            send_connection.send({'status':'unknown', 'reason':'release_failed',
                                  'error_type':type(error).__name__,
                                  'error':str(error)})
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception:
                pass
        try:
            send_connection.close()
        except OSError:
            pass


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
    row['owner_input_obligations'] = {
        'keys': deepcopy(getattr(backend, 'held_keycodes', {})),
        'buttons': sorted(getattr(backend, 'held_buttons', set())),
    }
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
                                 directory, display_name, options, owner_factory,
                                 input_obligations_state):
    owner = None
    control_stop = threading.Event()
    control_thread = None
    ready_sent = False
    try:
        owner = (owner_factory(targets, directory, display_name, options)
                 if owner_factory is not None else
                 GuardedSessionOwner(targets, directory, display_name, **options))
        owner.get()
        _bind_owner_input_obligation_publisher(owner, input_obligations_state)
        pid = multiprocessing.current_process().pid
        rpc_connection.send({'ok':True, 'snapshot':_owner_snapshot(owner, pid)})
        ready_sent = True
        control_thread = threading.Thread(
            target=_control_loop,
            args=(control_connection, control_stop, owner, pid),
            name='guarded-owner-control', daemon=True)
        control_thread.start()
        allowed = {'snapshot', 'invoke_guarded', 'run_compiled_profile', 'recover_input', 'inspect_target',
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
                    elif operation == 'run_compiled_profile':
                        result = owner.run_compiled_profile(**arguments)
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
        self._owner_client_disconnect = None
        self._owner_input_obligations = {'keys':{}, 'buttons':[]}
        self._owner_input_obligations_source = 'parent_initial_state'
        self._owner_input_obligations_state = None
        self._owner_input_obligations_live_read = {'status':'not_read'}
        self._owner_release_attempt = None
        self.review_required = False

    def _apply_snapshot(self, snapshot):
        self._snapshot_cache = deepcopy(snapshot)
        self.session_id = snapshot.get('session_id', self.session_id)
        self.binding_revision = snapshot.get('binding_revision', self.binding_revision)
        self.targets = deepcopy(snapshot.get('targets', self.targets))
        self.state = snapshot.get('state', self.state)
        self.error = snapshot.get('error', self.error)
        self.review_required = snapshot.get('review_required', self.review_required)
        obligations = snapshot.get('owner_input_obligations')
        if (isinstance(obligations, dict)
                and isinstance(obligations.get('keys'), dict)
                and isinstance(obligations.get('buttons'), list)
                and all(type(name) is str and type(code) is int
                        and 0 <= code < 256
                        for name, code in obligations['keys'].items())
                and all(type(button) is str
                        for button in obligations['buttons'])):
            self._owner_input_obligations = deepcopy(obligations)
            self._owner_input_obligations_source = 'child_rpc_snapshot'
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
        input_obligations_state = context.RawArray(
            'B', _OWNER_INPUT_OBLIGATIONS_CAPACITY)
        self._owner_input_obligations_state = input_obligations_state
        _publish_owner_input_obligations(input_obligations_state, {}, [])
        process = context.Process(
            target=_serve_owned_guarded_session,
            args=(rpc_child, control_child, self.targets, str(self._owner_root),
                  self.display_name,
                  {'process_identity':self.process_identity,
                   'query_worker':self.query_worker,
                   'observation_worker':self.observation_worker,
                   'window_lifecycle':self.window_lifecycle},
                  self._owner_factory, input_obligations_state),
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
                   owner_client_disconnect=deepcopy(self._owner_client_disconnect),
                   owner_input_obligations=deepcopy(self._owner_input_obligations),
                   owner_input_obligations_source=self._owner_input_obligations_source,
                   owner_input_obligations_live_read=deepcopy(
                       self._owner_input_obligations_live_read),
                   owner_release_attempt=deepcopy(self._owner_release_attempt),
                   cleanup_status='UNKNOWN' if self._execution_unknown else None,
                   authority_granted=False, restart_allowed=False)
        return row

    def _observe_owner_client_disconnect(self):
        resource_base = self._snapshot_cache.get('owner_x_client_resource_base')
        if type(resource_base) is not int or not 0 < resource_base < 2**32:
            return {'status':'unknown', 'reason':'resource_base_unavailable',
                    'worker_retired':None}
        expected_pid = self._snapshot_cache.get('owner_process_pid')
        if type(expected_pid) is not int or not 0 < expected_pid < 2**32:
            return {'status':'unknown', 'reason':'owner_pid_unavailable',
                    'worker_retired':None}
        try:
            result = wait_for_client_disconnect_supervised(
                self.display_name, resource_base, expected_pid=expected_pid,
                timeout_s=_XRES_DISCONNECT_TIMEOUT_S,
                terminate_grace_s=_XRES_DISCONNECT_TERMINATE_GRACE_S)
        except Exception as error:
            return {'status':'unknown', 'reason':'supervisor_failed',
                    'error':repr(error), 'worker_retired':None}
        if (not isinstance(result, dict)
                or result.get('status') not in ('disconnected', 'still_connected', 'unknown')):
            return {'status':'unknown', 'reason':'malformed_supervisor_result',
                    'worker_retired':None}
        return deepcopy(result)

    def _release_retired_owner_inputs(self, obligations):
        keys = obligations.get('keys') if isinstance(obligations, dict) else None
        buttons = obligations.get('buttons') if isinstance(obligations, dict) else None
        if (not isinstance(keys, dict) or not isinstance(buttons, list)
                or not keys and not buttons
                or any(type(name) is not str or type(code) is not int
                       or not 0 <= code < 256 for name, code in keys.items())
                or any(type(button) is not str
                       or button not in ('left', 'middle', 'right', 'x1', 'x2')
                       for button in buttons)):
            return {'status':'unknown', 'reason':'invalid_or_empty_obligations',
                    'worker_retired':None}
        try:
            result = supervise_xres_worker(
                _release_retired_inputs_worker,
                (self.display_name, keys, buttons),
                timeout_s=_RETIRED_RELEASE_TIMEOUT_S,
                terminate_grace_s=_RETIRED_RELEASE_TERMINATE_GRACE_S,
                accepted_statuses=('released', 'unknown'))
        except Exception as error:
            return {'status':'unknown', 'reason':'release_supervisor_failed',
                    'error':repr(error), 'worker_retired':None}
        release = result.get('release') if isinstance(result, dict) else None
        if (result.get('status') == 'released' and isinstance(release, dict)
                and release.get('verified') is True
                and release.get('keys_down') == []
                and release.get('buttons_down') == []):
            return {'status':'readback_verified',
                    'worker_retired':result.get('worker_retired'),
                    'worker_exitcode':result.get('worker_exitcode'),
                    'elapsed_ms':result.get('elapsed_ms'),
                    'release':deepcopy(release)}
        return {'status':'unknown', 'reason':result.get('reason', 'release_unverified'),
                'worker_retired':result.get('worker_retired'),
                'worker_exitcode':result.get('worker_exitcode'),
                'elapsed_ms':result.get('elapsed_ms'),
                'release':deepcopy(release)}

    def _cleanup_after_owner_retirement(self, retirement):
        if retirement.get('retired') is True:
            live_read = _read_owner_input_obligations(
                getattr(self, '_owner_input_obligations_state', None))
            self._owner_input_obligations_live_read = live_read
            if live_read.get('status') == 'snapshot':
                self._owner_input_obligations = deepcopy(live_read['obligations'])
                self._owner_input_obligations_source = 'retired_child_shared_state'
            client_disconnect = self._observe_owner_client_disconnect()
        else:
            self._owner_input_obligations_live_read = {
                'status':'not_read', 'reason':'owner_not_retired'}
            client_disconnect = {'status':'unknown', 'reason':'owner_not_retired',
                                 'worker_retired':None}
        self._owner_client_disconnect = client_disconnect
        if (retirement.get('retired') is True
                and client_disconnect.get('status') == 'disconnected'
                and self._owner_input_obligations_live_read.get('status') == 'snapshot'):
            release_attempt = self._release_retired_owner_inputs(
                getattr(self, '_owner_input_obligations', {'keys':{}, 'buttons':[]}))
        else:
            release_attempt = {'status':'not_attempted',
                               'reason':('owner_not_retired'
                                   if retirement.get('retired') is not True else
                                   'owner_disconnect_not_confirmed'
                                   if client_disconnect.get('status') != 'disconnected' else
                                   'owner_input_obligations_unavailable')}
        self._owner_release_attempt = release_attempt
        return client_disconnect, release_attempt

    def _retirement_cleanup_result_fields(self, retirement):
        client_disconnect, release_attempt = (
            self._cleanup_after_owner_retirement(retirement))
        return {
            'owner_client_disconnect':deepcopy(client_disconnect),
            **self._owner_input_obligations_result_fields(),
            'owner_release_attempt':deepcopy(release_attempt),
        }

    def _owner_input_obligations_result_fields(self):
        return {
            'owner_input_obligations':deepcopy(getattr(
                self, '_owner_input_obligations', {'keys':{}, 'buttons':[]})),
            'owner_input_obligations_source':getattr(
                self, '_owner_input_obligations_source', 'parent_initial_state'),
            'owner_input_obligations_live_read':deepcopy(getattr(
                self, '_owner_input_obligations_live_read', {'status':'not_read'})),
        }

    def invoke_guarded(self, operation, arguments, call_root):
        return self._call('invoke_guarded', operation=operation,
                          arguments=deepcopy(arguments), call_root=Path(call_root))

    def run_compiled_profile(self, interface, bindings, predicate_rules,
                             effect_rules, call_root, cancel_token):
        return self._call('run_compiled_profile', interface=deepcopy(interface),
                          bindings=deepcopy(bindings),
                          predicate_rules=deepcopy(predicate_rules),
                          effect_rules=deepcopy(effect_rules),
                          call_root=str(call_root), cancel_token=cancel_token)

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

    def _cancel_requires_owner_retirement(self, result):
        if result.get('owner_process_retired') is True:
            return False
        if result.get('late_server_request_possible') is True:
            return True
        obligations = result.get('owner_input_obligations')
        if not isinstance(obligations, dict):
            obligations = getattr(self, '_owner_input_obligations', None)
        if not isinstance(obligations, dict):
            return True
        keys = obligations.get('keys')
        buttons = obligations.get('buttons')
        if not isinstance(keys, dict) or not isinstance(buttons, list):
            return True
        return bool(keys) or bool(buttons)

    def cancel_guarded(self, token):
        if self._process is None or not self._process.is_alive() or self._control is None:
            return {'status':'not_active', 'input_dispatched':False,
                    'release_confirmed':False}
        with self._control_lock:
            try:
                self._control.send({'operation':'cancel_guarded', 'token':token})
                if not self._control.poll(_CANCEL_CONTROL_RESPONSE_TIMEOUT_S):
                    self._execution_unknown = True
                    self.review_required = True
                    retirement = self._retire('cancel control response unconfirmed')
                    client_disconnect, release_attempt = (
                        self._cleanup_after_owner_retirement(retirement))
                    return {'status':'cancel_unconfirmed', 'input_dispatched':None,
                            'owner_process_retired':retirement['retired'],
                            'owner_process_exitcode':retirement['exitcode'],
                            'owner_client_disconnect':deepcopy(client_disconnect),
                            **self._owner_input_obligations_result_fields(),
                            'owner_release_attempt':deepcopy(release_attempt),
                            'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                            'task_success':None, 'replay_allowed':False,
                            'late_server_request_possible':True}
                response = self._control.recv()
            except (EOFError, OSError) as error:
                self._execution_unknown = True
                self.review_required = True
                retirement = self._retire('cancel control response unconfirmed')
                client_disconnect, release_attempt = (
                    self._cleanup_after_owner_retirement(retirement))
                return {'status':'cancel_unconfirmed', 'error':repr(error),
                        'input_dispatched':None,
                        'owner_process_retired':retirement['retired'],
                        'owner_process_exitcode':retirement['exitcode'],
                        'owner_client_disconnect':deepcopy(client_disconnect),
                        **self._owner_input_obligations_result_fields(),
                        'owner_release_attempt':deepcopy(release_attempt),
                        'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                        'task_success':None, 'replay_allowed':False,
                        'late_server_request_possible':True}
        if response.get('ok') is not True:
            self._execution_unknown = True
            self.review_required = True
            retirement = self._retire('cancel control response unconfirmed')
            client_disconnect, release_attempt = (
                self._cleanup_after_owner_retirement(retirement))
            return {'status':'cancel_unconfirmed', 'input_dispatched':None,
                    'owner_process_retired':retirement['retired'],
                    'owner_process_exitcode':retirement['exitcode'],
                    'owner_client_disconnect':deepcopy(client_disconnect),
                    **self._owner_input_obligations_result_fields(),
                    'owner_release_attempt':deepcopy(release_attempt),
                    'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                    'task_success':None, 'replay_allowed':False,
                    'late_server_request_possible':True,
                    'error':response.get('error')}
        self._apply_snapshot(response.get('snapshot', {}))
        result = response['result']
        if result.get('status') != 'cancel_requested':
            return result
        requires_retirement = self._cancel_requires_owner_retirement(result)
        if (not requires_retirement
                and self._rpc_lock.acquire(timeout=_CANCEL_RETIRE_GRACE_S)):
            self._rpc_lock.release()
            return result
        retirement_reason = ('cancel left input or server-request obligation'
                             if requires_retirement else
                             'cancel retirement grace elapsed')
        retirement = self._retire(retirement_reason)
        client_disconnect, release_attempt = self._cleanup_after_owner_retirement(
            retirement)
        self._execution_unknown = True
        self.review_required = True
        return dict(result, owner_process_retired=retirement['retired'],
                    owner_process_exitcode=retirement['exitcode'],
                    owner_client_disconnect=deepcopy(client_disconnect),
                    **self._owner_input_obligations_result_fields(),
                    owner_release_attempt=deepcopy(release_attempt),
                    release_confirmed=False, cleanup_status='UNKNOWN',
                    task_success=None, replay_allowed=False,
                    late_server_request_possible=True)

    def _retire(self, reason):
        process = self._process
        if process is None:
            return {'retired':False, 'exitcode':None, 'reason':reason}
        kill_escalated = False
        if process.is_alive():
            process.terminate()
            process.join(_RETIRE_TERMINATE_GRACE_S)
            if process.is_alive() and callable(getattr(process, 'kill', None)):
                kill_escalated = True
                process.kill()
                process.join(_RETIRE_KILL_GRACE_S)
        # A child may exit between the kill grace poll and this final check.
        # Give that already-killed process one short reap window before
        # reporting it alive; a non-None exitcode is definitive retirement.
        retired = not process.is_alive()
        exitcode = process.exitcode
        if not retired and exitcode is None and kill_escalated:
            deadline = time.monotonic() + _RETIRE_KILL_SETTLE_GRACE_S
            while not retired and exitcode is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(0.001, remaining))
                retired = not process.is_alive()
                exitcode = process.exitcode
        retired = retired or exitcode is not None
        self._retirement = {'reason':reason, 'retired':retired,
                            'exitcode':exitcode,
                            'kill_escalated':kill_escalated}
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
        retirement = getattr(self, '_retirement', None)
        client_disconnect = getattr(self, '_owner_client_disconnect', None)
        previous_release_attempt = getattr(self, '_owner_release_attempt', None)
        if (retirement is not None
                and retirement.get('retired') is True
                and not self._process.is_alive()
                and client_disconnect is not None
                and previous_release_attempt is not None):
            if previous_release_attempt.get('status') == 'readback_verified':
                release_attempt = deepcopy(previous_release_attempt)
            else:
                # An explicit close after retirement may run after the platform
                # has recovered. Recheck owner disconnect and make one bounded
                # release-only attempt; never reconnect the retired owner or
                # replay its task operation.
                client_disconnect, release_attempt = (
                    self._cleanup_after_owner_retirement(retirement))
                self._owner_client_disconnect = deepcopy(client_disconnect)
                self._owner_release_attempt = deepcopy(release_attempt)
            report = {
                'status':'cleanup_failed', 'session_id':self.session_id,
                'release_attempted':release_attempt.get('status') != 'not_attempted',
                'release_confirmed':False, 'cleanup_status':'UNKNOWN',
                'task_success':None, 'replay_allowed':False, 'verified':False,
                'connection_close_attempted':False,
                'owner_client_disconnect':deepcopy(client_disconnect),
                **self._owner_input_obligations_result_fields(),
                'owner_release_attempt':release_attempt,
                'owner_process_retired':True,
                'owner_process_exitcode':self._process.exitcode,
                'late_server_request_possible':True,
                'retirement_reason':retirement.get('reason'),
            }
            if self.error is not None:
                report['error'] = self.error
            self.close_report = deepcopy(report)
            self._execution_unknown = True
            self.review_required = True
            self.state = 'failed'
            return deepcopy(report)
        retirement_cleanup = None
        cleanup_after_retirement_attempted = False

        def retirement_cleanup_fields(retirement):
            nonlocal retirement_cleanup, cleanup_after_retirement_attempted
            if cleanup_after_retirement_attempted:
                return retirement_cleanup
            retirement_cleanup = self._retirement_cleanup_result_fields(retirement)
            if retirement.get('retired') is True:
                cleanup_after_retirement_attempted = True
            return retirement_cleanup

        acquired = self._rpc_lock.acquire(timeout=_CLOSE_TIMEOUT_S)
        if not acquired:
            retirement = self._retire('close timed out waiting for owned operation')
            row = {'status':'cleanup_failed', 'session_id':self.session_id,
                   'release_attempted':True, 'release_confirmed':False,
                   'cleanup_status':'UNKNOWN', 'task_success':None,
                   'replay_allowed':False, 'connection_close_attempted':False,
                   **retirement_cleanup_fields(retirement),
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
                          **retirement_cleanup_fields(retirement),
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
                          task_success=None, replay_allowed=False,
                          late_server_request_possible=True,
                          **retirement_cleanup_fields(retirement),
                          owner_process_retired=retirement['retired'],
                          owner_process_exitcode=retirement['exitcode'])
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
