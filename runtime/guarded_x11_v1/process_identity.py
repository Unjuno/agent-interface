"""Opt-in XRes/Linux process-incarnation evidence, not window incarnation."""
import hashlib
import json
from pathlib import Path


def process_generation_from_identity(xid, pid, start_ticks):
    """Return the stable local XID/PID/start-tick identity digest."""
    if (type(xid) is not int or not 1 < xid < 2**32
            or type(pid) is not int or pid <= 0
            or type(start_ticks) is not int or start_ticks <= 0):
        raise ValueError('invalid X11 process identity fields')
    payload = {'scheme':'xres-linux-process-v1','xid':xid,
               'pid':pid,'start_ticks':start_ticks}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,
        separators=(',',':')).encode('ascii')).hexdigest()


def process_incarnation_from_identity(pid, start_ticks):
    """Return the local process incarnation digest shared by its X resources."""
    if type(pid) is not int or pid <= 0 or type(start_ticks) is not int or start_ticks <= 0:
        raise ValueError('invalid X11 process incarnation fields')
    payload = {'scheme':'xres-linux-process-incarnation-v1',
               'pid':pid,'start_ticks':start_ticks}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,
        separators=(',',':')).encode('ascii')).hexdigest()


def _read_linux_x11_process_incarnation(connection, xid):
    """Read a trusted XRes PID and Linux process start tick pair."""
    if type(xid) is not int or not 1 < xid < 2**32:
        raise RuntimeError('invalid target resource')
    if not connection.has_extension('X-Resource'):
        raise RuntimeError('X-Resource unavailable')
    version = getattr(connection, '_agent_interface_xres_version', None)
    if version is None:
        reply = connection.res_query_version()
        version = (reply.server_major, reply.server_minor)
        if any(type(value) is not int or value < 0 for value in version):
            raise RuntimeError('invalid X-Resource version')
        connection._agent_interface_xres_version = version
    if (type(version) is not tuple or len(version) != 2
            or any(type(value) is not int or value < 0 for value in version)
            or version < (1, 2)):
        raise RuntimeError('X-Resource 1.2 required')
    reply = connection.res_query_client_ids([{'client': xid, 'mask': 2}])
    try:
        if len(reply.ids) != 1:
            raise RuntimeError('ambiguous local client PID')
        item = reply.ids[0]
        if (type(item.spec.client) is not int or not 0 < item.spec.client < 2**32
                or type(item.spec.mask) is not int or item.spec.mask != 2
                or len(item.value) != 1):
            raise RuntimeError('invalid local client PID response')
        pid = item.value[0]
    except (AttributeError, TypeError) as error:
        raise RuntimeError('invalid local client PID response') from error
    if type(pid) is not int or pid <= 0:
        raise RuntimeError('invalid local client PID')
    stat = Path('/proc', str(pid), 'stat').read_text(encoding='ascii')
    opening, closing = stat.find('('), stat.rfind(')')
    if opening < 1 or closing <= opening or stat[:opening].strip() != str(pid):
        raise RuntimeError('process stat identity mismatch')
    fields = stat[closing + 1:].split()
    if (len(fields) <= 19 or fields[0] in ('Z', 'X', 'x')
            or not fields[19].isascii() or not fields[19].isdigit()):
        raise RuntimeError('process start identity unavailable')
    return pid, int(fields[19])


def read_linux_x11_process_identity(connection, xid):
    """Hash XID + server-reported PID + /proc start ticks.

    Requires a trusted local X server whose PID namespace matches this /proc.
    No window-property fallback. Calls are synchronous, without an I/O bound.
    Same-process resource/client reuse and changes after this read are not
    excluded by this evidence.
    """
    details = read_linux_x11_process_identity_details(connection,xid)
    return details['process_generation']


def read_linux_x11_process_incarnation(connection, xid):
    """Hash the XRes PID and /proc start tick without the window XID.

    This allows comparison of two windows owned by one process. It remains a
    local-server/PID-namespace correlation cue and is not authenticated window
    role, transient-parent identity, or a race-free process lifetime fence.
    """
    details = read_linux_x11_process_identity_details(connection,xid)
    return details['process_incarnation']


def read_linux_x11_process_identity_details(connection,xid):
    """Read PID/start ticks and both digests from one XRes query boundary."""
    pid,start_ticks = _read_linux_x11_process_incarnation(connection,xid)
    return {'xid':xid,'pid':pid,'start_ticks':start_ticks,
        'process_generation':process_generation_from_identity(xid,pid,start_ticks),
        'process_incarnation':process_incarnation_from_identity(pid,start_ticks)}
