"""XRes client-presence query; not a release receipt."""
import math
import multiprocessing
import sys
import time


def _validate_duration(name, value, *, allow_zero=False):
    if (type(value) not in (int, float) or not math.isfinite(value)
            or value < 0 or (not allow_zero and value == 0)):
        raise ValueError(name + ' must be a finite positive duration')


def supervise_xres_worker(target, args, *, timeout_s, terminate_grace_s=0.1,
                           accepted_statuses=('disconnected', 'still_connected', 'unknown')):
    """Run one worker under an external process deadline.

    A synchronous X request can exceed the worker's cooperative deadline. This
    supervisor bounds the query wait after process creation and reports UNKNOWN
    unless the worker returned a result and exited cleanly. Process creation and
    OS scheduling are outside that query budget. It does not prove input release.
    """
    _validate_duration('timeout_s', timeout_s)
    _validate_duration('terminate_grace_s', terminate_grace_s)
    if not callable(target) or not isinstance(args, tuple):
        raise TypeError('target must be callable and args must be a tuple')
    if (not isinstance(accepted_statuses, tuple) or not accepted_statuses
            or any(type(status) is not str or not status for status in accepted_statuses)):
        raise ValueError('accepted_statuses must be a non-empty tuple of strings')

    started = time.monotonic()
    deadline = started + timeout_s
    receive, send = None, None
    process = None
    process_started = False
    result = None
    try:
        context = multiprocessing.get_context('spawn')
        receive, send = context.Pipe(duplex=False)
        process = context.Process(target=target, args=(send, *args),
                                  name='xres-disconnect-observer')
        process.start()
        process_started = True
        send.close()
        send = None
        if receive.poll(max(0.0, deadline - time.monotonic())):
            try:
                result = receive.recv()
            except (EOFError, OSError):
                result = None
    except Exception as error:
        result = None
        reason = 'worker_start_failed'
        error_text = repr(error)
    else:
        reason = 'supervision_timeout'
        error_text = None

    forced_stop = False
    if process_started:
        process.join(terminate_grace_s if result is not None else 0)
        if process.is_alive():
            forced_stop = True
            process.terminate()
            process.join(terminate_grace_s)
        if process.is_alive() and hasattr(process, 'kill'):
            process.kill()
            process.join(terminate_grace_s)
        try:
            worker_retired = not process.is_alive()
        except (AssertionError, ValueError):
            worker_retired = False
        exitcode = process.exitcode
    else:
        worker_retired = None
        exitcode = None

    elapsed_ms = (time.monotonic() - started) * 1000.0
    if (isinstance(result, dict) and worker_retired and not forced_stop
            and exitcode == 0
            and result.get('status') in accepted_statuses):
        outcome = dict(result)
        outcome.update(worker_retired=True, worker_exitcode=exitcode,
                       elapsed_ms=elapsed_ms)
    else:
        if forced_stop:
            reason = ('worker_did_not_exit_cleanly' if result is not None
                      else 'supervision_timeout')
        elif result is not None and (
                not isinstance(result, dict)
                or result.get('status') not in accepted_statuses):
            reason = 'malformed_worker_result'
        elif process_started and not process.is_alive() and result is None:
            reason = 'worker_exited_without_result'
        outcome = {'status':'unknown', 'reason':reason,
                   'worker_retired':worker_retired, 'worker_exitcode':exitcode,
                   'elapsed_ms':elapsed_ms}
        if error_text is not None:
            outcome['error'] = error_text
    for connection in (send, receive):
        if connection is not None:
            try:
                connection.close()
            except OSError:
                pass
    return outcome


def _xres_disconnect_worker(send_connection, display_name, resource_base,
                            deadline_ns, poll_interval_s):
    display = None
    try:
        from Xlib.display import Display

        display = Display(display_name)
        remaining_s = max(0.0, (deadline_ns - time.monotonic_ns()) / 1_000_000_000)
        disconnected = wait_for_client_disconnect(
            display, resource_base, timeout_s=remaining_s,
            poll_interval_s=poll_interval_s)
        send_connection.send({'status':'disconnected' if disconnected
                              else 'still_connected'})
    except Exception as error:
        try:
            send_connection.send({'status':'unknown', 'reason':'query_failed',
                                  'error_type':type(error).__name__,
                                  'error':str(error)})
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        if display is not None:
            try:
                display.close()
            except Exception:
                pass
        try:
            send_connection.close()
        except OSError:
            pass


def wait_for_client_disconnect_supervised(display_name, resource_base, *,
                                          timeout_s=0.15,
                                          poll_interval_s=0.01,
                                          terminate_grace_s=0.1):
    """Observe exact XRes client disappearance with a killable query bound.

    `disconnected` only means the XRes reply omitted this client. It is not a
    queue-drained fence or a release receipt. Any unsupported platform, query
    error, or worker timeout returns `unknown` and must preserve UNKNOWN cleanup.
    """
    _validate_duration('timeout_s', timeout_s)
    _validate_duration('poll_interval_s', poll_interval_s)
    _validate_duration('terminate_grace_s', terminate_grace_s)
    if type(resource_base) is not int or not 0 <= resource_base < 2**32:
        raise ValueError('X client resource base must be an unsigned 32-bit integer')
    if display_name is not None and not isinstance(display_name, str):
        raise ValueError('display_name must be a string or None')
    if sys.platform != 'linux':
        return {'status':'unknown', 'reason':'unsupported_platform',
                'worker_retired':None, 'elapsed_ms':0.0}
    deadline_ns = time.monotonic_ns() + int(timeout_s * 1_000_000_000)
    return supervise_xres_worker(
        _xres_disconnect_worker,
        (display_name, resource_base, deadline_ns, poll_interval_s),
        timeout_s=timeout_s, terminate_grace_s=terminate_grace_s)


def client_is_connected(connection, resource_base):
    """Return exact client presence from one XRes QueryClients reply.

    A caller must separately bound the synchronous X request. `False` means
    only that this reply did not list the client; it does not itself authorize
    release or prove physical input neutrality.
    """
    if type(resource_base) is not int or not 0 <= resource_base < 2**32:
        raise ValueError('X client resource base must be an unsigned 32-bit integer')
    if not connection.has_extension('X-Resource'):
        raise RuntimeError('X-Resource unavailable')
    version = connection.res_query_version()
    major, minor = getattr(version, 'server_major', None), getattr(version, 'server_minor', None)
    if (type(major) is not int or type(minor) is not int
            or major < 1 or minor < 0):
        raise RuntimeError('invalid X-Resource version')
    clients = getattr(connection.res_query_clients(), 'clients', None)
    if type(clients) not in (list, tuple):
        raise RuntimeError('invalid X-Resource client list')
    bases = set()
    for client in clients:
        base = getattr(client, 'resource_base', None)
        mask = getattr(client, 'resource_mask', None)
        if (type(base) is not int or not 0 <= base < 2**32
                or type(mask) is not int or not 0 <= mask < 2**32
                or base in bases):
            raise RuntimeError('invalid or ambiguous X-Resource client list')
        bases.add(base)
    return resource_base in bases


def wait_for_client_disconnect(connection, resource_base, *, timeout_s,
                               poll_interval_s=0.02, clock=None, sleep=None):
    """Poll for exact client disappearance within a cooperative time budget.

    X protocol calls and sleep scheduling may exceed this budget. Callers that
    need a hard response bound must supervise this helper in a separate process.
    """
    _validate_duration('timeout_s', timeout_s, allow_zero=True)
    _validate_duration('poll_interval_s', poll_interval_s)
    if clock is None:
        clock = time.monotonic
    if sleep is None:
        sleep = time.sleep
    deadline = clock() + timeout_s
    first_query = True
    while first_query or clock() < deadline:
        first_query = False
        if not client_is_connected(connection, resource_base):
            return True
        remaining = deadline - clock()
        if remaining <= 0:
            return False
        sleep(min(poll_interval_s, remaining))
    return False
