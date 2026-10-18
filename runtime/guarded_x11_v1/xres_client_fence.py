"""XRes client-presence query; not a release receipt."""
import math
import time


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
    for name, value, allow_zero in (
            ('timeout_s', timeout_s, True),
            ('poll_interval_s', poll_interval_s, False)):
        if (type(value) not in (int, float) or not math.isfinite(value)
                or value < 0 or (not allow_zero and value == 0)):
            raise ValueError(name + ' must be a finite positive duration')
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
